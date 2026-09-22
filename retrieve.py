from pathlib import Path
import logging

import chromadb

logger = logging.getLogger("process-agent")

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
DATA_DIR = ROOT / "data" / "chroma"
COLLECTION = "policies"
TENANTS = {"A", "B"}

_TOPIC_KEYS = (
    (("年假", "年休假", "annual leave", "annual leave days"), "leave-annual"),
    (("病假", "sick leave"), "leave-sick"),
    (("事假", "personal leave"), "leave-personal"),
    (("差旅", "出差", "travel expense"), "expense-travel"),
    (("加班餐", "招待", "餐饮", "meal"), "expense-meal"),
)


def _client():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(DATA_DIR))


def _collection(reset: bool = False):
    client = _client()
    if reset:
        try:
            client.delete_collection(COLLECTION)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def _chunks_from_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8").strip()
    parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not parts:
        return [text] if text else []
    return parts


def ingest_docs() -> int:
    col = _collection(reset=True)
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    index = 0
    for path in sorted(DOCS_DIR.rglob("*.md")):
        lang = "zh" if path.name.endswith(".zh.md") else "en"
        rel = path.relative_to(DOCS_DIR).as_posix()
        tenant = rel.split("/", 1)[0] if "/" in rel else "shared"
        for chunk in _chunks_from_file(path):
            ids.append(f"{rel}-{index}")
            documents.append(chunk)
            metadatas.append(
                {
                    "path": f"docs/{rel}",
                    "lang": lang,
                    "tenant": tenant,
                }
            )
            index += 1
    if documents:
        col.add(ids=ids, documents=documents, metadatas=metadatas)
    return len(documents)


def _lang_key(lang: str) -> str:
    return "zh" if lang.lower().startswith("zh") else "en"


def _topic_path(question: str, lang: str, tenant: str) -> str | None:
    if tenant not in TENANTS:
        return None
    q = question.lower()
    key = _lang_key(lang)
    for words, stem in _TOPIC_KEYS:
        if any(word.lower() in q for word in words):
            return f"docs/{tenant}/{stem}.{key}.md"
    return None


def search_docs(question: str, lang: str, tenant: str, k: int = 3) -> list[dict]:
    tenant = (tenant or "").strip().upper()
    topic = _topic_path(question, lang, tenant)
    logger.info(
        "retrieve question=%r lang=%r tenant=%r topic=%r",
        question,
        lang,
        tenant,
        topic,
    )
    if not topic:
        return []
    path = ROOT / topic
    if not path.is_file():
        logger.warning("retrieve file missing: %s", path)
        return []
    prefix = f"docs/{tenant}/"
    suffix = f".{_lang_key(lang)}.md"
    hits = []
    for chunk in _chunks_from_file(path):
        if not topic.startswith(prefix) or not topic.endswith(suffix):
            continue
        hits.append({"text": chunk, "path": topic, "distance": 0.0})
    return hits
