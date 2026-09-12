"""Credential-safe Pinterest publishing adapter.

Medium is intentionally excluded from automatic API publishing. Medium's current
API terms prohibit automatically generated content, and Medium no longer issues
new integration tokens. Medium output is prepared for manual posting instead.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

PINTEREST_API = "https://api.pinterest.com/v5"


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"PUBLISH BLOCKED: required secret/config {name} is missing")
    return value


def _request_json(url: str, token: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
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
    pinterest = re.search(
        r"==============================\nPINTEREST MAIN PIN\n==============================\n(.*?)(?=\n==============================\nPINTEREST PRODUCT PIN)",
        text,
        re.S,
    )
    if not all((product_id, product_name, amazon_link, pinterest)):
        raise RuntimeError("PUBLISH BLOCKED: content package is missing required sections")
    section = pinterest.group(1)
    title = re.search(r"^Title:\s*(.+)$", section, re.M)
    description = re.search(r"^Description:\s*(.+)$", section, re.M)
    if not title or not description:
        raise RuntimeError("PUBLISH BLOCKED: Pinterest title/description is missing")
    return {
        "product_id": product_id.group(1),
        "product_name": product_name.group(1).strip(),
        "amazon_link": amazon_link.group(1).strip(),
        "pinterest_title": title.group(1).strip(),
        "pinterest_description": description.group(1).strip(),
    }


def _image_url_is_valid(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("PINTEREST_IMAGE_URL must be a public HTTPS URL")


def _already_pinned(board_id: str, token: str, amazon_link: str) -> bool:
    """Fail closed on an existing matching link to prevent duplicate Pins."""
    url = f"{PINTEREST_API}/boards/{urllib.parse.quote(board_id, safe='')}/pins?page_size=100"
    checked = 0
    while url and checked < 500:
        data = _request_json(url, token)
        for item in data.get("items", []):
            if item.get("link") == amazon_link:
                return True
            checked += 1
            if checked >= 500:
                break
        bookmark = data.get("bookmark")
        if not bookmark or checked >= 500:
            break
        url = f"{PINTEREST_API}/boards/{urllib.parse.quote(board_id, safe='')}/pins?page_size=100&bookmark={urllib.parse.quote(bookmark, safe='')}"
    return False


def publish_pinterest(data: dict) -> dict:
    token = _required("PINTEREST_ACCESS_TOKEN")
    board_id = _required("PINTEREST_BOARD_ID")
    image_url = _required("PINTEREST_IMAGE_URL")
    _image_url_is_valid(image_url)
    if _already_pinned(board_id, token, data["amazon_link"]):
        raise RuntimeError(
            f"PUBLISH BLOCKED: a Pinterest Pin with the same Amazon link already exists on board {board_id}"
        )
    payload = {
        "board_id": board_id,
        "title": data["pinterest_title"][:100],
        "description": data["pinterest_description"][:500],
        "link": data["amazon_link"],
        "media_source": {"source_type": "image_url", "url": image_url},
    }
    return _request_json(f"{PINTEREST_API}/pins", token, method="POST", payload=payload)


def main() -> None:
    if os.getenv("PUBLISH_ENABLED", "false").lower() != "true":
        print("Publishing disabled: set PUBLISH_ENABLED=true only in an authorized environment.")
        return
    if os.getenv("PUBLISH_MEDIUM", "false").lower() == "true":
        raise RuntimeError(
            "PUBLISH BLOCKED: Medium automatic API publishing is disabled. "
            "Use the generated Medium manual-post package instead."
        )
    pid = os.getenv("TARGET_PRODUCT_ID", "").strip()
    if not pid:
        raise RuntimeError("PUBLISH BLOCKED: TARGET_PRODUCT_ID is required")
    package = Path("content") / pid / "package.txt"
    if not package.is_file():
        raise RuntimeError(f"PUBLISH BLOCKED: missing package {package}")
    data = parse_package(package)
    if os.getenv("PUBLISH_PINTEREST", "true").lower() != "true":
        print(json.dumps({"product_id": pid, "published": []}, indent=2))
        return
    result = publish_pinterest(data)
    print(json.dumps({"product_id": pid, "published": ["pinterest"], "pinterest_id": result.get("id")}, indent=2))


if __name__ == "__main__":
    main()
