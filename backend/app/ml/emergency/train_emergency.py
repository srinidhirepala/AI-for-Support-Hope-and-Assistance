import os
from pathlib import Path

import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    TrainingArguments,
    Trainer,
)

# ============================================================
# ASHA - Emergency Detection Model Training
# ============================================================

# Project root
BASE_DIR = Path(__file__).resolve().parents[4]

# Dataset paths
TRAIN_FILE = (
    BASE_DIR
    / "data"
    / "emergency"
    / "processed"
    / "train.csv"
)

VALIDATION_FILE = (
    BASE_DIR
    / "data"
    / "emergency"
    / "processed"
    / "validation.csv"
)

# Output directory
MODEL_DIR = (
    BASE_DIR
    / "models"
    / "emergency"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# Model
MODEL_NAME = "distilroberta-base"

print("=" * 60)
print("ASHA Emergency Detection Model Training")
print("=" * 60)

# ------------------------------------------------------------
# 1. Load datasets
# ------------------------------------------------------------

print("\nLoading training dataset...")

train_df = pd.read_csv(TRAIN_FILE)

print(f"Training samples: {len(train_df)}")

print("\nLoading validation dataset...")

validation_df = pd.read_csv(VALIDATION_FILE)

print(f"Validation samples: {len(validation_df)}")

# Keep only required columns
train_df = train_df[["text", "label"]]
validation_df = validation_df[["text", "label"]]

# Make sure labels are integers
train_df["label"] = train_df["label"].astype(int)
validation_df["label"] = validation_df["label"].astype(int)

# ------------------------------------------------------------
# 2. Convert pandas → Hugging Face Dataset
# ------------------------------------------------------------

train_dataset = Dataset.from_pandas(
    train_df,
    preserve_index=False,
)

validation_dataset = Dataset.from_pandas(
    validation_df,
    preserve_index=False,
)

# ------------------------------------------------------------
# 3. Load tokenizer
# ------------------------------------------------------------

print("\nLoading tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

# ------------------------------------------------------------
# 4. Tokenization
# ------------------------------------------------------------

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        max_length=256,
    )


print("\nTokenizing training dataset...")

train_dataset = train_dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"],
)

print("Tokenizing validation dataset...")

validation_dataset = validation_dataset.map(
    tokenize_function,
    batched=True,
    remove_columns=["text"],
)

# ------------------------------------------------------------
# 5. Load classification model
# ------------------------------------------------------------

print("\nLoading DistilRoBERTa model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=2,
    id2label={
        0: "NON_SUICIDE",
        1: "POTENTIAL_CRISIS",
    },
    label2id={
        "NON_SUICIDE": 0,
        "POTENTIAL_CRISIS": 1,
    },
)

# ------------------------------------------------------------
# 6. Data collator
# ------------------------------------------------------------

data_collator = DataCollatorWithPadding(
    tokenizer=tokenizer
)

# ------------------------------------------------------------
# 7. Training configuration
# ------------------------------------------------------------

training_args = TrainingArguments(
    output_dir=str(MODEL_DIR / "checkpoints"),

    eval_strategy="epoch",
    save_strategy="epoch",

    learning_rate=2e-5,

    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,

    num_train_epochs=1,

    weight_decay=0.01,

    logging_steps=100,

    load_best_model_at_end=True,

    metric_for_best_model="eval_loss",

    report_to="none",

    save_total_limit=2,
)

# ------------------------------------------------------------
# 8. Trainer
# ------------------------------------------------------------

trainer = Trainer(
    model=model,
    args=training_args,

    train_dataset=train_dataset,
    eval_dataset=validation_dataset,

    processing_class=tokenizer,

    data_collator=data_collator,
)

# ------------------------------------------------------------
# 9. Train
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("Starting training...")
print("=" * 60)

trainer.train()

# ------------------------------------------------------------
# 10. Save final model
# ------------------------------------------------------------

FINAL_MODEL_DIR = MODEL_DIR / "distilroberta_emergency"

print("\nSaving trained model...")

trainer.save_model(
    FINAL_MODEL_DIR
)

tokenizer.save_pretrained(
    FINAL_MODEL_DIR
)

print("\n" + "=" * 60)
print("Training completed successfully!")
print("=" * 60)

print(f"\nModel saved to:")
print(FINAL_MODEL_DIR)