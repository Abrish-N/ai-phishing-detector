import re
import pickle
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)

# -----------------------------
# Load Dataset
# -----------------------------
expected_columns = [
    "id",
    "subject",
    "sender",
    "body",
    "contains_link",
    "urgent_word",
    "suspicious_sender",
    "label",
]
df = pd.read_csv("emails.csv", dtype=str, keep_default_na=False)
if list(df.columns) != expected_columns:
    raise ValueError(
        f"Expected emails.csv columns {expected_columns}, got {list(df.columns)}"
    )

labels = set(df["label"].str.strip())
if not labels.issubset({"0", "1"}):
    raise ValueError(f"Expected binary labels 0/1, got {sorted(labels)}")

# Combine subject + body
df["text"] = (
    df["subject"]
    + " "
    + df["body"]
)
df["label"] = df["label"].astype(int)

# -----------------------------
# Text Cleaning
# -----------------------------
def clean_text(text):
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+", " ", text)

    # Remove email addresses
    text = re.sub(r"\S+@\S+", " ", text)

    # Remove numbers
    text = re.sub(r"\d+", " ", text)

    # Remove punctuation
    text = re.sub(r"[^a-z\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


df["text"] = df["text"].apply(clean_text)

X = df["text"]
y = df["label"]

# -----------------------------
# Train/Test Split
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# -----------------------------
# TF-IDF Vectorizer
# -----------------------------
vectorizer = TfidfVectorizer(
    stop_words="english",
    lowercase=True,
    ngram_range=(1, 3),
    max_features=30000,
    min_df=2,
    max_df=0.95,
    sublinear_tf=True,
)

X_train_vec = vectorizer.fit_transform(X_train)
X_test_vec = vectorizer.transform(X_test)

# -----------------------------
# Logistic Regression
# -----------------------------
model = LogisticRegression(
    max_iter=3000,
    class_weight="balanced",
    solver="liblinear",
    random_state=42,
)

model.fit(X_train_vec, y_train)

# -----------------------------
# Evaluation
# -----------------------------
predictions = model.predict(X_test_vec)

accuracy = accuracy_score(y_test, predictions)

print("=" * 50)
print(f"Accuracy : {accuracy * 100:.2f}%")
print("=" * 50)

print("\nClassification Report\n")
print(classification_report(y_test, predictions))

print("\nConfusion Matrix\n")
print(confusion_matrix(y_test, predictions))

# -----------------------------
# Save
# -----------------------------
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("\nModel saved successfully.")