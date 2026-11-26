"""
Generate notebooks/01_model_training.ipynb
NSE Stock OHLCV dataset → preprocess → 80/20 split → train multiple ML models → compare → save best model
"""
import nbformat
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

nb = new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3 (venv)",
        "language": "python",
        "name": "python3"
    },
    "language_info": {"name": "python", "version": "3.11.0"}
}

cells = []

# ── Cell 1: Imports & Setup ────────────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 1 — Imports & Setup"))
cells.append(new_code_cell("""
import os, glob, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, confusion_matrix,
                              classification_report)
import joblib
import xgboost as xgb
import lightgbm as lgb

warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', 50)
pd.set_option('display.float_format', '{:.4f}'.format)
print("All libraries loaded successfully ✓")
"""))

# ── Cell 2: Load Dataset ──────────────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 2 — Load & Inspect Dataset"))
cells.append(new_code_cell("""
# Load all Stock_*.xlsx files from archive_data/
DATA_DIR = os.path.join('..', 'archive_data')
stock_files = glob.glob(os.path.join(DATA_DIR, 'Stock_*.xlsx'))
print(f"Found {len(stock_files)} stock files")

dfs = []
for f in stock_files:
    ticker = os.path.basename(f).replace('Stock_', '').replace('.xlsx', '')
    df = pd.read_excel(f)
    df['Ticker'] = ticker
    dfs.append(df)

raw_df = pd.concat(dfs, ignore_index=True)
print(f"\\nTotal rows: {len(raw_df):,}")
print(f"Columns: {list(raw_df.columns)}")
raw_df.head()
"""))

# ── Cell 3: Data Validation & Preprocessing ───────────────────────────────
cells.append(new_markdown_cell("## Cell 3 — Data Validation & Preprocessing"))
cells.append(new_code_cell("""
df = raw_df.copy()

# ── 3a. Column name normalisation ────────────────────────────────────────
df.columns = [c.strip().title() for c in df.columns]
print("Normalised columns:", list(df.columns))

# Try to find the Date column
date_col = next((c for c in df.columns if 'date' in c.lower()), None)
print(f"Date column detected: {date_col}")

# ── 3b. Missing-value report ─────────────────────────────────────────────
missing = df.isnull().sum()
missing_pct = (missing / len(df) * 100).round(2)
missing_report = pd.DataFrame({'Missing': missing, 'Pct(%)': missing_pct})
print("\\n── Missing Values ──")
print(missing_report[missing_report['Missing'] > 0])

# ── 3c. Duplicate dates per ticker ───────────────────────────────────────
if date_col:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    dup_dates = df[df.duplicated(subset=[date_col, 'Ticker'], keep=False)]
    print(f"\\nDuplicate (date, ticker) rows: {len(dup_dates)}")
    df = df.drop_duplicates(subset=[date_col, 'Ticker'], keep='first')
    print(f"After dedup: {len(df):,} rows")

# ── 3d. Inconsistency checks ─────────────────────────────────────────────
# Map to standard OHLCV names
col_map = {}
for c in df.columns:
    cl = c.lower()
    if 'open' in cl:   col_map[c] = 'Open'
    elif 'high' in cl: col_map[c] = 'High'
    elif 'low' in cl:  col_map[c] = 'Low'
    elif 'close' in cl and 'prev' not in cl: col_map[c] = 'Close'
    elif 'volume' in cl or 'vol' == cl: col_map[c] = 'Volume'
    elif 'shares' in cl or 'turnover' in cl: col_map[c] = 'Turnover'
    elif date_col and c == date_col: col_map[c] = 'Date'
    elif c == 'Ticker': col_map[c] = 'Ticker'
df = df.rename(columns=col_map)
print(f"\\nAfter rename columns: {list(df.columns)}")

ohlcv_cols = [c for c in ['Open','High','Low','Close','Volume'] if c in df.columns]
print("OHLCV cols present:", ohlcv_cols)

# High >= Low
if 'High' in df.columns and 'Low' in df.columns:
    bad_hl = df[df['High'] < df['Low']]
    print(f"Rows where High < Low: {len(bad_hl)}")
    df = df[df['High'] >= df['Low']]

# No negative prices
for c in ['Open','High','Low','Close']:
    if c in df.columns:
        neg = (df[c] <= 0).sum()
        print(f"Non-positive {c}: {neg}")
        df = df[df[c] > 0]

# Drop NaN in OHLCV
df = df.dropna(subset=ohlcv_cols)
print(f"\\nClean rows after all checks: {len(df):,}")
df.describe()
"""))

# ── Cell 4: Feature Engineering ───────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 4 — Feature Engineering & Target Variable"))
cells.append(new_code_cell("""
# Sort by ticker and date for lag features
if 'Date' in df.columns:
    df = df.sort_values(['Ticker', 'Date']).reset_index(drop=True)

# ── Price-based features ──────────────────────────────────────────────────
df['Daily_Return'] = df.groupby('Ticker')['Close'].pct_change()
df['Log_Return']   = np.log(df['Close'] / df.groupby('Ticker')['Close'].shift(1))
df['Price_Range']  = df['High'] - df['Low']
df['Price_Range_Pct'] = df['Price_Range'] / df['Close']

# Moving averages (5-day, 20-day)
df['MA5']  = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(5).mean())
df['MA20'] = df.groupby('Ticker')['Close'].transform(lambda x: x.rolling(20).mean())
df['MA5_20_Cross'] = (df['MA5'] > df['MA20']).astype(int)

# RSI-14
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

df['RSI14'] = df.groupby('Ticker')['Close'].transform(compute_rsi)

# Volume-based
if 'Volume' in df.columns:
    df['Vol_MA5']   = df.groupby('Ticker')['Volume'].transform(lambda x: x.rolling(5).mean())
    df['Vol_Ratio'] = df['Volume'] / (df['Vol_MA5'] + 1)

# ── Target: next-day direction (1 = up, 0 = down/flat) ───────────────────
df['Next_Close']  = df.groupby('Ticker')['Close'].shift(-1)
df['Target']      = (df['Next_Close'] > df['Close']).astype(int)

# Drop NaN rows created by rolling / shift
feature_cols = [
    'Daily_Return', 'Log_Return', 'Price_Range', 'Price_Range_Pct',
    'MA5', 'MA20', 'MA5_20_Cross', 'RSI14'
]
if 'Volume' in df.columns:
    feature_cols += ['Vol_MA5', 'Vol_Ratio']

df = df.dropna(subset=feature_cols + ['Target'])
print(f"Dataset ready: {len(df):,} rows | {len(feature_cols)} features | Target balance:")
print(df['Target'].value_counts(normalize=True).round(4))
"""))

# ── Cell 5: Train-Test Split ───────────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 5 — 80 / 20 Train-Test Split"))
cells.append(new_code_cell("""
X = df[feature_cols].values
y = df['Target'].values

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

# Scale features
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print(f"Train size : {X_train.shape[0]:,} rows")
print(f"Test  size : {X_test.shape[0]:,} rows")
print(f"Features   : {len(feature_cols)}")
"""))

# ── Cell 6: Model Training & Comparison ───────────────────────────────────
cells.append(new_markdown_cell("## Cell 6 — Model Training & Comparison"))
cells.append(new_code_cell("""
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
    'Decision Tree':       DecisionTreeClassifier(max_depth=10, random_state=42),
    'Random Forest':       RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1),
    'Gradient Boosting':   GradientBoostingClassifier(n_estimators=200, max_depth=5, random_state=42),
    'XGBoost':             xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                              use_label_encoder=False, eval_metric='logloss', random_state=42),
    'LightGBM':            lgb.LGBMClassifier(n_estimators=200, max_depth=6, learning_rate=0.1,
                                               random_state=42, verbose=-1),
    'SVM':                 SVC(kernel='rbf', probability=True, random_state=42),
    'KNN':                 KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
}

results = []
trained_models = {}

for name, model in models.items():
    print(f"Training {name}...", end=' ', flush=True)
    # Use scaled data for distance-based / linear; tree-based work on raw
    use_scaled = name in ('Logistic Regression', 'SVM', 'KNN')
    Xtr = X_train_sc if use_scaled else X_train
    Xte = X_test_sc  if use_scaled else X_test
    
    model.fit(Xtr, y_train)
    y_pred  = model.predict(Xte)
    y_proba = model.predict_proba(Xte)[:, 1] if hasattr(model, 'predict_proba') else y_pred
    
    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    auc  = roc_auc_score(y_test, y_proba)
    
    results.append({
        'Model': name,
        'Accuracy': acc,
        'Precision': prec,
        'Recall': rec,
        'F1-Score': f1,
        'ROC-AUC': auc
    })
    trained_models[name] = (model, use_scaled)
    print(f"Accuracy={acc:.4f}")

results_df = pd.DataFrame(results).sort_values('Accuracy', ascending=False).reset_index(drop=True)
print("\\n" + "="*70)
print("MODEL COMPARISON REPORT")
print("="*70)
print(results_df.to_string(index=False))

# Flag if any model exceeds 90%
if results_df['Accuracy'].max() >= 0.90:
    best_name = results_df.iloc[0]['Model']
    print(f"\\n✅ Best model: {best_name} — Accuracy: {results_df.iloc[0]['Accuracy']:.4f} (>90%)")
else:
    print("\\n⚠️ No model reached 90% — will apply hyperparameter tuning in next cell")
"""))

# ── Cell 7: Hyperparameter tuning if needed ────────────────────────────────
cells.append(new_markdown_cell("## Cell 7 — Hyperparameter Tuning (if best < 90%)"))
cells.append(new_code_cell("""
from sklearn.model_selection import RandomizedSearchCV

best_acc = results_df['Accuracy'].max()

if best_acc < 0.90:
    print("Best accuracy below 90% — tuning Random Forest & XGBoost...")
    
    rf_params = {
        'n_estimators': [300, 500],
        'max_depth': [15, 20, None],
        'min_samples_split': [2, 5],
        'max_features': ['sqrt', 'log2']
    }
    rf = RandomForestClassifier(random_state=42, n_jobs=-1)
    rf_search = RandomizedSearchCV(rf, rf_params, n_iter=10, cv=3,
                                   scoring='accuracy', random_state=42, n_jobs=-1)
    rf_search.fit(X_train, y_train)
    rf_best = rf_search.best_estimator_
    rf_acc  = accuracy_score(y_test, rf_best.predict(X_test))
    print(f"Tuned RF accuracy: {rf_acc:.4f}")
    trained_models['Random Forest (Tuned)'] = (rf_best, False)
    
    xgb_params = {
        'n_estimators': [300, 500],
        'max_depth': [6, 8],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8, 1.0],
        'colsample_bytree': [0.8, 1.0]
    }
    xgb_m = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_search = RandomizedSearchCV(xgb_m, xgb_params, n_iter=10, cv=3,
                                     scoring='accuracy', random_state=42, n_jobs=-1)
    xgb_search.fit(X_train, y_train)
    xgb_best = xgb_search.best_estimator_
    xgb_acc  = accuracy_score(y_test, xgb_best.predict(X_test))
    print(f"Tuned XGB accuracy: {xgb_acc:.4f}")
    trained_models['XGBoost (Tuned)'] = (xgb_best, False)
    
    # Rebuild results
    new_rows = []
    for n, (m, sc) in [('Random Forest (Tuned)', (rf_best, False)),
                        ('XGBoost (Tuned)', (xgb_best, False))]:
        yp = m.predict(X_test)
        yr = m.predict_proba(X_test)[:, 1]
        new_rows.append({'Model': n,
                         'Accuracy': accuracy_score(y_test, yp),
                         'Precision': precision_score(y_test, yp, zero_division=0),
                         'Recall': recall_score(y_test, yp, zero_division=0),
                         'F1-Score': f1_score(y_test, yp, zero_division=0),
                         'ROC-AUC': roc_auc_score(y_test, yr)})
    results_df = pd.concat([results_df, pd.DataFrame(new_rows)], ignore_index=True)
    results_df = results_df.sort_values('Accuracy', ascending=False).reset_index(drop=True)

print("\\nFinal Rankings:")
print(results_df.to_string(index=False))
"""))

# ── Cell 8: Comparison Chart ──────────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 8 — Comparison Chart"))
cells.append(new_code_cell("""
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

metrics = ['Accuracy', 'F1-Score', 'ROC-AUC']
x = np.arange(len(results_df))
width = 0.25

for i, m in enumerate(metrics[:2]):
    axes[0].bar(x + i*width, results_df[m], width, label=m)
axes[0].axhline(0.9, color='red', linestyle='--', label='90% threshold')
axes[0].set_xticks(x + width/2)
axes[0].set_xticklabels(results_df['Model'], rotation=35, ha='right', fontsize=9)
axes[0].set_title('Model Performance Metrics')
axes[0].set_ylim(0, 1.05)
axes[0].legend()

# ROC-AUC bar
axes[1].barh(results_df['Model'], results_df['ROC-AUC'], color='steelblue')
axes[1].axvline(0.9, color='red', linestyle='--', label='90% AUC')
axes[1].set_title('ROC-AUC by Model')
axes[1].set_xlabel('ROC-AUC')
axes[1].legend()

plt.tight_layout()
plt.savefig('model_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
print("Chart saved as model_comparison.png")
"""))

# ── Cell 9: Save Best Model ────────────────────────────────────────────────
cells.append(new_markdown_cell("## Cell 9 — Save Best Model"))
cells.append(new_code_cell("""
best_model_name = results_df.iloc[0]['Model']
best_model_obj, best_uses_scaled = trained_models[best_model_name]

# Save model, scaler, feature list
os.makedirs('.', exist_ok=True)
joblib.dump(best_model_obj, 'best_model.pkl')
joblib.dump(scaler,         'scaler.pkl')
joblib.dump(feature_cols,   'feature_columns.pkl')

print(f"Best model : {best_model_name}")
print(f"Accuracy   : {results_df.iloc[0]['Accuracy']:.4f}")
print(f"F1-Score   : {results_df.iloc[0]['F1-Score']:.4f}")
print(f"ROC-AUC    : {results_df.iloc[0]['ROC-AUC']:.4f}")
print(f"Uses scaled: {best_uses_scaled}")
print("\\nSaved: best_model.pkl, scaler.pkl, feature_columns.pkl ✓")
"""))

# ── Cell 10: Confusion Matrix & Classification Report ─────────────────────
cells.append(new_markdown_cell("## Cell 10 — Confusion Matrix & Classification Report (Best Model)"))
cells.append(new_code_cell("""
Xte_final = X_test_sc if best_uses_scaled else X_test
y_pred_best = best_model_obj.predict(Xte_final)

# Confusion matrix
cm = confusion_matrix(y_test, y_pred_best)
fig, ax = plt.subplots(figsize=(6, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
            xticklabels=['Down/Flat', 'Up'],
            yticklabels=['Down/Flat', 'Up'])
ax.set_title(f'Confusion Matrix — {best_model_name}')
ax.set_ylabel('Actual')
ax.set_xlabel('Predicted')
plt.tight_layout()
plt.savefig('confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.show()

print("\\nClassification Report:")
print(classification_report(y_test, y_pred_best, target_names=['Down/Flat', 'Up']))
"""))

# ── Assemble notebook ─────────────────────────────────────────────────────
nb.cells = cells
out_path = os.path.join(os.path.dirname(__file__), '01_model_training.ipynb')
with open(out_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)
print(f"Written: {out_path}")
