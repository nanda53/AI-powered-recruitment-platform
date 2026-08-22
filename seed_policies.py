import requests
BASE = "http://localhost:8000"

POLICIES = {
    "Leave Policy": (
        "Annual Leave Policy. Full-time employees accrue 24 days of paid leave per year. "
        "Requests must be submitted at least 5 working days in advance. Up to 10 unused days "
        "may be carried over into the next year."),
    "Interview Panel Policy": (
        "Interview Panel Policy. Every technical interview panel must include at least two "
        "engineers, at least one of whom is senior. Panels should reflect diverse backgrounds "
        "to reduce bias. Panels of 2-3 people are standard. Protected attributes such as age, "
        "gender, religion, or ethnicity must never be discussed or considered."),
    "Referral Policy": (
        "Employee Referral Policy. Referred candidates follow the same screening process as "
        "all applicants. The referring employee receives a bonus after the new hire completes "
        "90 days of employment."),
    "Compensation Policy": (
        "Compensation Policy. Salary bands by level: Junior (0-2 yrs) $70,000-$90,000; "
        "Mid (3-5 yrs) $95,000-$120,000; Senior (6-9 yrs) $125,000-$155,000; "
        "Staff (10+ yrs) $160,000-$190,000. Add up to 10% for scarce skills such as AWS, "
        "Kubernetes, or machine learning. Education above the role's requirement adds up to 5%. "
        "Final offers must stay within the band for the assessed level."),
}

for title, text in POLICIES.items():
    r = requests.post(f"{BASE}/policies", json={"title": title, "text": text})
    print(f"{title:24} -> {r.status_code} {r.text[:80]}")
