import os
import sys

import httpx


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        print(f"Missing environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    base_url = require_env("MODEL_BASE_URL").rstrip("/")
    model = require_env("MODEL_NAME")
    api_key = require_env("MODEL_API_KEY")

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Reply with one short sentence: Stage 1 model call works.",
            }
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
    except httpx.HTTPError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if response.status_code >= 400:
        print(f"HTTP {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    data = response.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        print(f"Unexpected response: {data}", file=sys.stderr)
        sys.exit(1)

    print(text)


if __name__ == "__main__":
    main()
