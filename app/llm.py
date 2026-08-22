import os

import httpx
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import OPENAI_API_KEY, OPENAI_BASE_URL, VERIFY_SSL

# Shared HTTP client. verify=False only when OPENAI_VERIFY_SSL=false (self-signed proxies).
_client = httpx.Client(verify=VERIFY_SSL)

# Role -> model name. Defaults are standard OpenAI models; override any of them
# with an env var (e.g. MODEL_GENERATE=gpt-4o) to point a role at a different model.
MODELS = {
    "parse":    os.environ.get("MODEL_PARSE",    "gpt-4o-mini"),   # resume -> JSON
    "classify": os.environ.get("MODEL_CLASSIFY", "gpt-4o-mini"),   # cheap checks / PII
    "match":    os.environ.get("MODEL_MATCH",    "gpt-4o"),        # JD matcher
    "agent":    os.environ.get("MODEL_AGENT",    "gpt-4o"),        # agent reasoning
    "generate": os.environ.get("MODEL_GENERATE", "gpt-4o"),        # summaries / questions
}
EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-large")

def chat(role: str = "parse", temperature: float = 0, **kw) -> ChatOpenAI:
    return ChatOpenAI(base_url=OPENAI_BASE_URL, model=MODELS[role],
                      api_key=OPENAI_API_KEY, http_client=_client,
                      temperature=temperature, **kw)

def embedder() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(base_url=OPENAI_BASE_URL, model=EMBED_MODEL,
                            api_key=OPENAI_API_KEY, http_client=_client)
