import csv
import os
import sys
import tempfile

PRODUCTS_FILE = "products.csv"
CONTENT_DIR = "content"
TEST_OUTPUT_DIR = ".test-output"
REQUIRED_COLUMNS = {"product_id", "product_name", "category", "amazon_link", "used"}

def load_products(path=PRODUCTS_FILE):
if not os.path.isfile(path):
raise RuntimeError(f"Database not found: {path}")

with open(path, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    if not reader.fieldnames or not REQUIRED_COLUMNS.issubset(reader.fieldnames):
        raise RuntimeError(
            "products.csv is missing one or more required columns."
        )

    products = list(reader)

ids = [product["product_id"].strip() for product in products]

if any(not product_id for product_id in ids):
    raise RuntimeError("Every product must have a product_id.")

if len(ids) != len(set(ids)):
    raise RuntimeError("Product IDs must be unique.")

return products

def select_first_unused(products):
for product in products:
if product["used"].strip().lower() == "no":
return product

return None

def build_content(product):
return f"""PRODUCT CONTENT PACKAGE

Product ID: {product['product_id']}
Product Name: {product['product_name']}
Category: {product['category']}
Amazon Link: {product['amazon_link']}

==============================
MEDIUM

Title:
Amazon Desk Setup Upgrade: {product['product_name']}

Subtitle:
A simple addition for a cleaner, more comfortable workspace.

Product:
{product['product_name']}

Why It Matters:
{product['product_name']} can be a practical addition to a modern desk setup.

Amazon:
{product['amazon_link']}

==============================
PINTEREST MAIN PIN

Title:
Amazon Desk Setup Upgrade

Description:
Upgrade your workspace with practical Amazon desk setup products.

Featured Product:
{product['product_name']}

Amazon:
{product['amazon_link']}

==============================
PINTEREST PRODUCT PIN

Title:
{product['product_name']} — Desk Setup Upgrade

Description:
Give your desk a simple upgrade with {product['product_name']}.

Category:
{product['category']}

Amazon:
{product['amazon_link']}

==============================
END OF CONTENT PACKAGE

"""

def generate_and_verify(product, output_root):
output_dir = os.path.join(output_root, product["product_id"])
os.makedirs(output_dir, exist_ok=True)

content_file = os.path.join(output_dir, "package.txt")

content = build_content(product)

if not content.strip():
    raise RuntimeError("Generated content is empty.")

with open(content_file, "w", encoding="utf-8") as file:
    file.write(content)

if not os.path.isfile(content_file):
    raise RuntimeError(
        "Content verification failed: file does not exist."
    )

if os.path.getsize(content_file) == 0:
    raise RuntimeError(
        "Content verification failed: file is empty."
    )

with open(content_file, "r", encoding="utf-8") as file:
    saved_content = file.read()

required_content = (
    product["product_id"],
    product["product_name"],
    product["amazon_link"],
    "MEDIUM",
    "PINTEREST MAIN PIN",
    "PINTEREST PRODUCT PIN",
)

for required_text in required_content:
    if required_text not in saved_content:
        raise RuntimeError(
            f"Content verification failed: missing '{required_text}'."
        )

return content_file

def save_products_atomic(products, path=PRODUCTS_FILE):
directory = os.path.dirname(path) or "."

file_descriptor, temporary_path = tempfile.mkstemp(
    prefix=".products-",
    suffix=".tmp",
    dir=directory,
)

try:
    with os.fdopen(
        file_descriptor,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=list(products[0].keys()),
        )

        writer.writeheader()
        writer.writerows(products)

        file.flush()
        os.fsync(file.fileno())

    os.replace(temporary_path, path)

finally:
    if os.path.exists(temporary_path):
        os.remove(temporary_path)

def main():
test_mode = (
os.getenv("TEST_MODE", "false").strip().lower() == "true"
)

dry_run = (
    os.getenv("DRY_RUN", "false").strip().lower() == "true"
)

products = load_products()

selected_product = select_first_unused(products)

if selected_product is None:
    print("No unused products found.")
    return

product_id = selected_product["product_id"]
product_name = selected_product["product_name"]

output_root = (
    TEST_OUTPUT_DIR
    if test_mode
    else CONTENT_DIR
)

print("========================================")
print("Stage 2.3B — Safe Content Generation")
print("========================================")
print(f"Mode: {'TEST' if test_mode else 'PRODUCTION'}")
print(f"Dry run: {dry_run}")
print(f"Selected: {product_id} — {product_name}")

content_file = generate_and_verify(
    selected_product,
    output_root,
)

print(f"Content verified: {content_file}")

if test_mode or dry_run:
    print("No production state change made.")
    return

# Re-read immediately before consumption so we do not
# rely on stale product state.
current_products = load_products()

current_product = next(
    (
        product
        for product in current_products
        if product["product_id"] == product_id
    ),
    None,
)

if current_product is None:
    raise RuntimeError(
        "Safety stop: selected product no longer exists."
    )

if current_product["used"].strip().lower() != "no":
    raise RuntimeError(
        "Safety stop: selected product is no longer unused. "
        "products.csv was not changed."
    )

for product in current_products:
    if product["product_id"] == product_id:
        product["used"] = "Yes"
        break

save_products_atomic(current_products)

print(f"Consumed safely: {product_id} No -> Yes")
print("Automation completed successfully.")

if name == "main":
main()