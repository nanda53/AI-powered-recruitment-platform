import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, average_precision_score
from xgboost import XGBClassifier

df = pd.read_csv("resume_dataset_200k_enhanced.csv")
print("shape:", df.shape)
print("columns:", list(df.columns))

TARGET = "hired"          # <-- change if your label column has a different name
print(df[TARGET].value_counts(normalize=True))

# encode the common categorical columns if they exist
if "education_level" in df:
    df["education_level"] = df["education_level"].map({"Bachelors": 1, "Masters": 2, "PhD": 3})
if "university_tier" in df:
    df["university_tier"] = df["university_tier"].map({"Tier 1": 3, "Tier 2": 2, "Tier 3": 1})
cat_cols = [c for c in ["company_type"] if c in df]
df = pd.get_dummies(df, columns=cat_cols)

drop = [c for c in ["candidate_id", TARGET] if c in df]
X = df.drop(columns=drop).select_dtypes("number")
y = df[TARGET]

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

neg, pos = (y_tr == 0).sum(), (y_tr == 1).sum()
model = XGBClassifier(
    n_estimators=2000, max_depth=6, learning_rate=0.03,
    subsample=0.8, colsample_bytree=0.8,
    scale_pos_weight=neg / pos, eval_metric="aucpr", early_stopping_rounds=50,
)
model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

proba = model.predict_proba(X_te)[:, 1]
pred = model.predict(X_te)
print("\n=== SCORE ===")
print(classification_report(y_te, pred))
print("ROC-AUC:", round(roc_auc_score(y_te, proba), 4))
print("PR-AUC :", round(average_precision_score(y_te, proba), 4))

# save the trained model + the exact feature order, for the demo predictor
joblib.dump({"model": model, "features": list(X.columns)}, "hire_model.pkl")
print("\nsaved model -> hire_model.pkl")
