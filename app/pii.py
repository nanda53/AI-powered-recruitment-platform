import json

from app.llm import chat

PII_SYSTEM = (
    "Extract personal identifiers from this resume as JSON with keys: "
    "name, email, phone, address, gender, age. Use null if absent. "
    "Output JSON only."
)

def extract_pii(raw_text: str) -> dict:
    r = chat("classify").invoke([("system", PII_SYSTEM), ("human", raw_text)])
    try:    return json.loads(r.content)
    except: return {}
