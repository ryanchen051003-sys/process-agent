# process-agent

Learning project: Q&A for expense reimbursement and leave policy.

Flow: ask a question → look up fake documents or call a fake tool → answer with a source → log failures.

This is a personal pre-joining project. It is not a Kingdee production system.

## Current stage

Stage 0 — engineering baseline.

- Done: `GET /health`
- Not built: model call, retrieval, real tools, Docker

## What you need

- Python 3.11 or newer
- This repository cloned to your machine

## Run (Windows)

Open PowerShell in the project folder.

### Step 1 — virtual environment

Skip the first line if `.venv` already exists.

    python -m venv .venv
    .venv\Scripts\activate

### Step 2 — install dependencies

    pip install -r requirements.txt

### Step 3 — start the service

    uvicorn main:app --reload --host 127.0.0.1 --port 8000

Leave that window open. The terminal should print a line that contains:

    Uvicorn running on http://127.0.0.1:8000

### Step 4 — check it works

Browser:

    http://127.0.0.1:8000/health

Or a second PowerShell window:

    Invoke-RestMethod http://127.0.0.1:8000/health

Expected:

    {"status":"ok","service":"process-agent"}

API docs: http://127.0.0.1:8000/docs

## Run (macOS / Linux)

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

Then open http://127.0.0.1:8000/health

## Configuration

Stage 0 does not use a model API key.

Do not commit `.env` or secrets.

## License

Personal learning use.
