"""Prepare a Medium-ready manual-post package from an approved content package.

This produces Markdown for manual paste into Medium. It deliberately does not
call Medium's API. The generated package preserves the affiliate disclosure and
Amazon link from the approved content package and adds an explicit image checklist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def extract(package: Path) -> tuple[str, str, str]:
    text = package.read_text(encoding="utf-8")
    match = re.search(
        r"==============================\nMEDIUM\n==============================\n(.*?)(?=\n==============================\nPINTEREST MAIN PIN)",
        text,
        re.S,
    )
    if not match:
        raise RuntimeError("MEDIUM section missing")
    section = match.group(1).strip()
    title = re.search(r"^Title:\s*(.+)$", section, re.M)
    subtitle = re.search(r"^Subtitle:\s*(.+)$", section, re.M)
    if not title:
        raise RuntimeError("Medium title missing")
    title_text = title.group(1).strip()
    subtitle_text = subtitle.group(1).strip() if subtitle else ""
    body = re.sub(r"^Title:\s*.+$", "", section, count=1, flags=re.M)
    body = re.sub(r"^Subtitle:\s*.+$", "", body, count=1, flags=re.M).strip()
    return title_text, subtitle_text, body


def main() -> None:
    pid = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    if not re.fullmatch(r"P\d{3}", pid):
        raise SystemExit("Usage: python prepare_medium_manual.py P020")
    package = Path("content") / pid / "package.txt"
    if not package.is_file():
        raise SystemExit(f"Missing approved package: {package}")
    title, subtitle, body = extract(package)
    out_dir = Path("medium-ready") / pid
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "medium-post.md"
    checklist = out_dir / "IMAGE-CHECKLIST.md"
    output.write_text(
        f"# {title}\n\n"
        f"_{subtitle}_\n\n"
        f"{body}\n\n"
        "---\n\n"
        "**Medium image checklist before publishing**\n\n"
        "- Add the approved real product/desk image as the first image.\n"
        "- Set that first image as the featured image.\n"
        "- Use only images you have the right to publish.\n"
        "- Confirm the affiliate disclosure remains visible.\n"
        "- Confirm the Amazon affiliate link is unchanged.\n"
        "- Human-edit and fact-check the article before publishing.\n",
        encoding="utf-8",
    )
    checklist.write_text(
        "# Image checklist\n\n"
        "The automation does not invent or scrape replacement product imagery.\n\n"
        "1. Supply the approved real product image.\n"
        "2. Use it as the first Medium image/featured image.\n"
        "3. Verify you have permission/right to publish the image.\n"
        "4. For Pinterest, make the same approved image available at the public HTTPS URL configured in `PINTEREST_IMAGE_URL`.\n",
        encoding="utf-8",
    )
    print(f"Prepared: {output}")
    print(f"Image checklist: {checklist}")


if __name__ == "__main__":
    main()
