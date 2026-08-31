"""Amazon.in Associates link construction and validation.

This module deliberately works from a verified canonical product URL/ASIN.
It does not resolve short links or guess product identity.
"""

import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

AMAZON_IN_HOSTS = {"amazon.in", "www.amazon.in"}
ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")


def extract_asin(url: str) -> str:
    """Extract a 10-character ASIN from common Amazon.in product URL forms."""
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or parsed.netloc.lower() not in AMAZON_IN_HOSTS:
        raise ValueError("Only verified HTTPS Amazon.in product URLs are accepted.")

    match = re.search(r"/(?:dp|gp/product)/([A-Za-z0-9]{10})(?:/|$)", parsed.path)
    if not match:
        raise ValueError("Amazon.in URL does not contain a recognizable ASIN.")

    asin = match.group(1).upper()
    if not ASIN_PATTERN.fullmatch(asin):
        raise ValueError("Invalid ASIN format.")
    return asin


def build_affiliate_link(canonical_url: str, associate_tag: str) -> str:
    """Build a clean Amazon.in product Special Link from a verified URL."""
    tag = associate_tag.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+-21", tag):
        raise ValueError("Invalid Amazon.in Associate tag format.")

    asin = extract_asin(canonical_url)
    return f"https://www.amazon.in/dp/{asin}?{urlencode({'tag': tag})}"


def validate_affiliate_link(link: str, expected_asin: str, associate_tag: str) -> None:
    """Fail closed unless the link targets the expected Amazon.in ASIN and tag."""
    parsed = urlparse(link.strip())
    if parsed.scheme != "https" or parsed.netloc.lower() not in AMAZON_IN_HOSTS:
        raise ValueError("Affiliate link must target Amazon.in over HTTPS.")

    actual_asin = extract_asin(link)
    if actual_asin != expected_asin.strip().upper():
        raise ValueError("Affiliate link ASIN does not match the verified product identity.")

    query = parse_qs(parsed.query)
    tags = query.get("tag", [])
    if tags != [associate_tag.strip()]:
        raise ValueError("Affiliate link does not contain the expected Associate tag.")

    if set(query) != {"tag"}:
        raise ValueError("Affiliate link contains unexpected query parameters.")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build or validate an Amazon.in Associates link.")
    parser.add_argument("--url", required=True, help="Verified canonical Amazon.in product URL")
    parser.add_argument("--tag", required=True, help="Amazon.in Associate tag")
    parser.add_argument("--expected-asin", help="Validate against this verified ASIN")
    args = parser.parse_args()

    link = build_affiliate_link(args.url, args.tag)
    if args.expected_asin:
        validate_affiliate_link(link, args.expected_asin, args.tag)
    print(link)


if __name__ == "__main__":
    main()
