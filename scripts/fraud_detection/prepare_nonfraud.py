import os
import random
import glob
import shutil
import logging
from typing import List, Set
from tqdm import tqdm
from edinet2dataset.parser import Parser
import polars as pl
from argparse import ArgumentParser

logging.basicConfig(level=logging.INFO)


def get_fraud_doc_ids(fraud_dir: str) -> List[str]:
    return [
        os.path.splitext(os.path.basename(file))[0]
        for file in os.listdir(fraud_dir)
        if file.endswith(".tsv")
    ]


def is_fraud(doc_id: str, fraud_doc_ids: Set[str]) -> bool:
    return doc_id in fraud_doc_ids


def copy_files(pdf_file: str, tsv_file: str, dest_dir: str) -> None:
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(pdf_file, dest_dir)
    shutil.copy(tsv_file, dest_dir)
    logging.info(f"Copied: {pdf_file} and {tsv_file} to {dest_dir}")


def sample_and_copy_nonfraud_example(edinet_dir: str, dest_dir: str) -> None:
    pdf_files = glob.glob(os.path.join(edinet_dir, "*.pdf"))
    if not pdf_files:
        return

    doc_ids = [os.path.splitext(os.path.basename(file))[0] for file in pdf_files]
    doc_id = random.choice(doc_ids)
    pdf_file = os.path.join(edinet_dir, f"{doc_id}.pdf")
    tsv_file = os.path.join(edinet_dir, f"{doc_id}.tsv")

    if os.path.exists(pdf_file) and os.path.exists(tsv_file):
        copy_files(pdf_file, tsv_file, dest_dir)


def get_nonfraud_doc_dirs(
    annual_dir: str, fraud_edinet_codes: Set[str], sample_size: int = 10
) -> List[str]:
    dirs = glob.glob(os.path.join(annual_dir, "*"))
    nonfraud_dirs = []

    for edinet_dir in random.sample(dirs, min(len(dirs), sample_size * 2)):
        edinet_code = os.path.basename(edinet_dir)
        if edinet_code not in fraud_edinet_codes:
            nonfraud_dirs.append(edinet_dir)
        if len(nonfraud_dirs) >= sample_size:
            break

    return nonfraud_dirs


def get_fraud_edinet_codes(fraud_dir: str) -> Set[str]:
    fraud_tsv_files = glob.glob(os.path.join(fraud_dir, "*.tsv"))
    edinet_codes = set()
    parser = Parser()

    for fraud_file in fraud_tsv_files:
        try:
            df = pl.read_csv(
                fraud_file, separator="\t", encoding="utf-16", infer_schema_length=0
            )
            edinet_code = (
                parser.filter_by_element_id(df, "EDINETCodeDEI")
                .select("値")
                .to_numpy()[0][0]
            )
            logging.info(f"Extracted EDINET code: {edinet_code}")
            edinet_codes.add(edinet_code)
        except Exception as e:
            logging.warning(f"Failed to read {fraud_file}: {e}")

    return edinet_codes


def parse_args():
    arg_parser = ArgumentParser(description="Prepare non-fraud examples")
    arg_parser.add_argument(
        "--annual_dir",
        type=str,
        default="edinet_corpus/annual",
        help="Directory containing annual documents",
    )
    arg_parser.add_argument(
        "--fraud_dir",
        type=str,
        default="fraud_detection/fraud/annual",
        help="Directory containing fraud documents",
    )
    arg_parser.add_argument(
        "--dest_dir",
        type=str,
        default="fraud_detection/nonfraud/annual",
        help="Destination directory for non-fraud examples",
    )
    arg_parser.add_argument(
        "--sample_size",
        type=int,
        default=700,
        help="Number of non-fraud examples to sample",
    )
    return arg_parser.parse_args()


def main():
    args = parse_args()
    random.seed(42)

    fraud_edinet_codes = get_fraud_edinet_codes(args.fraud_dir)
    logging.info(f"Found {len(fraud_edinet_codes)} fraud EDINET codes.")

    filtered_dirs = get_nonfraud_doc_dirs(
        args.annual_dir, fraud_edinet_codes, sample_size=args.sample_size
    )
    logging.info(f"Found {len(filtered_dirs)} directories to process.")

    for edinet_dir in tqdm(filtered_dirs, desc="Processing non-fraud examples"):
        sample_and_copy_nonfraud_example(edinet_dir, args.dest_dir)


if __name__ == "__main__":
    main()
