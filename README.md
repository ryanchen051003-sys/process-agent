# process-agent

Learning project: Q&A for expense reimbursement and leave policy.

Flow: ask a question → look up fake documents or call a fake tool → answer with a source → log failures.

This is a personal pre-joining project. It is not a Kingdee production system.

## Current stage

Stage 2 closing — retrieve fake docs, then answer with a file `source`.

- Done: `docs/` fake policies; Chroma ingest; `/ask` finds a doc before the model; `lang` picks `.zh.md` / `.en.md`; `tenant=A|B` folders; unknown questions return `source=none`
- TBD: wire `tools.py` into `/ask`; restore vector `query` as the primary lookup; Docker

This is still a personal learning project. It is not a Kingdee production system.

## Stage 2 pipeline and a failure we hit

Ask `POST /ask` with `question`, `lang`, and `tenant`. The service maps the question to one markdown file under `docs/{tenant}/`, fills `{docs}` in the prompt, then calls the model. The JSON `source` is that file path. If no topic matches (for example a made-up benefit), it does not call the model and returns “not specified”, `source=none`.

Retrieval failed twice on the way here. PowerShell often garbled Chinese, so `/docs` must be used for CJK questions. A pure Chroma `query` plus `where={"path": ...}` also came back empty on this machine even after ingest, so `/ask` now opens the matched markdown file directly. Chroma is still used for `python ingest_docs.py`. Swapping vendors or claiming this is live at Kingdee is out of scope.

## Layout

    .gitignore
    README.md
    requirements.txt
    pytest.ini
    main.py          # FastAPI: /health and POST /ask (model)
    tools.py         # fake get_leave_balance / get_bill_status
    call_model.py    # one-shot model call
    .env.example
    prompts/
        zh.txt       # Chinese system+user template, placeholder {question}
        en.txt
    docs/            # fake leave and expense policies, zh/en pairs
    retrieve.py      # chunk + Chroma search
    ingest_docs.py   # load docs/ into data/chroma/
    data/            # local Chroma files, gitignored
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

### Step 5 — ingest documents (once, after clone or after editing docs/)

    pip install -r requirements.txt
    python ingest_docs.py

Expected: a line like `ingested N chunks from docs/`. First run may download a small embedding model.

### Step 6 — POST /ask (retrieve, then model)

    Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/ask -ContentType "application/json" -Body '{"question":"How many annual leave days after one year?","lang":"en","tenant":"A"}'

Expected: `answer` uses the tenant A document, `source` is a path such as `docs/A/leave-annual.en.md` or `docs/A/leave-annual.zh.md`, `error` is empty. Chinese questions are easier in http://127.0.0.1:8000/docs .

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

## Configuration

`POST /ask` and `call_model.py` read three environment variables. They are
not stored in the repository. Do not commit `.env` or paste a real key into
README. `.env.example` lists the names only.

| Name | Meaning | Example (fake) |
|---|---|---|
| `MODEL_BASE_URL` | Vendor HTTP root (script appends `/chat/completions`) | `https://api.deepseek.com` |
| `MODEL_NAME` | Model id | `deepseek-chat` |
| `MODEL_API_KEY` | Secret from the vendor console | set locally, never commit |

PowerShell, same window as `uvicorn`, before starting the server:

    $env:MODEL_BASE_URL="https://api.deepseek.com"
    $env:MODEL_NAME="deepseek-chat"
    $env:MODEL_API_KEY="your-key"

Changing these values requires stopping uvicorn with Ctrl+C and starting it again.

On failure the server retries the vendor call once. Logs contain
`model call attempt 1` and `model call attempt 2`. The JSON shape stays
`answer` / `source` / `error`. The process must not exit.

## License

Personal learning use.
