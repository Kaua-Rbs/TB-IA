#!/usr/bin/env python
import argparse
import json
import urllib.request

from backend.seed import synthetic_questionnaires


def post_seed(api_url: str) -> None:
    request = urllib.request.Request(
        api_url.rstrip("/") + "/seed/synthetic",
        data=b"",
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        print(response.read().decode("utf-8"))


def print_local_payload() -> None:
    payload = [item.model_dump(mode="json") for item in synthetic_questionnaires()]
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Carrega ou imprime seed sintetico.")
    parser.add_argument("--api", help="URL base da API FastAPI, por exemplo http://127.0.0.1:8000")
    args = parser.parse_args()

    if args.api:
        post_seed(args.api)
    else:
        print_local_payload()


if __name__ == "__main__":
    main()

