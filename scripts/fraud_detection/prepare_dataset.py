import os
import glob
import json
from argparse import ArgumentParser, Namespace

import datasets
import pandas as pd
from loguru import logger

from edinet2dataset.parser import parse_tsv
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm
from sklearn.model_selection import train_test_split


def find_tsv_files(report_dir: str) -> list[str]:
    target_dir = os.path.join(report_dir, "annual")
    return glob.glob(os.path.join(target_dir, "*.tsv"))


def load_fraud_explanation(analysis_path: str) -> dict[str, dict]:
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis_data = [json.loads(line) for line in f]
    explanation_table = {}
    for analysis in analysis_data:
        if not analysis["is_accounting_fraud"]:
            continue
        doc_id = analysis["amended_doc_id"]
        explanation = analysis["explanation"]
        amended_doc_id = analysis["amended_doc_id"]
        explanation_table[doc_id] = {
            "amended_doc_id": amended_doc_id,
            "explanation": explanation,
        }
    return explanation_table


def build_data_entry(tsv_path: str, label: int, explanation_table: dict) -> dict:
    financial_data = parse_tsv(tsv_path)
    if not financial_data:
        logger.warning(f"Failed to parse {tsv_path}")
        return {}
    logger.info(f"Processed {tsv_path}")

    doc_id = os.path.basename(tsv_path).replace(".tsv", "")
    if label == 1 and doc_id in explanation_table:
        explanation = explanation_table[doc_id]["explanation"]
        amended_doc_id = explanation_table[doc_id]["amended_doc_id"]
    else:
        explanation = ""
        amended_doc_id = ""
    edinet_code = financial_data.meta.get("EDINETコード")

    if not edinet_code:
        logger.warning(f"EDINETコード not found in {tsv_path}")
        return {}

    return {
        "meta": json.dumps(financial_data.meta, ensure_ascii=False),
        "summary": json.dumps(financial_data.summary, ensure_ascii=False),
        "bs": json.dumps(financial_data.bs, ensure_ascii=False),
        "pl": json.dumps(financial_data.pl, ensure_ascii=False),
        "cf": json.dumps(financial_data.cf, ensure_ascii=False),
        "text": json.dumps(financial_data.text, ensure_ascii=False),
        "label": int(label),
        "explanation": explanation,
        "edinet_code": edinet_code,
        "amended_doc_id": amended_doc_id,
        "doc_id": doc_id,
        "file_path": tsv_path,
    }


def gather_all_tsv_files(base_dir: str) -> list[tuple[str, int]]:
    all_files = []
    for report_type, label in [("fraud", 1), ("nonfraud", 0)]:
        report_dir = os.path.join(base_dir, report_type)
        tsv_files = find_tsv_files(report_dir)
        all_files.extend([(tsv_file, label) for tsv_file in tsv_files])
    return all_files


def process_all_reports_parallel(base_dir: str, explanation_table: dict) -> list[dict]:
    entries = []
    tsv_files_with_labels = gather_all_tsv_files(base_dir)

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(build_data_entry, tsv_file, label, explanation_table): (
                tsv_file,
                label,
            )
            for tsv_file, label in tsv_files_with_labels
        }

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing all reports"
        ):
            tsv_file, _ = futures[future]
            try:
                entry = future.result()
                if entry:
                    entries.append(entry)
            except Exception as e:
                logger.error(f"Error processing {tsv_file}: {e}")

    return entries


def create_dataset(base_dir: str, explanation_table: dict) -> datasets.Dataset:
    all_data = process_all_reports_parallel(base_dir, explanation_table)
    return datasets.Dataset.from_dict(
        {k: [d[k] for d in all_data] for k in all_data[0]}
    )


def split_dataset_by_edinet_code(
    dataset: datasets.Dataset, test_size: float = 0.2, seed: int = 42
) -> dict[str, datasets.Dataset]:
    df = pd.DataFrame(dataset)

    unique_codes = df["edinet_code"].unique()
    train_codes, test_codes = train_test_split(
        unique_codes, test_size=test_size, random_state=seed
    )

    train_df = df[df["edinet_code"].isin(train_codes)].reset_index(drop=True)
    test_df = df[df["edinet_code"].isin(test_codes)].reset_index(drop=True)

    return {
        "train": datasets.Dataset.from_pandas(train_df),
        "test": datasets.Dataset.from_pandas(test_df),
    }


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Prepare the dataset for training")
    parser.add_argument(
        "--base_dir", type=str, default="fraud_detection", help="Path for raw data"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="dataset/fraud_detection",
        help="Path to save the dataset",
    )
    parser.add_argument(
        "--deduplication",
        type=bool,
        default=True,
        help="Remove duplicated entries based on EDINET code",
    )
    parser.add_argument(
        "--analysis_path",
        type=str,
        default="fraud_detection/analysis/result.jsonl",
        help="Path to the analysis JSON file",
    )
    return parser.parse_args()


def save_dataset(dataset: datasets.Dataset, output_path: str):
    dataset.to_json(output_path, force_ascii=False)
    logger.info(f"Dataset saved to {output_path}")


def main():
    args = parse_args()
    explanation_table = load_fraud_explanation(args.analysis_path)
    os.makedirs(args.output_dir, exist_ok=True)

    dataset = create_dataset(args.base_dir, explanation_table)
    dataset = dataset.sort("edinet_code")

    dataset_dict = split_dataset_by_edinet_code(dataset)

    for split_name, ds in dataset_dict.items():
        output_path = os.path.join(args.output_dir, f"{split_name}.json")
        save_dataset(ds, output_path)

    for split_name in ["train", "test"]:
        loaded = datasets.load_dataset(
            "json",
            data_files={
                split_name: os.path.join(args.output_dir, f"{split_name}.json")
            },
        )
        print(f"{split_name}: {len(loaded[split_name])} samples")
        print(loaded[split_name][0])


if __name__ == "__main__":
    main()
