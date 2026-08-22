import os
from pathlib import Path
from dotenv import load_dotenv

# Read .env ONCE, for the whole app.
load_dotenv(Path(__file__).resolve().parent.parent / ".env", encoding="utf-8-sig")

# --- LLM provider (any OpenAI-compatible endpoint) ------------------------
# Works with the official OpenAI API out of the box. To use a compatible
# proxy/gateway (LiteLLM, Azure OpenAI, local vLLM/Ollama, etc.), set
# OPENAI_BASE_URL to that endpoint.
OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL") or None      # None -> api.openai.com

# Some corporate proxies use self-signed certs. Set OPENAI_VERIFY_SSL=false to
# skip TLS verification (leave it enabled everywhere else).
VERIFY_SSL      = os.environ.get("OPENAI_VERIFY_SSL", "true").lower() != "false"

DATABASE_URL    = os.environ.get("DATABASE_URL", "sqlite:///./recruitment.db")
