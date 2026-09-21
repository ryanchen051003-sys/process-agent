from datetime import datetime, timezone
from pathlib import Path
import logging
import os

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from retrieve import search_docs

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("process-agent")

app = FastAPI(title="process-agent")


class AskRequest(BaseModel):
    question: str
    lang: str


class AskResponse(BaseModel):
    answer: str
    source: str
    error: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "process-agent"}


def _prompt_path(lang: str) -> Path:
    key = "zh" if lang.lower().startswith("zh") else "en"
    return PROMPTS_DIR / f"{key}.txt"


def _load_prompt(lang: str, question: str, docs: str) -> str | None:
    path = _prompt_path(lang)
    try:
        template = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("prompt file missing: %s", path.name)
        return None
    return template.replace("{docs}", docs).replace("{question}", question)


def _one_model_call(
    url: str,
    headers: dict,
    payload: dict,
    attempt: int,
) -> tuple[str | None, str | None]:
    """Return (text, error). text set means success."""
    logger.info("model call attempt %s", attempt)
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=20.0)
    except httpx.TimeoutException:
        logger.warning("model call attempt %s failed: timeout after 20s", attempt)
        return None, "model timeout after 20s"
    except httpx.HTTPError as exc:
        logger.warning(
            "model call attempt %s failed: network error %s",
            attempt,
            exc.__class__.__name__,
        )
        return None, "model network error"

    if response.status_code >= 400:
        logger.warning(
            "model call attempt %s failed: HTTP %s",
            attempt,
            response.status_code,
        )
        return None, f"model HTTP {response.status_code}"

    try:
        text = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError):
        logger.warning("model call attempt %s failed: unexpected response shape", attempt)
        return None, "model returned an unexpected response"

    if not text or not str(text).strip():
        logger.warning("model call attempt %s failed: empty content", attempt)
        return None, "model returned an empty answer"

    logger.info("model call attempt %s succeeded", attempt)
    return str(text).strip(), None


def _chat(question: str, lang: str) -> tuple[str, str, str | None]:
    """Return (answer, source, error). Never raises to the caller."""
    base_url = os.environ.get("MODEL_BASE_URL", "").strip().rstrip("/")
    model = os.environ.get("MODEL_NAME", "").strip()
    api_key = os.environ.get("MODEL_API_KEY", "").strip()
    if not base_url or not model or not api_key:
        logger.warning("model call failed: missing environment variable")
        return "", "", "missing MODEL_BASE_URL, MODEL_NAME, or MODEL_API_KEY"

    hits = search_docs(question, lang)
    if not hits:
        logger.info("retrieve: no relevant chunk")
        if lang.lower().startswith("zh"):
            return "根据现有政策文档，无法确定。", "none", None
        return "Not specified in the policy documents.", "none", None

    docs_block = "\n\n".join(f"[{h['path']}]\n{h['text']}" for h in hits)
    source = " | ".join(dict.fromkeys(h["path"] for h in hits))
    logger.info("retrieve hits=%s", source)

    content = _load_prompt(lang, question, docs_block)
    if content is None:
        return "", "", "prompt file missing"

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error = "model call failed"
    for attempt in (1, 2):
        text, error = _one_model_call(url, headers, payload, attempt)
        if error is None and text is not None:
            return text, source, None
        last_error = error or last_error
        if attempt == 1:
            logger.info("retrying model call once")

    return "", "", last_error


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    now = datetime.now(timezone.utc).isoformat()
    logger.info(
        "POST /ask time=%s question=%r lang=%r",
        now,
        body.question,
        body.lang,
    )
    answer, source, error = _chat(body.question, body.lang)
    return AskResponse(answer=answer, source=source, error=error)
