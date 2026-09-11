"""Read-only validation for Medium/Pinterest publishing credentials and image source.

All checks are independent so one failed provider does not hide failures in the
other provider. Secrets are never printed.
"""
from __future__ import annotations

import os
import urllib.error
import urllib.parse
import urllib.request


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} is missing")
    return value


def request_json(url: str, token: str) -> int:
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "amazon-desk-setup-automation/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            response.read(2048)
            return response.status
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network error: {exc.reason}") from exc


def check_image(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("PINTEREST_IMAGE_URL must be a public HTTPS URL")
    req = urllib.request.Request(
        url,
        method="HEAD",
        headers={"User-Agent": "amazon-desk-setup-automation/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            if response.status < 200 or response.status >= 400:
                raise RuntimeError(f"image URL returned HTTP {response.status}")
            content_type = response.headers.get("Content-Type", "").lower()
            if not content_type.startswith("image/"):
                raise RuntimeError("PINTEREST_IMAGE_URL does not return an image content type")
    except urllib.error.HTTPError as exc:
        if exc.code != 405:
            raise RuntimeError(f"image URL returned HTTP {exc.code}") from exc
        get_req = urllib.request.Request(
            url,
            method="GET",
            headers={"Range": "bytes=0-1023", "User-Agent": "amazon-desk-setup-automation/1.0"},
        )
        try:
            with urllib.request.urlopen(get_req, timeout=20) as response:
                content_type = response.headers.get("Content-Type", "").lower()
                response.read(1024)
                if not content_type.startswith("image/"):
                    raise RuntimeError("PINTEREST_IMAGE_URL does not return an image content type")
        except urllib.error.HTTPError as get_exc:
            raise RuntimeError(f"image URL returned HTTP {get_exc.code}") from get_exc
        except urllib.error.URLError as get_exc:
            raise RuntimeError(f"image URL network error: {get_exc.reason}") from get_exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"image URL network error: {exc.reason}") from exc


def main() -> None:
    failures: list[str] = []

    # Medium: existing tokens only. Medium's current help page says it no longer
    # issues new integration tokens, while existing tokens continue to work.
    try:
        medium_token = required("MEDIUM_INTEGRATION_TOKEN")
        medium_user_id = required("MEDIUM_USER_ID")
        status = request_json("https://api.medium.com/v1/me", medium_token)
        print(f"Medium credential check: PASS (HTTP {status})")
        print("Medium user ID: PRESENT")
        if not medium_user_id:
            raise RuntimeError("MEDIUM_USER_ID is missing")
    except RuntimeError as exc:
        print(f"Medium credential check: FAIL ({exc})")
        failures.append(f"Medium: {exc}")

    try:
        pinterest_token = required("PINTEREST_ACCESS_TOKEN")
        board_id = required("PINTEREST_BOARD_ID")
        image_url = required("PINTEREST_IMAGE_URL")
        status = request_json("https://api.pinterest.com/v5/pins?page_size=1", pinterest_token)
        print(f"Pinterest token check: PASS (HTTP {status})")
        status = request_json(f"https://api.pinterest.com/v5/boards/{board_id}", pinterest_token)
        print(f"Pinterest board access check: PASS (HTTP {status})")
        check_image(image_url)
        print("Pinterest image URL check: PASS")
    except RuntimeError as exc:
        print(f"Pinterest/image check: FAIL ({exc})")
        failures.append(f"Pinterest/image: {exc}")

    if failures:
        raise SystemExit("\n".join(failures))

    print("Publishing credentials and image source passed read-only validation.")


if __name__ == "__main__":
    main()
