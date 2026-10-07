import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split


# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[4]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "emergency"
    / "Suicide_Detection.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "emergency"
    / "processed"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# --------------------------------------------------
# Load dataset
# --------------------------------------------------

print("Loading dataset...")

df = pd.read_csv(INPUT_FILE)

print(f"Original dataset size: {len(df)}")


# --------------------------------------------------
# Keep only required columns
# --------------------------------------------------

df = df[["text", "class"]].copy()


# --------------------------------------------------
# Basic cleaning
# --------------------------------------------------

df["text"] = df["text"].astype(str).str.strip()

df = df[df["text"].str.len() > 0]

df = df.drop_duplicates(subset=["text"])

print(f"Dataset size after cleaning: {len(df)}")


# --------------------------------------------------
# Convert labels
# --------------------------------------------------

df["label"] = df["class"].map({
    "non-suicide": 0,
    "suicide": 1,
})


# Remove anything that failed to map
df = df.dropna(subset=["label"])

df["label"] = df["label"].astype(int)


# --------------------------------------------------
# Train / temporary split
# 70% train
# 30% temporary
# --------------------------------------------------

train_df, temp_df = train_test_split(
    df,
    test_size=0.30,
    random_state=42,
    stratify=df["label"],
)


# --------------------------------------------------
# Validation / test split
# 15% validation
# 15% test
# --------------------------------------------------

validation_df, test_df = train_test_split(
    temp_df,
    test_size=0.50,
    random_state=42,
    stratify=temp_df["label"],
)


# --------------------------------------------------
# Save
# --------------------------------------------------

train_df.to_csv(
    OUTPUT_DIR / "train.csv",
    index=False,
)

validation_df.to_csv(
    OUTPUT_DIR / "validation.csv",
    index=False,
)

test_df.to_csv(
    OUTPUT_DIR / "test.csv",
    index=False,
)


# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\nDataset preparation complete!")

print(f"Training samples:   {len(train_df)}")
print(f"Validation samples: {len(validation_df)}")
print(f"Test samples:       {len(test_df)}")

print("\nTraining distribution:")
print(train_df["class"].value_counts())

print("\nValidation distribution:")
print(validation_df["class"].value_counts())

print("\nTest distribution:")
print(test_df["class"].value_counts())

print(f"\nSaved files to:")
print(OUTPUT_DIR)