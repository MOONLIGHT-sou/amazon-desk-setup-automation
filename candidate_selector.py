import json

APPROVAL_RANK = {"APPROVE": 2, "REVIEW": 1}
CONFIDENCE_RANK = {"unknown": 0, "low": 1, "medium": 2, "high": 3}


def select_candidate(products, report):
    """Select the strongest unused candidate without ever promoting HOLD/DEFER/REJECT."""
    results = {item["product_id"]: item for item in report.get("results", [])}
    eligible = []

    for product in products:
        if product.get("used", "").strip().lower() != "no":
            continue

        result = results.get(product["product_id"])
        if not result or result.get("decision") not in APPROVAL_RANK:
            continue

        eligible.append((
            APPROVAL_RANK[result["decision"]],
            result.get("opportunity_score", 0),
            result.get("evidence_coverage", 0),
            CONFIDENCE_RANK.get(result.get("confidence", "unknown"), 0),
            product["product_id"],
            product,
            result,
        ))

    if not eligible:
        return None

    eligible.sort(key=lambda item: (-item[0], -item[1], -item[2], -item[3], item[4]))
    _, _, _, _, _, product, result = eligible[0]
    return {"product": product, "selection": result}


def load_report(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)
