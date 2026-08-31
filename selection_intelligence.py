import json
import os

EVIDENCE_FILE = "selection_evidence.json"
REPORT_FILE = "selection_report.json"

WEIGHTS = {
    "demand": 20,
    "review_volume": 20,
    "rating_context": 15,
    "review_themes": 15,
    "niche_fit": 10,
    "fact_verifiability": 10,
    "content_potential": 10,
}

CONFIDENCE_RANK = {"unknown": 0, "low": 1, "medium": 2, "high": 3}
HARD_GATES = ("identity", "niche_fit", "fact_verifiability")


def load_evidence(path=EVIDENCE_FILE):
    with open(path, encoding="utf-8") as file:
        data = json.load(file)
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported selection evidence schema version.")
    if not isinstance(data.get("products"), dict):
        raise RuntimeError("Selection evidence must contain a products object.")
    return data["products"]


def normalize_confidence(value):
    value = str(value or "unknown").strip().lower()
    if value not in CONFIDENCE_RANK:
        raise RuntimeError(f"Invalid confidence value: {value!r}")
    return value


def signal_value(signal):
    if not isinstance(signal, dict):
        return 0, "unknown"
    confidence = normalize_confidence(signal.get("confidence"))
    value = signal.get("score")
    if value is None:
        return 0, confidence
    value = float(value)
    if not 0 <= value <= 100:
        raise RuntimeError("Signal scores must be between 0 and 100.")
    return value, confidence


def evaluate(product_id, evidence):
    product = evidence.get(product_id)
    if product is None:
        return {
            "product_id": product_id,
            "decision": "HOLD",
            "confidence": "unknown",
            "evidence_coverage": 0,
            "opportunity_score": 0,
            "reasons": ["No evidence record exists."],
        }

    reasons = []
    identity = product.get("identity", {})
    niche = product.get("niche_fit", {})
    facts = product.get("fact_verifiability", {})

    for gate_name, gate in (("identity", identity), ("niche_fit", niche), ("fact_verifiability", facts)):
        gate_confidence = normalize_confidence(gate.get("confidence"))
        if gate_confidence == "unknown":
            reasons.append(f"Hard gate {gate_name} is unknown.")
        if gate.get("blocked") is True:
            reasons.append(f"Hard gate {gate_name} is blocked.")

    weighted_score = 0.0
    available_weight = 0.0
    confidences = []

    for name, weight in WEIGHTS.items():
        value, confidence = signal_value(product.get(name))
        if product.get(name, {}).get("score") is not None:
            weighted_score += value * weight / 100
            available_weight += weight
        confidences.append(confidence)

    opportunity_score = round((weighted_score / available_weight) * 100, 1) if available_weight else 0.0
    evidence_coverage = round((available_weight / sum(WEIGHTS.values())) * 100, 1)

    min_confidence = min((CONFIDENCE_RANK[c] for c in confidences), default=0)
    overall_confidence = next(name for name, rank in CONFIDENCE_RANK.items() if rank == min_confidence)

    if any("blocked" in reason for reason in reasons):
        decision = "REJECT"
    elif any("unknown" in reason for reason in reasons):
        decision = "HOLD"
    elif opportunity_score >= 80 and evidence_coverage >= 80 and min_confidence >= CONFIDENCE_RANK["medium"]:
        decision = "APPROVE"
    elif opportunity_score >= 65 and evidence_coverage >= 60:
        decision = "REVIEW"
    else:
        decision = "DEFER"

    if evidence_coverage < 60:
        reasons.append("Evidence coverage is below the review threshold.")
    if opportunity_score >= 80:
        reasons.append("Opportunity score is strong.")
    elif opportunity_score >= 65:
        reasons.append("Opportunity score is promising but requires review.")
    else:
        reasons.append("Opportunity score is not yet strong enough.")

    return {
        "product_id": product_id,
        "decision": decision,
        "confidence": overall_confidence,
        "evidence_coverage": evidence_coverage,
        "opportunity_score": opportunity_score,
        "reasons": reasons,
    }


def build_report(products_path="products.csv", evidence_path=EVIDENCE_FILE):
    evidence = load_evidence(evidence_path)
    product_ids = []
    with open(products_path, newline="", encoding="utf-8") as file:
        import csv
        product_ids = [row["product_id"].strip() for row in csv.DictReader(file)]

    results = [evaluate(product_id, evidence) for product_id in product_ids]
    return {"schema_version": 1, "results": results}


def main():
    report = build_report()
    output = os.getenv("SELECTION_REPORT", REPORT_FILE)
    with open(output, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
