import pandas as pd
import joblib

# load the trained model + the feature order it expects
bundle = joblib.load("hire_model.pkl")
model, feat_cols = bundle["model"], bundle["features"]

df = pd.read_csv("resume_dataset_200k_enhanced.csv")

# pick a few candidates to score (first 10 rows here — change as you like)
sample = df.head(10).copy()
ids = sample["candidate_id"].tolist()
actual = sample["hired"].tolist()

# apply the SAME encoding used in training
if "education_level" in sample:
    sample["education_level"] = sample["education_level"].map({"Bachelors": 1, "Masters": 2, "PhD": 3})
if "university_tier" in sample:
    sample["university_tier"] = sample["university_tier"].map({"Tier 1": 3, "Tier 2": 2, "Tier 3": 1})
sample = pd.get_dummies(sample, columns=[c for c in ["company_type"] if c in sample])

# align to the model's feature columns (fill any missing dummy with 0)
X = sample.reindex(columns=feat_cols, fill_value=0)

proba = model.predict_proba(X)[:, 1]

print("=== ML HIRE PREDICTIONS (model: hire_model.pkl) ===")
print(f"{'cand_id':>8} {'hire_prob':>10} {'ml_decision':>12} {'actual':>8}")
for cid, p, a in zip(ids, proba, actual):
    decision = "HIRE" if p >= 0.5 else "REJECT"
    print(f"{cid:>8} {p:>10.3f} {decision:>12} {int(a):>8}")
