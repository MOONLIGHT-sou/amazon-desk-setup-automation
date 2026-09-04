import csv
import json
import os
import re
import tempfile

from affiliate_link import validate_affiliate_link
from candidate_selector import select_candidate
from selection_intelligence import build_report

PRODUCTS_FILE = "products.csv"
CONTENT_DIR = "content"
TEST_OUTPUT_DIR = ".test-output"
REVIEW_STATE_FILE = "review_state.json"
SELECTION_EVIDENCE_FILE = "selection_evidence.json"
PRODUCT_FACTS_FILE = "product_facts.json"
AMAZON_ASSOCIATE_TAG = "moonlight0adc-21"

REQUIRED_COLUMNS = {"product_id", "product_name", "category", "amazon_link", "used"}
MIN_MEDIUM_WORDS = 320
MIN_PIN_DESCRIPTION_WORDS = 30
REQUIRED_DISCLOSURE = "As an Amazon Associate I earn from qualifying purchases."
LINK_DISCLOSURE = "(paid link)"

BANNED_CLAIMS = (
    r"\bperfect\b",
    r"\bnumber one\b",
    r"\beliminate(s|d)?\b",
    r"\bcure(s|d)?\b",
    r"\bprevent(s|ed)?\b",
    r"\bboost(s|ed) productivity\b",
    r"\bimprove(s|d) eyesight\b",
    r"\bprotect(s|ed) your eyes\b",
    r"\bhealth benefit(s)?\b",
)

FABRICATED_EXPERIENCE = (
    r"\bi (?:tested|used|tried|bought|owned|reviewed)\b",
    r"\bmy (?:experience|setup|unit|monitor light bar)\b",
    r"\bi (?:recommend|love|like|hate)\b",
)

PLACEHOLDER_PATTERN = r"\{[^}]+\}|\[INSERT|TODO|PLACEHOLDER"

PRODUCT_PROFILES = {
    "monitor_light": {
        "keywords": ("monitor", "light", "bar"),
        "angle": "lighting around the monitor while keeping the desktop visually calm",
        "fit": (
            "A monitor light bar is worth evaluating as a task-lighting option around the display, "
            "not as a replacement for every other light in the room."
        ),
        "sections": (
            "screen reflections and light direction",
            "monitor clearance and mounting compatibility",
            "USB or other power requirements",
            "brightness and control options listed by the seller",
            "whether the light placement leaves the desk surface clear",
        ),
        "tradeoffs": (
            "Check the monitor's top edge, thickness, curvature, camera position, and available clearance before buying. "
            "Also check how the seller describes light direction and controls; do not assume every model behaves the same way."
        ),
    },
    "keyboard": {
        "keywords": ("keyboard",),
        "angle": "typing comfort, desk appearance, and the amount of control you want at your fingertips",
        "fit": (
            "A keyboard should be judged against the way you actually type, the space available on the desk, "
            "and the connection or layout you prefer."
        ),
        "sections": (
            "layout and available desk width",
            "switch or key feel described by the seller",
            "wired or wireless connection requirements",
            "noise level expectations",
            "compatibility with your devices",
        ),
        "tradeoffs": (
            "A more feature-heavy keyboard can add flexibility but can also add cost, noise, or desk clutter. "
            "Use the listing's specifications rather than assuming a particular switch, battery, or connectivity feature."
        ),
    },
    "desk_mat": {
        "keywords": ("mat",),
        "angle": "a cleaner working surface and a more consistent visual base for the rest of the desk",
        "fit": (
            "A desk mat is mainly a surface decision: size, material, edge treatment, cleaning needs, and how it fits "
            "around the keyboard, mouse, and other items matter more than appearance alone."
        ),
        "sections": (
            "desk dimensions and available coverage",
            "surface material and cleaning instructions",
            "edge construction and thickness",
            "mouse and keyboard placement",
            "whether the size leaves useful desk space around it",
        ),
        "tradeoffs": (
            "A larger mat can visually unify a setup but uses more surface area and may be harder to clean or reposition. "
            "Choose from the actual dimensions rather than judging scale from a product photo."
        ),
    },
    "desk_shelf": {
        "keywords": ("shelf",),
        "angle": "using vertical space without turning the desktop into a storage pile",
        "fit": (
            "A desk shelf earns its space when it gives frequently used items a deliberate home while keeping the main work area usable."
        ),
        "sections": (
            "available desk width and depth",
            "shelf height relative to the monitor",
            "weight or load information supplied by the seller",
            "access to items stored underneath",
            "whether the shelf creates useful space rather than another layer of clutter",
        ),
        "tradeoffs": (
            "A shelf can free visual and working space, but it also adds height and another surface to maintain. "
            "Check the listed dimensions and load information instead of assuming it will fit every monitor or desk."
        ),
    },
    "clock": {
        "keywords": ("clock",),
        "angle": "adding a useful time reference without sacrificing the minimal look of the workspace",
        "fit": (
            "A desk clock is most useful when its display is easy to read from your normal working position and its placement does not compete with the main task area."
        ),
        "sections": (
            "display visibility from your normal sitting position",
            "size and placement on the desk",
            "brightness or display controls listed by the seller",
            "power requirements",
            "whether the clock adds useful information without adding visual noise",
        ),
        "tradeoffs": (
            "A larger or brighter display may be easier to read but can become a stronger visual element on a minimal desk. "
            "Use the seller's specifications to decide whether the display fits your space."
        ),
    },
    "cooling_pad": {
        "keywords": ("cooling", "pad"),
        "angle": "adding a laptop cooling accessory while keeping the desk footprint and cable setup under control",
        "fit": (
            "A laptop cooling pad is worth evaluating when you want a dedicated platform for the laptop and the listed design fits your machine and workspace. "
            "The decision should be based on the seller's specifications and your actual desk layout, not on a promise of guaranteed temperature or performance improvement."
        ),
        "sections": (
            "listed dimensions and available desk space",
            "laptop size and compatibility information supplied by the seller",
            "USB power and port requirements",
            "fan and stand features stated by the seller",
            "whether the stand position and cable routing fit the desk",
        ),
        "tradeoffs": (
            "A cooling pad adds another device, cable, and occupied surface area to the desk. "
            "Check the listing's dimensions, compatibility, power requirements, and stated features before buying, and do not assume a specific temperature reduction or gaming-performance gain."
        ),
    },
}


def load_products(path=PRODUCTS_FILE):
    if not os.path.isfile(path):
        raise RuntimeError(f"Database not found: {path}")

    with open(path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
            raise RuntimeError("products.csv is missing one or more required columns.")

        products = list(reader)

    ids = [product["product_id"].strip() for product in products]

    if any(not product_id for product_id in ids):
        raise RuntimeError("Every product must have a product_id.")

    if len(ids) != len(set(ids)):
        raise RuntimeError("Product IDs must be unique.")

    for product in products:
        for field in ("product_id", "product_name", "category", "amazon_link", "used"):
            product[field] = product[field].strip()

        if product["used"].lower() not in {"yes", "no"}:
            raise RuntimeError(
                f"Invalid used value for {product['product_id']}: {product['used']!r}"
            )

        if not re.fullmatch(r"https?://[^\s]+", product["amazon_link"]):
            raise RuntimeError(
                f"Invalid Amazon link for {product['product_id']}: {product['amazon_link']!r}"
            )

    return products


def load_product_facts(product_id):
    try:
        with open(PRODUCT_FACTS_FILE, encoding="utf-8") as file:
            facts = json.load(file)["facts"][product_id]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Content safety failed: verified product facts are unavailable for {product_id}: {exc}"
        ) from exc

    safe_facts = facts.get("safe_facts")
    if not isinstance(safe_facts, list) or not all(isinstance(item, str) and item.strip() for item in safe_facts):
        raise RuntimeError(
            f"Content safety failed: safe_facts are missing or invalid for {product_id}."
        )

    return facts


def select_for_run(products, test_mode):
    report = build_report()
    selection = select_candidate(products, report)

    if selection is None:
        print("Selection intelligence: no eligible unused candidate; safe stop.")
        return None, report

    selected = selection["product"]
    result = selection["selection"]
    print(
        "Selection intelligence: selected "
        f"{selected['product_id']} — {selected['product_name']} "
        f"(decision={result['decision']}, score={result['opportunity_score']}, "
        f"coverage={result['evidence_coverage']}, confidence={result['confidence']})"
    )
    return selected, report


def load_review_authorization(product_id):
    try:
        with open(REVIEW_STATE_FILE, encoding="utf-8") as file:
            state = json.load(file)
        review = state["products"][product_id]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"SAFETY STOP: review authorization is unavailable or invalid: {exc}") from exc

    if review.get("status") != "APPROVED":
        raise RuntimeError(
            "SAFETY STOP: human review has not approved this product. "
            f"status={review.get('status')!r}"
        )
    if review.get("approved_for_production") is not True:
        raise RuntimeError("SAFETY STOP: approved_for_production is not true.")
    if review.get("draft_qc") != "PASSED":
        raise RuntimeError("SAFETY STOP: draft QC is not PASSED.")

    return review


def load_verified_asin(product_id):
    try:
        with open(SELECTION_EVIDENCE_FILE, encoding="utf-8") as file:
            evidence = json.load(file)
        asin = evidence["products"][product_id]["identity"]["asin"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"SAFETY STOP: verified ASIN evidence is unavailable: {exc}") from exc

    if not re.fullmatch(r"[A-Z0-9]{10}", str(asin).upper()):
        raise RuntimeError(f"SAFETY STOP: invalid verified ASIN for {product_id}.")
    return str(asin).upper()


def words(text):
    return re.findall(r"\b[\w’'-]+\b", text)


def infer_profile(product):
    normalized = re.sub(r"[^a-z0-9]+", " ", product["product_name"].lower()).split()

    for profile_name, profile in PRODUCT_PROFILES.items():
        if all(keyword in normalized for keyword in profile["keywords"]):
            return profile_name, profile

    raise RuntimeError(
        f"Content quality failed: no approved product profile exists for "
        f"{product['product_id']} ({product['product_name']}). "
        "Add a reviewed profile before generating production content."
    )


def product_label(product):
    return f"{product['product_name']} for a {product['category'].lower()}"


def build_content(product):
    name = product["product_name"]
    category = product["category"]
    link = product["amazon_link"]
    facts = load_product_facts(product["product_id"])
    variant = facts.get("variant", "").strip()
    safe_facts = facts["safe_facts"]
    profile_name, profile = infer_profile(product)
    label = product_label(product)

    checklist = "\n".join(f"- {item.capitalize()}." for item in profile["sections"])
    verified_facts = "\n".join(f"- {item}." for item in safe_facts)
    variant_line = f"Verified variant: {variant}\n" if variant else ""

    medium_title = f"How to Decide If a {name} Upgrade Earns a Place on Your Desk"
    medium_subtitle = (
        f"A practical {category.lower()} decision guide focused on fit, tradeoffs, and everyday use."
    )

    medium = f"""Title:
{medium_title}

Subtitle:
{medium_subtitle}

Affiliate disclosure:
This post contains affiliate links. If you buy through a qualifying link, I may earn a commission at no additional cost to you. {REQUIRED_DISCLOSURE}

Introduction:
A minimal desk is easier to maintain when every item has a clear job. That does not mean buying the fewest products possible. It means choosing upgrades that solve a recurring problem without creating a new one. {name} is a {category.lower()} option worth evaluating when the way you use your workspace suggests that this particular type of upgrade could earn its space.

The useful question is not whether {name} looks good in a desk photo. The useful question is whether it fits your desk, your routine, and the amount of complexity you are willing to maintain. This guide is deliberately written as a decision guide rather than a product review because the current price, specifications, compatibility, and availability should be checked on the seller's listing before purchase.

Verified Product Facts:
{variant_line}{verified_facts}

Why This Type of Upgrade Can Make Sense:
{profile["fit"]} The clearest reason to consider {name} is a specific recurring need. If there is no clear need, adding another accessory can make a minimal setup harder to manage rather than better.

What To Check Before Buying:
Use the product listing as the source of truth for specifications. For {label}, pay particular attention to:
{checklist}

The right checklist depends on the product. For this {profile_name.replace("_", " ")} profile, those details matter because a visually attractive accessory can still be a poor fit if it conflicts with the physical layout or workflow of the desk.

Tradeoffs To Consider:
{profile["tradeoffs"]} There is no single setup that is correct for everyone. A good decision balances the problem you want to solve against cost, space, compatibility, maintenance, and how often the product will actually be useful.

A Simple Desk-Fit Test:
Before buying, measure the relevant part of your desk and compare those measurements with the seller's listed dimensions. Then imagine the product in the position where you would use it most often. Ask three questions: What problem does it solve? What space will it occupy? What existing item, if any, becomes unnecessary?

If the answers are clear, the upgrade has a stronger case. If the answers are vague, waiting is often better than buying another accessory simply because it looks good in a setup photo.

Who This May Suit:
This kind of {category.lower()} upgrade can be relevant to students, home-office users, creators, and people who want a cleaner working environment. The important variable is not the label of the user; it is whether the product matches the person's actual desk dimensions and routine.

What It Will Not Do:
{name} should not be treated as a universal solution to every desk or comfort problem. It cannot replace good workspace planning, and no product listing can tell you exactly how an accessory will feel in your own setup. Avoid buying based on promises that go beyond the specifications and use case described by the seller.

Bottom Line:
{name} is worth considering when it solves a real, recurring problem and its specifications fit your workspace. Check the current listing for price, availability, compatibility, dimensions, and other product details before making a decision. If those details do not match your desk, the right move is to skip the purchase rather than force the setup around the accessory.

{LINK_DISCLOSURE} Amazon product link:
{link}

{REQUIRED_DISCLOSURE}
Editorial status: This package is generated from structured product data and requires human review before publication.
"""

    main_pin_description = (
        f"Planning a cleaner {category.lower()}? Use this {name} buying checklist to compare fit, space, compatibility, "
        f"and everyday usefulness before adding another accessory. {LINK_DISCLOSURE} "
        f"Check the current listing before buying. {REQUIRED_DISCLOSURE}"
    )

    product_pin_description = (
        f"{name} is a focused {category.lower()} option to evaluate when it solves a real desk problem. "
        f"Check the seller's current specifications, dimensions, compatibility, price, and reviews before deciding. "
        f"{LINK_DISCLOSURE} {REQUIRED_DISCLOSURE}"
    )

    return f"""PRODUCT CONTENT PACKAGE

Product ID: {product['product_id']}
Product Name: {name}
Category: {category}
Amazon Link: {link}

==============================
MEDIUM
==============================

{medium}

==============================
PINTEREST MAIN PIN
==============================

Title:
{medium_title}

Description:
{main_pin_description}

Featured Product:
{name}

{LINK_DISCLOSURE} Amazon:
{link}

{REQUIRED_DISCLOSURE}

==============================
PINTEREST PRODUCT PIN
==============================

Title:
{name} — Focused Desk Setup Decision Guide

Description:
{product_pin_description}

Category:
{category}

{LINK_DISCLOSURE} Amazon:
{link}

{REQUIRED_DISCLOSURE}

==============================
CONTENT QUALITY
==============================

Content is generated from structured product data and must pass deterministic compliance, specificity, claim-safety, and completeness checks before production output is allowed.
Profile: {profile_name}
Affiliate disclosure: PRESENT
Human review before publication: REQUIRED

==============================
END OF CONTENT PACKAGE
==============================
"""


def section_between(content, start_marker, end_marker):
    start = content.find(start_marker)
    end = content.find(end_marker, start + len(start_marker))
    if start == -1 or end == -1 or end <= start:
        return ""
    return content[start:end]


def assert_no_pattern(text, patterns, message):
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            raise RuntimeError(message)


def verify_link_disclosure(section, link):
    link_index = section.find(link)
    if link_index == -1:
        raise RuntimeError("Content quality failed: expected affiliate link is missing.")

    nearby = section[max(0, link_index - 140): link_index + len(link) + 20]
    if LINK_DISCLOSURE.lower() not in nearby.lower():
        raise RuntimeError(
            "Content compliance failed: affiliate link does not have a nearby paid-link disclosure."
        )


def verify_content(content, product):
    if not content.strip():
        raise RuntimeError("Generated content is empty.")

    required_content = (
        product["product_id"],
        product["product_name"],
        product["category"],
        product["amazon_link"],
        "MEDIUM",
        "PINTEREST MAIN PIN",
        "PINTEREST PRODUCT PIN",
        "CONTENT QUALITY",
        REQUIRED_DISCLOSURE,
        LINK_DISCLOSURE,
        "Editorial status: This package is generated from structured product data and requires human review before publication.",
    )

    for required_text in required_content:
        if not required_text or required_text not in content:
            raise RuntimeError(
                f"Content verification failed: missing '{required_text}'."
            )

    facts = load_product_facts(product["product_id"])
    variant = facts.get("variant", "").strip()
    if variant and variant not in content:
        raise RuntimeError(
            f"Content verification failed: verified product variant '{variant}' is missing."
        )
    for safe_fact in facts["safe_facts"]:
        if safe_fact not in content:
            raise RuntimeError(
                f"Content verification failed: verified safe fact '{safe_fact}' is missing."
            )

    assert_no_pattern(
        content,
        (PLACEHOLDER_PATTERN,),
        "Content verification failed: unresolved placeholder detected.",
    )

    assert_no_pattern(
        content,
        BANNED_CLAIMS,
        "Content safety failed: unsupported or high-risk claim detected.",
    )

    assert_no_pattern(
        content,
        FABRICATED_EXPERIENCE,
        "Content integrity failed: fabricated personal experience detected.",
    )

    medium = section_between(content, "MEDIUM", "PINTEREST MAIN PIN")
    main_pin = section_between(content, "PINTEREST MAIN PIN", "PINTEREST PRODUCT PIN")
    product_pin = section_between(content, "PINTEREST PRODUCT PIN", "CONTENT QUALITY")

    medium_words = len(words(medium))
    main_pin_words = len(words(main_pin))
    product_pin_words = len(words(product_pin))

    if medium_words < MIN_MEDIUM_WORDS:
        raise RuntimeError(
            f"Content quality failed: MEDIUM section has {medium_words} words; minimum is {MIN_MEDIUM_WORDS}."
        )

    if main_pin_words < MIN_PIN_DESCRIPTION_WORDS:
        raise RuntimeError("Content quality failed: Pinterest Main Pin is too short.")

    if product_pin_words < MIN_PIN_DESCRIPTION_WORDS:
        raise RuntimeError("Content quality failed: Pinterest Product Pin is too short.")

    profile_name, profile = infer_profile(product)

    for section_name, section in (
        ("MEDIUM", medium),
        ("PINTEREST MAIN PIN", main_pin),
        ("PINTEREST PRODUCT PIN", product_pin),
    ):
        if section.count(product["product_name"]) < 1:
            raise RuntimeError(
                f"Content quality failed: {section_name} does not mention the product."
            )

    for phrase in profile["sections"][:3]:
        if phrase.lower() not in medium.lower():
            raise RuntimeError(
                f"Content specificity failed: MEDIUM is missing approved product-specific consideration '{phrase}'."
            )

    if "Tradeoffs To Consider:" not in medium:
        raise RuntimeError("Content quality failed: tradeoff section is missing.")

    if "What It Will Not Do:" not in medium:
        raise RuntimeError("Content quality failed: limitation section is missing.")

    verify_link_disclosure(medium, product["amazon_link"])
    verify_link_disclosure(main_pin, product["amazon_link"])
    verify_link_disclosure(product_pin, product["amazon_link"])

    disclosure_count = content.count(REQUIRED_DISCLOSURE)
    if disclosure_count < 4:
        raise RuntimeError(
            "Content compliance failed: required Amazon Associate statement is not repeated in all package surfaces."
        )

    if content.count(product["amazon_link"]) < 4:
        raise RuntimeError("Content quality failed: expected product link placements are incomplete.")

    print(
        "Content quality: PASS "
        f"(Medium={medium_words} words, Main Pin={main_pin_words} words, Product Pin={product_pin_words}, "
        f"profile={profile_name}, disclosures={disclosure_count})"
    )


def generate_and_verify(product, output_root, write_output=True):
    content = build_content(product)
    verify_content(content, product)

    if not write_output:
        print("Dry run: content verified in memory; no production file written.")
        return None

    output_dir = os.path.join(output_root, product["product_id"])
    os.makedirs(output_dir, exist_ok=True)
    content_file = os.path.join(output_dir, "package.txt")

    if os.path.exists(content_file):
        raise RuntimeError(
            f"SAFETY STOP: production content already exists for {product['product_id']}; refusing to overwrite it."
        )

    with open(content_file, "w", encoding="utf-8") as file:
        file.write(content)

    if not os.path.isfile(content_file):
        raise RuntimeError("Content verification failed: file does not exist.")

    if os.path.getsize(content_file) == 0:
        raise RuntimeError("Content verification failed: file is empty.")

    with open(content_file, "r", encoding="utf-8") as file:
        saved_content = file.read()

    verify_content(saved_content, product)
    return content_file


def save_products_atomic(products, path=PRODUCTS_FILE):
    directory = os.path.dirname(path) or "."
    file_descriptor, temporary_path = tempfile.mkstemp(
        prefix=".products-",
        suffix=".tmp",
        dir=directory,
    )

    try:
        with os.fdopen(file_descriptor, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(products[0].keys()))
            writer.writeheader()
            writer.writerows(products)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, path)

    finally:
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def mark_product_used(products, product_id):
    matches = [product for product in products if product["product_id"] == product_id]
    if len(matches) != 1:
        raise RuntimeError(f"SAFETY STOP: expected exactly one target product, found {len(matches)}.")

    target = matches[0]
    if target["used"].lower() != "no":
        raise RuntimeError(
            f"SAFETY STOP: target {product_id} is no longer unused ({target['used']!r})."
        )
    target["used"] = "Yes"


def main():
    test_mode = os.getenv("TEST_MODE", "false").strip().lower() == "true"
    dry_run = os.getenv("DRY_RUN", "false").strip().lower() == "true"
    target_product_id = os.getenv("TARGET_PRODUCT_ID", "").strip()

    products = load_products()
    selected_product, selection_report = select_for_run(products, test_mode)

    if selected_product is None:
        print("No eligible candidate selected. Safe stop.")
        return

    product_id = selected_product["product_id"]
    product_name = selected_product["product_name"]

    if not test_mode and not target_product_id:
        raise RuntimeError("SAFETY STOP: TARGET_PRODUCT_ID is required for production execution.")

    if not test_mode and product_id != target_product_id:
        raise RuntimeError(
            "SAFETY STOP: intelligent selector target does not match the explicitly authorized production target. "
            f"selected={product_id}, authorized={target_product_id}"
        )

    if not test_mode:
        load_review_authorization(product_id)

        expected_asin = load_verified_asin(product_id)
        try:
            validate_affiliate_link(
                selected_product["amazon_link"],
                expected_asin,
                AMAZON_ASSOCIATE_TAG,
            )
        except ValueError as exc:
            raise RuntimeError(
                f"SAFETY STOP: affiliate link validation failed for {product_id}: {exc}"
            ) from exc
        print(f"Affiliate link validation: PASS ({product_id}, ASIN={expected_asin})")

        if selected_product["used"].lower() != "no":
            raise RuntimeError(f"SAFETY STOP: production target {product_id} is not unused.")

    output_root = TEST_OUTPUT_DIR if test_mode else CONTENT_DIR
    write_output = test_mode or not dry_run

    print("========================================")
    print("Stage 2 — Quality-Controlled Content Generation")
    print("========================================")
    print(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}")
    print(f"Dry run: {dry_run}")
    print(f"Selected: {product_id} — {product_name}")

    content_file = generate_and_verify(
        selected_product,
        output_root,
        write_output=write_output,
    )

    if content_file:
        print(f"Content verified: {content_file}")

    if test_mode or dry_run:
        print("No production state change made.")
        return

    current_products = load_products()
    current_product = next(
        (product for product in current_products if product["product_id"] == product_id),
        None,
    )
    if current_product is None:
        raise RuntimeError(f"SAFETY STOP: target {product_id} disappeared before mutation.")
    if current_product["used"].lower() != "no":
        raise RuntimeError(
            f"SAFETY STOP: target {product_id} changed before mutation ({current_product['used']!r})."
        )
    if current_product["amazon_link"] != selected_product["amazon_link"]:
        raise RuntimeError("SAFETY STOP: target Amazon link changed during production execution.")

    # Re-check authorization immediately before the only database mutation.
    load_review_authorization(product_id)
    mark_product_used(current_products, product_id)
    save_products_atomic(current_products)
    print(f"Production state mutation: PASS ({product_id} No -> Yes)")


if __name__ == "__main__":
    main()
