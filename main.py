import csv
import os
import re
import tempfile

PRODUCTS_FILE = "products.csv"
CONTENT_DIR = "content"
TEST_OUTPUT_DIR = ".test-output"
REQUIRED_COLUMNS = {"product_id", "product_name", "category", "amazon_link", "used"}
MIN_MEDIUM_WORDS = 180
MIN_PIN_DESCRIPTION_WORDS = 25


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


def select_first_unused(products):
    for product in products:
        if product["used"].lower() == "no":
            return product
    return None


def words(text):
    return re.findall(r"\b[\w’'-]+\b", text)


def product_label(product):
    return f"{product['product_name']} for a {product['category'].lower()}"


def build_content(product):
    name = product["product_name"]
    category = product["category"]
    link = product["amazon_link"]
    label = product_label(product)

    medium_title = f"A Practical {name} Upgrade for a Cleaner Desk Setup"
    medium_subtitle = (
        f"How {name} can improve the feel, function, and visual simplicity of a {category.lower()} workspace."
    )

    medium = f"""Title:
{medium_title}

Subtitle:
{medium_subtitle}

Introduction:
A good desk setup does not need dozens of expensive accessories. The better approach is to identify one small friction point and solve it well. {name} is a {category.lower()} upgrade that can help a workspace feel more intentional without turning the desk into a collection of gadgets.

The Problem It Solves:
Desk improvements are most useful when they make an everyday task easier or make the workspace easier to maintain. {name} can be useful when your current setup feels incomplete, visually inconsistent, or less comfortable than it should be. Instead of rebuilding the entire desk, this kind of focused upgrade gives you one clear change to evaluate.

Why It Fits a Minimal Setup:
Minimal does not mean empty. It means each item has a reason to be there. {name} works best when it supports the way you already use the desk and when its size, placement, and appearance fit the rest of the workspace. Keeping the upgrade purposeful helps preserve a clean visual line while still adding useful function.

What To Look For:
Before buying, check the dimensions, compatibility, materials, connection requirements, and return policy listed by the seller. Also consider how often you will actually use the product. A good desk accessory should earn its space. If the product solves a real recurring problem, the value is much easier to judge than if it is being purchased only because it looks good in a setup photo.

Who It May Suit:
This type of upgrade can make sense for students, home-office users, creators, and anyone building a more organized workspace. It is especially worth considering when you want a visible improvement without replacing the whole desk. Your own desk dimensions and workflow should be the final deciding factors.

A Simple Setup Approach:
Start with the existing desk rather than buying more accessories around the product. Place {name} where it supports the task you perform most often. Remove anything it makes redundant, then check the setup from a normal sitting position. The goal is not maximum equipment. The goal is a workspace that feels easier to use every day.

Bottom Line:
{name} is best viewed as a focused desk upgrade rather than a magic solution. If it matches your workspace, solves a genuine problem, and fits your budget, it can be a practical step toward a cleaner and more comfortable setup. Check the current product details before buying because price, availability, and specifications can change.

Amazon:
{link}
"""

    main_pin_description = (
        f"Build a cleaner desk without replacing everything. {name} is a practical {category.lower()} upgrade for a workspace that needs better function and a more intentional look. "
        "Save this idea for your next desk refresh and check the current product details before buying."
    )

    product_pin_description = (
        f"Looking for a focused desk upgrade? {name} can help improve a {category.lower()} workspace without adding unnecessary clutter. "
        "Check the current price, specifications, compatibility, and reviews before deciding if it fits your setup."
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

Amazon:
{link}

==============================
PINTEREST PRODUCT PIN
==============================

Title:
{name} — Focused Desk Setup Upgrade

Description:
{product_pin_description}

Category:
{category}

Amazon:
{link}

==============================
CONTENT QUALITY
==============================

Content is generated from structured product data and passed through deterministic quality checks before it can be written.

==============================
END OF CONTENT PACKAGE
==============================
"""


def section_between(content, start_marker, end_marker):
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start == -1 or end == -1 or end <= start:
        return ""
    return content[start:end]


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
    )

    for required_text in required_content:
        if not required_text or required_text not in content:
            raise RuntimeError(
                f"Content verification failed: missing '{required_text}'."
            )

    if re.search(r"\{[^}]+\}|\[INSERT|TODO|PLACEHOLDER", content, re.IGNORECASE):
        raise RuntimeError("Content verification failed: unresolved placeholder detected.")

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

    for section_name, section in (
        ("MEDIUM", medium),
        ("PINTEREST MAIN PIN", main_pin),
        ("PINTEREST PRODUCT PIN", product_pin),
    ):
        if section.count(product["product_name"]) < 1:
            raise RuntimeError(
                f"Content quality failed: {section_name} does not mention the product."
            )
        if section.count(product["amazon_link"]) < 1:
            raise RuntimeError(
                f"Content quality failed: {section_name} is missing the Amazon link."
            )

    print(
        "Content quality: PASS "
        f"(Medium={medium_words} words, Main Pin={main_pin_words} words, Product Pin={product_pin_words} words)"
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


def main():
    test_mode = os.getenv("TEST_MODE", "false").strip().lower() == "true"
    dry_run = os.getenv("DRY_RUN", "false").strip().lower() == "true"

    products = load_products()
    selected_product = select_first_unused(products)

    if selected_product is None:
        print("No unused products found.")
        return

    product_id = selected_product["product_id"]
    product_name = selected_product["product_name"]

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
        raise RuntimeError("Safety stop: selected product no longer exists.")

    if current_product["used"].lower() != "no":
        raise RuntimeError(
            "Safety stop: selected product is no longer unused. products.csv was not changed."
        )

    for product in current_products:
        if product["product_id"] == product_id:
            product["used"] = "Yes"
            break

    save_products_atomic(current_products)

    print(f"Consumed safely: {product_id} No -> Yes")
    print("Automation completed successfully.")


if __name__ == "__main__":
    main()
