import csv
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
        return 0, "unknown", False
    confidence = normalize_confidence(signal.get("confidence"))
    value = signal.get("score")
    if value is None:
        return 0, confidence, False
    value = float(value)
    if not 0 <= value <= 100:
        raise RuntimeError("Signal scores must be between 0 and 100.")
    return value, confidence, True


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
    available_confidences = []

    for name, weight in WEIGHTS.items():
        value, confidence, available = signal_value(product.get(name))
        if available:
            weighted_score += value * weight / 100
            available_weight += weight
            available_confidences.append(confidence)

    opportunity_score = round((weighted_score / available_weight) * 100, 1) if available_weight else 0.0
    evidence_coverage = round((available_weight / sum(WEIGHTS.values())) * 100, 1)

    # Unknown signals do not poison the confidence of evidence that actually exists.
    # Hard-gate unknowns still force HOLD and therefore remain visible in reasons.
    gate_confidences = [
        normalize_confidence(gate.get("confidence"))
        for gate in (identity, niche, facts)
        if normalize_confidence(gate.get("confidence")) != "unknown"
    ]
    confidence_inputs = available_confidences + gate_confidences
    min_confidence = min((CONFIDENCE_RANK[c] for c in confidence_inputs), default=0)
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
    if opportunity_score >= 80 and evidence_coverage >= 60:
        reasons.append("Available evidence scores strongly, but coverage still controls approval.")
    elif opportunity_score >= 65:
        reasons.append("Available evidence is promising but requires review.")
    elif available_weight:
        reasons.append("Available evidence is not yet strong enough.")
    else:
        reasons.append("No scored evidence is available.")

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
    with open(products_path, newline="", encoding="utf-8") as file:
        product_ids = [row["product_id"].strip() for row in csv.DictReader(file)]
    return {"schema_version": 1, "results": [evaluate(product_id, evidence) for product_id in product_ids]}


def main():
    report = build_report()
    output = os.getenv("SELECTION_REPORT", REPORT_FILE)
    with open(output, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
