"""Credential-safe Medium/Pinterest publishing adapter.

The adapter is intentionally fail-closed: no network publishing occurs unless the
required environment variables are present and PUBLISH_ENABLED=true. Secrets are
never written to repository files or logs.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path


MEDIUM_API = "https://api.medium.com/v1"
PINTEREST_API = "https://api.pinterest.com/v5"


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"PUBLISH BLOCKED: required secret/config {name} is missing")
    return value


def _request(url: str, token: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "amazon-desk-setup-automation/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"PUBLISH FAILED: HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"PUBLISH FAILED: network error: {exc.reason}") from exc


def parse_package(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    product_id = re.search(r"^Product ID:\s*(\S+)", text, re.M)
    product_name = re.search(r"^Product Name:\s*(.+)$", text, re.M)
    amazon_link = re.search(r"^Amazon Link:\s*(\S+)", text, re.M)
    medium = re.search(r"==============================\nMEDIUM\n==============================\n(.*?)(?=\n==============================\nPINTEREST MAIN PIN)", text, re.S)
    if not all((product_id, product_name, amazon_link, medium)):
        raise RuntimeError("PUBLISH BLOCKED: content package is missing required sections")
    section = medium.group(1)
    title = re.search(r"^Title:\s*(.+)$", section, re.M)
    if not title:
        raise RuntimeError("PUBLISH BLOCKED: Medium title is missing")
    # Preserve the generated copy; remove only the package metadata wrapper.
    body = re.sub(r"^Title:\s*.+$", "", section, count=1, flags=re.M).strip()
    return {
        "product_id": product_id.group(1),
        "product_name": product_name.group(1).strip(),
        "amazon_link": amazon_link.group(1).strip(),
        "medium_title": title.group(1).strip(),
        "medium_body": body,
    }


def publish_medium(data: dict) -> dict:
    token = _required("MEDIUM_INTEGRATION_TOKEN")
    user_id = _required("MEDIUM_USER_ID")
    payload = {
        "title": data["medium_title"],
        "contentFormat": "markdown",
        "content": data["medium_body"],
        "publishStatus": os.getenv("MEDIUM_PUBLISH_STATUS", "draft"),
        "tags": ["desk setup", "productivity", "amazon finds"],
    }
    return _request(f"{MEDIUM_API}/users/{user_id}/posts", token, payload)


def publish_pinterest(data: dict) -> dict:
    token = _required("PINTEREST_ACCESS_TOKEN")
    board_id = _required("PINTEREST_BOARD_ID")
    image_url = _required("PINTEREST_IMAGE_URL")
    payload = {
        "board_id": board_id,
        "title": data["medium_title"][:100],
        "description": (
            f"{data['product_name']} — desk setup decision guide. "
            "Check the current Amazon listing before buying. "
            "As an Amazon Associate I earn from qualifying purchases."
        )[:500],
        "link": data["amazon_link"],
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    return _request(f"{PINTEREST_API}/pins", token, payload)


def main() -> None:
    if os.getenv("PUBLISH_ENABLED", "false").lower() != "true":
        print("Publishing disabled: set PUBLISH_ENABLED=true only in an authorized environment.")
        return
    pid = os.getenv("TARGET_PRODUCT_ID", "").strip()
    if not pid:
        raise RuntimeError("PUBLISH BLOCKED: TARGET_PRODUCT_ID is required")
    package = Path("content") / pid / "package.txt"
    if not package.is_file():
        raise RuntimeError(f"PUBLISH BLOCKED: missing package {package}")
    data = parse_package(package)
    results = {}
    if os.getenv("PUBLISH_MEDIUM", "true").lower() == "true":
        results["medium"] = publish_medium(data)
    if os.getenv("PUBLISH_PINTEREST", "true").lower() == "true":
        results["pinterest"] = publish_pinterest(data)
    print(json.dumps({"product_id": pid, "published": list(results)}, indent=2))


if __name__ == "__main__":
    main()
