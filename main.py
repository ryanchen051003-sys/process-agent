from datetime import datetime, timezone
import logging

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


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    now = datetime.now(timezone.utc).isoformat()
    logger.info(
        "POST /ask time=%s question=%r lang=%r",
        now,
        body.question,
        body.lang,
    )
    return AskResponse(
        answer="Mock answer. No model is connected in Stage 0.",
        source="mock",
        error=None,
    )
