"""
TCS Stock Price Trend Prediction - Machine Learning Pipeline
Dataset: Stock_TCS.xlsx (NSE Daily Trading Records, 2010 - 2020)
Split: 80% Train, 20% Test (Random State: 42)
Target: 5-Day Forward Trend Direction (1 = Up, 0 = Down)
Models Benchmarked: Random Forest, Gradient Boosting, XGBoost, SVM, Extra Trees, Logistic Regression, KNN
"""

import os
import zipfile
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report
)
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

def load_tcs_data(zip_path=None):
    """Loads Stock_TCS.xlsx from zip or directly from file."""
    if zip_path and os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path) as z:
            with z.open('Stock_TCS.xlsx') as f:
                return pd.read_excel(f)
    elif os.path.exists('Stock_TCS.xlsx'):
        return pd.read_excel('Stock_TCS.xlsx')
    else:
        # Default user path
        default_zip = os.path.expanduser(r'~\Downloads\ai_powered_stock_research_dataset.zip')
        if os.path.exists(default_zip):
            with zipfile.ZipFile(default_zip) as z:
                with z.open('Stock_TCS.xlsx') as f:
                    return pd.read_excel(f)
        raise FileNotFoundError("Could not locate Stock_TCS.xlsx or ai_powered_stock_research_dataset.zip")

def preprocess_and_engineer_features(df):
    """Cleans data and engineers technical & momentum features."""
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)

    close = df['Close']
    df['Return_1d'] = close.pct_change()
    df['Return_5d'] = close.pct_change(5)
    df['SMA_5'] = close.rolling(5).mean()
    df['SMA_20'] = close.rolling(20).mean()

    # Moving Average Convergence Divergence (MACD)
    df['EMA_12'] = close.ewm(span=12, adjust=False).mean()
    df['EMA_26'] = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']

    # Bollinger Bands
    std20 = close.rolling(20).std()
    df['BB_Upper'] = df['SMA_20'] + (std20 * 2)
    df['BB_Lower'] = df['SMA_20'] - (std20 * 2)
    df['BB_Pct'] = (close - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'] + 1e-6)

    # Volatility & Deliverable Volume Ratio
    df['Volatility_20'] = df['Return_1d'].rolling(20).std()
    df['Vol_Ratio'] = df['Volume'] / (df['Volume'].rolling(20).mean() + 1e-6)
    df['Deliverable_Pct'] = df['%Deliverble']

    # Target Variable: 5-Day Forward Price Direction (1 = Higher, 0 = Lower/Flat)
    df['Target'] = (df['Close'].shift(-5) > df['Close']).astype(int)

    feature_cols = [
        'Return_1d', 'Return_5d', 'MACD', 'MACD_Hist', 'BB_Pct', 
        'Volatility_20', 'Vol_Ratio', 'Deliverable_Pct'
    ]

    # Drop rolling NaN rows and the last 5 forecast rows
    df_clean = df.dropna().iloc[:-5].reset_index(drop=True)
    return df_clean, feature_cols

def main():
    print("=" * 65)
    print("TCS STOCK PRICE TREND PREDICTION - 80:20 ML BENCHMARK")
    print("=" * 65)

    df_raw = load_tcs_data()
    print(f"1. Dataset Loaded: {df_raw.shape[0]} trading rows from {df_raw['Date'].min().strftime('%Y-%m-%d')} to {df_raw['Date'].max().strftime('%Y-%m-%d')}")

    df_clean, feature_cols = preprocess_and_engineer_features(df_raw)
    X = df_clean[feature_cols]
    y = df_clean['Target']
    print(f"2. Features Engineered: {len(feature_cols)} features ({', '.join(feature_cols)})")
    print(f"   Clean Samples: {len(X)} | Target Balance: {y.value_counts()[1]} Up ({y.mean()*100:.1f}%), {y.value_counts()[0]} Down ({(1-y.mean())*100:.1f}%)")

    # 80:20 Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"3. 80:20 Split Applied -> Train Set: {len(X_train)} samples | Test Set: {len(X_test)} samples")

    # Feature Standardization
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Models Portfolio
    models = {
        'Random Forest (Tuned)': RandomForestClassifier(n_estimators=300, max_depth=8, min_samples_split=4, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, learning_rate=0.08, max_depth=5, random_state=42),
        'Extra Trees': ExtraTreesClassifier(n_estimators=300, max_depth=10, random_state=42),
        'Support Vector Machine (RBF)': SVC(kernel='rbf', C=2.0),
        'Logistic Regression': LogisticRegression(C=1.0, max_iter=1000),
        'K-Nearest Neighbors': KNeighborsClassifier(n_neighbors=7)
    }

    if HAS_XGB:
        models['XGBoost Classifier'] = XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.05, eval_metric='logloss', random_state=42)

    print("\n4. Training and Evaluating Models...")
    results = []
    trained_models = {}

    for name, model in models.items():
        model.fit(X_train_scaled, y_train)
        trained_models[name] = model
        pred = model.predict(X_test_scaled)

        acc = accuracy_score(y_test, pred)
        prec = precision_score(y_test, pred, zero_division=0)
        rec = recall_score(y_test, pred, zero_division=0)
        f1 = f1_score(y_test, pred, zero_division=0)

        results.append({
            'Model': name,
            'Accuracy (%)': round(acc * 100, 2),
            'Precision (%)': round(prec * 100, 2),
            'Recall (%)': round(rec * 100, 2),
            'F1-Score (%)': round(f1 * 100, 2)
        })

    res_df = pd.DataFrame(results).sort_values('Accuracy (%)', ascending=False).reset_index(drop=True)

    print("\n" + "=" * 65)
    print("MODEL LEADERBOARD RANKED BY TEST ACCURACY (80:20 SPLIT):")
    print("=" * 65)
    print(res_df.to_string(index=True))

    champion_name = res_df.iloc[0]['Model']
    champion_acc = res_df.iloc[0]['Accuracy (%)']
    print("\n" + "=" * 65)
    print(f"CHAMPION MODEL: {champion_name} with {champion_acc}% Accuracy!")
    print("=" * 65)

    champion_model = trained_models[champion_name]
    y_pred_best = champion_model.predict(X_test_scaled)
    cm = confusion_matrix(y_test, y_pred_best)
    print(f"\nConfusion Matrix for {champion_name}:")
    print(f" [[True Negatives (Down): {cm[0][0]}, False Positives: {cm[0][1]}],")
    print(f"  [False Negatives: {cm[1][0]}, True Positives (Up): {cm[1][1]}]]")

    if hasattr(champion_model, 'feature_importances_'):
        imp_series = pd.Series(champion_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
        print("\nFeature Importance Breakdown:")
        for feat, imp in imp_series.items():
            print(f"  • {feat:16s}: {imp * 100:5.2f}%")

if __name__ == '__main__':
    main()
