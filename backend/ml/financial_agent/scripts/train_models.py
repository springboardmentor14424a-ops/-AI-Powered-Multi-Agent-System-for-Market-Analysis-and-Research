import pandas as pd
import numpy as np
from pathlib import Path
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix
)

# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

INPUT_FILE = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
    / "reliance_features.csv"
)

MODEL_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "models"
)

RESULTS_DIR = (
    PROJECT_ROOT
    / "backend"
    / "ml"
    / "financial_agent"
    / "data"
    / "processed"
)

MODEL_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

df = pd.read_csv(INPUT_FILE, parse_dates=["Date"])

df = df.sort_values("Date").reset_index(drop=True)

print("=" * 60)
print("FINANCIAL AGENT - MODEL TRAINING")
print("=" * 60)

print("\nDataset shape:", df.shape)

# --------------------------------------------------
# SELECT FEATURES
# --------------------------------------------------

# Columns that should not be used for model training
columns_to_drop = [
    "Date",
    "Symbol",
    "Series",
    "Target"
]

X = df.drop(columns=columns_to_drop)

y = df["Target"]

print("\nFeatures used for training:")
print(X.columns.tolist())

print("\nTotal features:", X.shape[1])

# --------------------------------------------------
# CHRONOLOGICAL TRAIN-TEST SPLIT
# --------------------------------------------------

# First 80% = training data
# Last 20% = testing data

split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print("\nTraining data size:", X_train.shape)
print("Testing data size:", X_test.shape)

print("\nTraining period:")
print(df["Date"].iloc[0], "to", df["Date"].iloc[split_index - 1])

print("\nTesting period:")
print(df["Date"].iloc[split_index], "to", df["Date"].iloc[-1])

# --------------------------------------------------
# DEFINE ML MODELS
# --------------------------------------------------

models = {

    "Logistic Regression": Pipeline([
        ("scaler", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000))
    ]),

    "Random Forest": RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    ),

    "Gradient Boosting": GradientBoostingClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=3,
        random_state=42
    ),

    "SVM": Pipeline([
        ("scaler", StandardScaler()),
        ("model", SVC(kernel="rbf"))
    ])

}

# --------------------------------------------------
# TRAIN AND EVALUATE MODELS
# --------------------------------------------------

results = []

best_model = None
best_model_name = None
best_accuracy = -1

print("\n" + "=" * 60)
print("TRAINING MODELS")
print("=" * 60)

for model_name, model in models.items():

    print(f"\nTraining {model_name}...")

    # Train the model
    model.fit(X_train, y_train)

    # Make predictions
    predictions = model.predict(X_test)

    # Calculate performance metrics
    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    balanced_acc = balanced_accuracy_score(
        y_test,
        predictions
    )

    # Store results
    results.append({
        "Model": model_name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "Balanced_Accuracy": balanced_acc
    })

    print(f"Accuracy          : {accuracy:.4f}")
    print(f"Precision        : {precision:.4f}")
    print(f"Recall           : {recall:.4f}")
    print(f"F1 Score         : {f1:.4f}")
    print(f"Balanced Accuracy: {balanced_acc:.4f}")

    # Select best model based on accuracy
    if accuracy > best_accuracy:

        best_accuracy = accuracy
        best_model = model
        best_model_name = model_name

# --------------------------------------------------
# MODEL COMPARISON
# --------------------------------------------------

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="Accuracy",
    ascending=False
).reset_index(drop=True)

print("\n" + "=" * 60)
print("MODEL COMPARISON")
print("=" * 60)

print(results_df.to_string(index=False))

# Save comparison results
results_file = RESULTS_DIR / "model_comparison.csv"

results_df.to_csv(results_file, index=False)

# --------------------------------------------------
# SAVE BEST MODEL
# --------------------------------------------------

best_model_file = MODEL_DIR / "best_financial_model.pkl"

model_bundle = {
    "model": best_model,
    "model_name": best_model_name,
    "features": X.columns.tolist(),
    "accuracy": best_accuracy
}

joblib.dump(model_bundle, best_model_file)

# --------------------------------------------------
# BEST MODEL RESULTS
# --------------------------------------------------

print("\n" + "=" * 60)
print("BEST MODEL")
print("=" * 60)

print("Best model:", best_model_name)
print(f"Best accuracy: {best_accuracy:.4f}")

# Generate predictions using best model
best_predictions = best_model.predict(X_test)

print("\nClassification Report:")
print(classification_report(
    y_test,
    best_predictions,
    zero_division=0
))

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, best_predictions))

# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n" + "=" * 60)
print("TRAINING COMPLETED SUCCESSFULLY!")
print("=" * 60)

print("\nBest model saved to:")
print(best_model_file)

print("\nComparison results saved to:")
print(results_file)
