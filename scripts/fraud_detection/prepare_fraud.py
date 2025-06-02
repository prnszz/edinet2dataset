import os
import json
import logging
import re
import backoff
from argparse import ArgumentParser
from tqdm import tqdm
import anthropic
from concurrent.futures import ThreadPoolExecutor, as_completed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from edinet2dataset.downloader import Downloader
import glob
import polars as pl
from edinet2dataset.parser import Parser

# Suppress specific pdfminer warning about text extraction
logging.getLogger("pdfminer.pdfpage").setLevel(logging.ERROR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_original_report(
    doc_id: str, output_dir: str = "fraud_detection/fraud/annual"
) -> None:
    downloader = Downloader()
    downloader.download_document(doc_id, "pdf", output_dir)
    logger.info(f"Downloaded original PDF: {doc_id}")
    downloader.download_document(doc_id, "tsv", output_dir)
    logger.info(f"Downloaded original TSV: {doc_id}")


def extract_text_with_pdfminer(pdf_path: str, max_pages: int = 4) -> str:
    resource_manager = PDFResourceManager()
    fake_file_handle = StringIO()
    converter = TextConverter(
        resource_manager, fake_file_handle, laparams=LAParams(), codec="utf-8"
    )
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(pdf_path, "rb") as fh:
        for page_num, page in enumerate(PDFPage.get_pages(fh, check_extractable=False)):
            if page_num >= max_pages:
                break
            page_interpreter.process_page(page)

    text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()
    return text


def read_tsv_get_original_doc_id(tsv_path: str) -> str | None:
    parser = Parser()
    df = pl.read_csv(tsv_path, separator="\t", encoding="utf-16", infer_schema_length=0)
    df = parser.unique_element_list(df)
    df = parser.filter_by_element_id(
        df, "IdentificationOfDocumentSubjectToAmendmentDEI"
    )
    return df["値"].to_numpy()[0] if df.shape[0] == 1 else None


def create_amended_prompt(pdf_text: str) -> str:
    """Create prompt for Claude to analyze amended reports."""
    prompt = """
以下のテキストは訂正有価証券報告書の冒頭部分です。この訂正有価証券報告書が不適切会計、粉飾決算、会計不正に関連しているかどうかを判断してください。

特に「提出理由」の部分に着目し、以下のような言葉や表現がある場合は不正会計の可能性が高いと考えられます：
- 不適切会計
- 会計不正
- 不正行為
- 粉飾決算
- 会計処理の誤り
- 売上の過大計上
- 費用の過少計上
- 資産の過大評価
- 不適切な収益認識
- 監査法人からの指摘
- 社内調査
- 第三者委員会

訂正の理由が単純な記載ミスや軽微な修正ではなく、会計上の重大な問題を示している場合は「Yes」と回答し、詳細な説明を提供してください。
特に財務諸表（貸借対照表、損益計算書、キャッシュフロー計算書など）の数値に変更が生じた事例に注目してください。
会計不正とは関係ない場合や財務諸表に変更が生じていない場合は「No」と回答し、その理由を簡潔に説明してください。

以下のJSON形式で回答してください。このJSONは必ず有効なJSON形式である必要があります:

```json
{
  "is_accounting_fraud": bool # true or false
  "explanation": str # 理由を説明する
  "company_name": str # 会社名
}
```

回答は必ずこの形式に一致させてください。
JSONは必ず上記の形式の```json```タグで囲んで提供してください。

訂正有価証券報告書のテキスト:
"""
    return prompt + "\n" + pdf_text


def extract_json_between_markers(llm_output: str) -> dict | None:
    # Regular expression pattern to find JSON content between ```json and ```
    json_pattern = r"```json(.*?)```"
    matches = re.findall(json_pattern, llm_output, re.DOTALL)

    if not matches:
        # Fallback: Try to find any JSON-like content in the output
        json_pattern = r"\{.*?\}"
        matches = re.findall(json_pattern, llm_output, re.DOTALL)

    for json_string in matches:
        json_string = json_string.strip()
        try:
            parsed_json = json.loads(json_string)
            return parsed_json
        except json.JSONDecodeError:
            # Attempt to fix common JSON issues
            try:
                # Remove invalid control characters
                json_string_clean = re.sub(r"[\x00-\x1F\x7F]", "", json_string)
                parsed_json = json.loads(json_string_clean)
                return parsed_json
            except json.JSONDecodeError:
                continue  # Try next match

    return None  # No valid JSON found


@backoff.on_exception(
    backoff.expo, (anthropic.RateLimitError, anthropic.APITimeoutError), max_tries=3
)
def get_response_from_llm(
    user_text: str,
    client: anthropic.Anthropic,
    model: str,
    system_prompt: str,
    temperature: float = 0.1,
    max_tokens: int = 4096,
) -> tuple[str, list]:
    """Get response from Claude with retry handling."""
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_text,
                }
            ],
        }
    ]
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        messages=messages,
    )
    return response.content[0].text


def judge_amended_pdf(pdf_path: str) -> dict | None:
    """Analyze a single amended PDF file to determine if it's related to accounting fraud."""
    doc_id = os.path.basename(pdf_path).split(".")[0]
    tsv_path = pdf_path.replace(".pdf", ".tsv")
    if not os.path.exists(tsv_path):
        logger.info(f"{tsv_path} not found")
        return None

    original_doc_id = read_tsv_get_original_doc_id(tsv_path)
    if not original_doc_id:
        logger.info(f"{doc_id}'s corredponding report does not exist.")
        return None

    pdf_text = extract_text_with_pdfminer(pdf_path, max_pages=4)
    full_prompt = create_amended_prompt(pdf_text)
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = get_response_from_llm(
        user_text=full_prompt,
        client=client,
        model="claude-3-7-sonnet-20250219",
        system_prompt="You are an expert in detecting accounting fraud in financial documents.",
        temperature=0.0,
    )
    json_data = extract_json_between_markers(response)
    if not json_data:
        logger.error(f"Failed to extract JSON from response for {pdf_path}")
        return None
    is_accounting_fraud = json_data.get("is_accounting_fraud", False)
    explanation = json_data.get("explanation", "")
    company_name = json_data.get("company_name", "")

    return {
        "amended_doc_id": doc_id,
        "original_doc_id": original_doc_id,
        "company_name": company_name,
        "is_accounting_fraud": is_accounting_fraud,
        "explanation": explanation,
        "amended_pdf_path": pdf_path,
    }


def judge_amended_batch(
    args,
    amended_dir: str = "edinet_corpus/annual_amended",
    analysis_dir: str = "fraud_detection/analysis",
) -> list[dict]:
    """Analyze all amended reports in batch and save results."""
    amended_pdf_files = glob.glob(os.path.join(amended_dir, "*", "*.pdf"))
    amended_pdf_files.sort()

    if args.limit is not None:
        amended_pdf_files = amended_pdf_files[: args.limit]

    all_analyses = []

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(judge_amended_pdf, pdf_file)
            for pdf_file in amended_pdf_files
        ]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Processing amended PDFs",
            unit="file",
        ):
            pdf_file = amended_pdf_files[futures.index(future)]
            try:
                analysis = future.result()
                if analysis:
                    all_analyses.append(analysis)
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                continue

    with open(os.path.join(analysis_dir, "result.jsonl"), "w", encoding="utf-8") as f:
        for analysis in all_analyses:
            f.write(json.dumps(analysis, ensure_ascii=False) + "\n")

    fraud_cases = [case for case in all_analyses if case["is_accounting_fraud"]]
    return fraud_cases


def parse_args():
    parser = ArgumentParser(
        description="Analyze amended reports and prepare fraud dataset"
    )
    parser.add_argument(
        "--analysis_dir",
        type=str,
        default="fraud_detection/analysis",
        help="Directory containing analysis results",
    )
    parser.add_argument(
        "--amended_dir",
        type=str,
        default="edinet_corpus/annual_amended",
        help="Directory containing amended reports",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="fraud_detection/fraud/annual",
        help="Directory to save the output files",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=5,
        help="Maximum number of worker threads for parallel processing",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of documents to process (for debugging)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.analysis_dir, exist_ok=True)
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.amended_dir, exist_ok=True)

    # Step 1: Analyze amended reports
    fraud_cases = judge_amended_batch(args, args.amended_dir, args.analysis_dir)

    logger.info(f"Found {len(fraud_cases)} fraud cases.")

    # Step 2: Download original documents for fraud cases
    for case in tqdm(fraud_cases, desc="Preparing fraud dataset"):
        download_original_report(case["original_doc_id"], args.output_dir)


if __name__ == "__main__":
    main()
