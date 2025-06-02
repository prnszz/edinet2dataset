from datasets import load_dataset
from collections import Counter

ds = load_dataset(
    "json",
    data_files={
        "train": "dataset/industry_prediction/train.json",
    },
)
print(Counter(ds["train"]["industry"]))
print(f"sum: {len(ds['train'])}")

# ds.push_to_hub("SakanaAI/EDINET-Bench", "industry_prediction", private=True)
