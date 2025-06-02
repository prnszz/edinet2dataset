from datasets import load_dataset
from collections import Counter

ds = load_dataset(
    "json",
    data_files={
        "train": "dataset/fraud_detection/train.json",
        "test": "dataset/fraud_detection/test.json",
    },
)
print(ds)

train_labels = ds["train"]["label"]
print("train", sorted(Counter(train_labels).items()))
test_labels = ds["test"]["label"]
print("test", sorted(Counter(test_labels).items()))

ds.push_to_hub("SakanaAI/EDINET-Bench", "fraud_detection", private=True)
