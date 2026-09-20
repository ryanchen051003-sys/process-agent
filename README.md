# process-agent

Learning project: Q&A for expense reimbursement and leave policy.

Flow: ask a question → look up fake documents or call a fake tool → answer with a source → log failures.

This is a personal pre-joining project. It is not a Kingdee production system.

## Current stage

Stage 1 — `POST /ask` calls the model. No retrieval yet.

- Done: Stage 0 service, fake tools, tests, `call_model.py`, `/ask` uses env-configured model
- Not built: retrieval, wiring `tools.py` into `/ask`, Docker

## Layout

    .gitignore
    README.md
    requirements.txt
    pytest.ini
    main.py          # FastAPI: /health and POST /ask (model)
    tools.py         # fake get_leave_balance / get_bill_status
    call_model.py    # one-shot model call; not used by /ask yet
    .env.example     # env names only; copy to .env locally, never commit .env
    tests/
        test_tools.py

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

### Step 3 — set model env vars, then start the service

PowerShell (this window only; do not commit the key):

    $env:MODEL_BASE_URL="https://api.deepseek.com"
    $env:MODEL_NAME="deepseek-flash"
    $env:MODEL_API_KEY="your-key"

Then:

    uvicorn main:app --reload --host 127.0.0.1 --port 8000

Leave that window open. The terminal should print a line that contains:

    Uvicorn running on http://127.0.0.1:8000

### Step 4 — check /health

Browser:

    http://127.0.0.1:8000/health

Or a second PowerShell window:

    Invoke-RestMethod http://127.0.0.1:8000/health

Expected:

    {"status":"ok","service":"process-agent"}

API docs: http://127.0.0.1:8000/docs

### Step 5 — POST /ask (model)

    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType "application/json" -Body '{"question":"How many annual leave days in a typical policy?","lang":"en"}'

Expected: `answer` is model text (not the old mock sentence), `source` starts with `model:`, `error` is empty.

If the model is down or the key is wrong: HTTP 200 with an `error` string, server process still running.

Missing `question` should return HTTP 422.

## Tests

From the project folder, with `.venv` activated:

    pytest -q

Expected: two passed tests in `tests/test_tools.py` (hit + missing for leave and bill).

Windows example after a fresh clone:

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    pytest -q

## Run (macOS / Linux)

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pytest -q
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

Then open http://127.0.0.1:8000/health

## Call a model (Stage 1)

`POST /ask` does not use the model yet. Use the standalone script.

Set three environment variables. Any OpenAI-compatible provider works
(DeepSeek, Moonshot, OpenAI, a local gateway, etc.).

PowerShell (this window only):

    $env:MODEL_BASE_URL="https://api.example.com/v1"
    $env:MODEL_NAME="your-model-name"
    $env:MODEL_API_KEY="your-key"
    python call_model.py

Expected: one short sentence printed from the model. The script must not print the key.

Do not commit `.env` or secrets. `.env.example` is safe to commit.

## License

Personal learning use.
