# Phase 4: RAG over HR policy documents

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.llm import embedder

VECTOR_DIR = "./chroma_policies"
_splitter  = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)


def _store() -> Chroma:
    return Chroma(collection_name="hr_policies",
                  embedding_function=embedder(),
                  persist_directory=VECTOR_DIR)

def ingest_policy(title: str, source: str, text: str):
    chunks = _splitter.split_text(text)
    metadatas = [{"title": title, "source": source, "chunk": i}
                 for i in range(len(chunks))]
    _store().add_texts(chunks, metadatas=metadatas)     # embeds via text-embedding-3-large


def retrieve(query: str, k: int = 4) -> list[dict]:
    hits = _store().similarity_search_with_score(query, k=k)
    return [{
        "text": d.page_content,
        "citation": f'{d.metadata.get("title")} ({d.metadata.get("source")})',
        "score": round(float(s), 3),
    } for d, s in hits]
