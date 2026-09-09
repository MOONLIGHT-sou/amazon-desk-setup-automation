import json
import os

APPROVAL_RANK = {"APPROVE": 2, "REVIEW": 1}
CONFIDENCE_RANK = {"unknown": 0, "low": 1, "medium": 2, "high": 3}


def select_candidate(products, report):
    """Select the strongest unused candidate, or the explicitly authorized production target."""
    results = {item["product_id"]: item for item in report.get("results", [])}

    # Production already performs the stronger authorization checks immediately
    # before execution. When it supplies an explicit target, selection must not
    # silently replace that authorized product with a different candidate merely
    # because opportunity evidence is incomplete. The target still has to exist
    # and remain unused here; the production workflow separately verifies review
    # authorization and first-unused ordering.
    target_id = os.getenv("TARGET_PRODUCT_ID", "").strip()
    if target_id:
        target = next((product for product in products if product.get("product_id") == target_id), None)
        if target is None:
            raise RuntimeError(f"SAFETY STOP: explicit production target {target_id} was not found.")
        if target.get("used", "").strip().lower() != "no":
            raise RuntimeError(f"SAFETY STOP: explicit production target {target_id} is already used.")

        result = results.get(target_id, {
            "product_id": target_id,
            "decision": "AUTHORIZED_TARGET",
            "confidence": "unknown",
            "evidence_coverage": 0,
            "opportunity_score": 0,
            "reasons": ["Explicit target supplied by the production workflow after its authorization gates."],
            "next_evidence": [],
        })
        return {"product": target, "selection": result}

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
