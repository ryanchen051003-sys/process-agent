from fastapi import FastAPI

app = FastAPI(title="process-agent")


@app.get("/health")
def health():
    return {"status": "ok", "service": "process-agent"}