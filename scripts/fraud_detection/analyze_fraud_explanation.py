import os
import json
from tqdm import tqdm

path = "v5/analysis/result.jsonl"

results = []
with open(path, "r") as file:
    for line in file:
        results.append(json.loads(line))


# copy the files to the analyze_fraud_explanation directory
output_dir = "analyze_fraud_explanation"
os.makedirs(output_dir, exist_ok=True)

for result in tqdm(results, desc="Processing results"):
    is_fraud = result["is_accounting_fraud"]
    if not is_fraud:
        continue
    amended_pdf_path = result["amended_pdf_path"]
    doc_id = result["original_doc_id"]
    save_dir = os.path.join(output_dir, doc_id)
    os.makedirs(save_dir, exist_ok=True)
    amended_pdf_name = os.path.basename(amended_pdf_path)
    amended_pdf_save_path = os.path.join(save_dir, amended_pdf_name)
    os.system(f"cp {amended_pdf_path} {amended_pdf_save_path}")
    with open(os.path.join(save_dir, "result.json"), "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
