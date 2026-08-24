# main.py

import csv
import os
import sys

PRODUCTS_FILE = "products.csv"
CONTENT_DIR = "content"

def find_first_unused_product():
"""Find the first product whose used status is 
```
with open(PRODUCTS_FILE, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    products = list(reader)

for product in products:
    if product["used"].strip().lower() == "no":
        return products, product

return products, None
```

def generate_content(product):
"""Generate the content package for the selected product."""

```
product_id = product["product_id"]
product_name = product["product_name"]
category = product["category"]
amazon_link = product["amazon_link"]

os.makedirs(CONTENT_DIR, exist_ok=True)

content_file = os.path.join(
    CONTENT_DIR,
    f"{product_id}.txt"
)

content = f"""PRODUCT CONTENT PACKAGE
```

Product ID: {product_id}
Product Name: {product_name}
Category: {category}
Amazon Link: {amazon_link}

==============================
MEDIUM
======

Title:
5 Amazon Desk Setup Products That Instantly Upgrade Your Workspace

Subtitle:
A simple desk upgrade can make your workspace feel cleaner, more comfortable, and more inspiring.

Product:
{product_name}

Why It Matters:
A good desk setup is not only about appearance. The right products can make your workspace feel more organized, comfortable, and enjoyable to use.

{product_name} can be a useful addition to a modern desk setup, especially for people who want to improve their workspace without completely redesigning it.

Amazon:
{amazon_link}

==============================
PINTEREST MAIN PIN
==================

Title:
Amazon Desk Setup Upgrade

Description:
Upgrade your workspace with simple Amazon desk setup products designed to make your desk cleaner, more comfortable, and more aesthetic.

Featured Product:
{product_name}

Amazon:
{amazon_link}

==============================
PINTEREST PRODUCT PIN
=====================

Title:
{product_name} — Desk Setup Upgrade

Description:
Give your desk a simple upgrade with {product_name}. A practical addition for anyone building a cleaner, more productive, and aesthetic workspace.

Category:
{category}

Amazon:
{amazon_link}

==============================
END OF CONTENT PACKAGE
======================

"""

```
with open(content_file, "w", encoding="utf-8") as file:
    file.write(content)

return content_file
```

def verify_content_file(content_file, product):
"""
Verify that the generated content file exists,
is not empty, and contains the expected product data.
"""

```
product_id = product["product_id"]
product_name = product["product_name"]

print("")
print("VERIFYING GENERATED CONTENT...")
print(f"Expected file: {content_file}")

# Check 1: File exists
if not os.path.isfile(content_file):
    raise RuntimeError(
        f"CONTENT VERIFICATION FAILED: "
        f"{content_file} does not exist."
    )

print("✓ File exists")

# Check 2: File is not empty
file_size = os.path.getsize(content_file)

if file_size == 0:
    raise RuntimeError(
        f"CONTENT VERIFICATION FAILED: "
        f"{content_file} is empty."
    )

print(f"✓ File is not empty ({file_size} bytes)")

# Check 3: Read the generated file
with open(content_file, "r", encoding="utf-8") as file:
    generated_content = file.read()

# Check 4: Product ID exists
if product_id not in generated_content:
    raise RuntimeError(
        f"CONTENT VERIFICATION FAILED: "
        f"Product ID {product_id} was not found in generated content."
    )

print(f"✓ Product ID found: {product_id}")

# Check 5: Product name exists
if product_name not in generated_content:
    raise RuntimeError(
        f"CONTENT VERIFICATION FAILED: "
        f"Product name '{product_name}' was not found in generated content."
    )

print(f"✓ Product name found: {product_name}")

print("✓ CONTENT VERIFICATION PASSED")

return True
```

def mark_product_as_used(products, selected_product):
"""Mark the successfully processed product as used."""

```
product_id = selected_product["product_id"]

for product in products:
    if product["product_id"] == product_id:
        product["used"] = "Yes"
        break
```

def save_products(products):
"""Save the updated products.csv."""

```
fieldnames = [
    "product_id",
    "product_name",
    "category",
    "amazon_link",
    "used"
]

with open(
    PRODUCTS_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(products)
```

def main():
print("========================================")
print("Amazon Desk Setup Automation")
print("Stage 2.3B — Safe Content Generation")
print("========================================")

```
# ----------------------------------------
# STEP 1 — Find first unused product
# ----------------------------------------

products, selected_product = find_first_unused_product()

if selected_product is None:
    print("")
    print("No unused products found.")
    sys.exit(0)

product_id = selected_product["product_id"]
product_name = selected_product["product_name"]

print("")
print("SELECTED PRODUCT")
print(f"Product ID: {product_id}")
print(f"Product Name: {product_name}")

# ----------------------------------------
# STEP 2 — Generate content
# ----------------------------------------

print("")
print("GENERATING CONTENT...")

content_file = generate_content(selected_product)

print(f"Content generated: {content_file}")

# ----------------------------------------
# STEP 3 — VERIFY CONTENT
# ----------------------------------------
# IMPORTANT:
# The product is NOT marked as used before
# this verification succeeds.

verify_content_file(
    content_file,
    selected_product
)

# ----------------------------------------
# STEP 4 — ONLY NOW mark product as used
# ----------------------------------------

print("")
print("CONTENT IS VERIFIED.")
print("Product is now safe to mark as used.")

mark_product_as_used(
    products,
    selected_product
)

# ----------------------------------------
# STEP 5 — Save products.csv
# ----------------------------------------

save_products(products)

print("")
print("PRODUCT STATUS UPDATED")
print(f"{product_id}: No → Yes")

# ----------------------------------------
# FINAL SUCCESS
# ----------------------------------------

print("")
print("========================================")
print("AUTOMATION COMPLETED SUCCESSFULLY")
print("========================================")
print(f"Generated: {content_file}")
print(f"Processed product: {product_id}")
print("Content verification: PASSED")
print("Product consumption: SAFE")
print("========================================")
```

if **name** == "**main**":
main()
