import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[4]

csv_path = (
    BASE_DIR
    / "data"
    / "emergency"
    / "Suicide_Detection.csv"
)

print("Loading dataset...")

df = pd.read_csv(csv_path)

print("\nDataset shape:")
print(df.shape)

print("\nColumns:")
print(df.columns.tolist())

print("\nClass distribution:")
print(df["class"].value_counts())

print("\nMissing values:")
print(df.isnull().sum())

print("\nSample records:")
print(df.head())