from datetime import datetime, timezone
from pathlib import Path
import logging
import os

import httpx

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
from fastapi import FastAPI
from pydantic import BaseModel

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


def _load_prompt(lang: str, question: str) -> str | None:
    path = _prompt_path(lang)
    try:
        template = path.read_text(encoding="utf-8")
    except OSError:
        logger.warning("prompt file missing: %s", path.name)
        return None
    return template.replace("{question}", question)


def _chat(question: str, lang: str) -> tuple[str, str, str | None]:
    """Return (answer, source, error). Never raises to the caller."""
    base_url = os.environ.get("MODEL_BASE_URL", "").strip().rstrip("/")
    model = os.environ.get("MODEL_NAME", "").strip()
    api_key = os.environ.get("MODEL_API_KEY", "").strip()
    if not base_url or not model or not api_key:
        logger.warning("model call failed: missing environment variable")
        return "", "", "missing MODEL_BASE_URL, MODEL_NAME, or MODEL_API_KEY"

    content = _load_prompt(lang, question)
    if content is None:
        return "", "", "prompt file missing"

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": content,
            }
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=20.0)
    except httpx.TimeoutException:
        logger.warning("model call failed: timeout after 20s")
        return "", "", "model timeout after 20s"
    except httpx.HTTPError as exc:
        logger.warning("model call failed: network error %s", exc.__class__.__name__)
        return "", "", "model network error"

    if response.status_code >= 400:
        logger.warning("model call failed: HTTP %s", response.status_code)
        return "", "", f"model HTTP {response.status_code}"

    try:
        text = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError):
        logger.warning("model call failed: unexpected response shape")
        return "", "", "model returned an unexpected response"

    if not text or not str(text).strip():
        logger.warning("model call failed: empty content")
        return "", "", "model returned an empty answer"

    return str(text).strip(), f"model:{model}", None


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
