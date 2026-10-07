from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    pipeline,
)


# ============================================================
# ASHA - Emergency Detection Model Evaluation
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[4]

TEST_FILE = (
    BASE_DIR
    / "data"
    / "emergency"
    / "processed"
    / "test.csv"
)

MODEL_DIR = (
    BASE_DIR
    / "models"
    / "emergency"
    / "distilroberta_emergency"
)


print("=" * 60)
print("ASHA Emergency Detection Model Evaluation")
print("=" * 60)


# ------------------------------------------------------------
# 1. Load test dataset
# ------------------------------------------------------------

print("\nLoading test dataset...")

df = pd.read_csv(TEST_FILE)

df = df[["text", "label"]].copy()

df["label"] = df["label"].astype(int)

print(f"Test samples: {len(df)}")


# ------------------------------------------------------------
# 2. Load trained model
# ------------------------------------------------------------

print("\nLoading trained model...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_DIR
)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_DIR
)


# ------------------------------------------------------------
# 3. Create classifier
# ------------------------------------------------------------

classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    device=-1,
)


# ------------------------------------------------------------
# 4. Generate predictions
# ------------------------------------------------------------

print("\nGenerating predictions...")

texts = df["text"].tolist()

predictions = []

batch_size = 32

for start in range(0, len(texts), batch_size):

    batch = texts[start:start + batch_size]

    results = classifier(
        batch,
        truncation=True,
        max_length=256,
    )

    for result in results:

        label = result["label"]

        if label == "POTENTIAL_CRISIS":
            predictions.append(1)
        else:
            predictions.append(0)

    processed = min(
        start + batch_size,
        len(texts)
    )

    if processed % 1000 == 0 or processed == len(texts):
        print(
            f"Processed {processed}/{len(texts)}"
        )


# ------------------------------------------------------------
# 5. Calculate metrics
# ------------------------------------------------------------

accuracy = accuracy_score(
    df["label"],
    predictions,
)

print("\n" + "=" * 60)
print("Evaluation Results")
print("=" * 60)

print(f"\nAccuracy: {accuracy:.4f}")

print("\nClassification Report:")

print(
    classification_report(
        df["label"],
        predictions,
        target_names=[
            "NON_SUICIDE",
            "POTENTIAL_CRISIS",
        ],
        digits=4,
    )
)


# ------------------------------------------------------------
# 6. Confusion matrix
# ------------------------------------------------------------

matrix = confusion_matrix(
    df["label"],
    predictions,
)

print("\nConfusion Matrix:")

print(matrix)

print("\nMatrix format:")
print("[[True Negative, False Positive],")
print(" [False Negative, True Positive]]")


print("\n" + "=" * 60)
print("Evaluation completed!")
print("=" * 60)