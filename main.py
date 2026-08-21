import csv
import os

print("========================================")
print("   AMAZON DESK SETUP AUTOMATION")
print("========================================")

# Load the product database
with open("products.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)
    products = list(reader)

# Find the first unused product
unused_product = None

for product in products:
    if product["used"].strip().lower() == "no":
        unused_product = product
        break

# If an unused product exists
if unused_product:

    product_id = unused_product["product_id"]
    product_name = unused_product["product_name"]
    category = unused_product["category"]
    amazon_link = unused_product["amazon_link"]

    print("\nNEXT PRODUCT")
    print("----------------------------------------")
    print("Product ID:", product_id)
    print("Product:", product_name)
    print("Category:", category)
    print("Amazon Link:", amazon_link)
    print("----------------------------------------")

    # Create content folder if it doesn't exist
    os.makedirs("content", exist_ok=True)

    # Create content file
    content_file = f"content/{product_id}.txt"

    with open(content_file, "w", encoding="utf-8") as file:
        file.write("AMAZON DESK SETUP CONTENT PACKAGE\n")
        file.write("=================================\n\n")

        file.write(f"Product ID: {product_id}\n")
        file.write(f"Product Name: {product_name}\n")
        file.write(f"Category: {category}\n")
        file.write(f"Amazon Link: {amazon_link}\n\n")

        file.write("MEDIUM BLOG\n")
        file.write("-----------\n")
        file.write(f"Title: {product_name} – A Simple Upgrade for Your Desk\n")
        file.write("Subtitle: A practical desk upgrade worth considering.\n\n")

        file.write("PINTEREST MAIN PIN\n")
        file.write("-----------------\n")
        file.write(f"Title: {product_name} Desk Setup Upgrade\n")
        file.write(
            f"Description: Upgrade your desk setup with {product_name}. "
            "A simple idea for creating a cleaner, more productive workspace.\n\n"
        )

        file.write("PINTEREST PRODUCT PIN\n")
        file.write("---------------------\n")
        file.write(f"Title: {product_name} for a Better Desk Setup\n")
        file.write(
            f"Description: Looking for a simple desk upgrade? "
            f"Check out this {product_name}.\n"
        )

    print("\nCONTENT PACKAGE CREATED")
    print("----------------------------------------")
    print("File:", content_file)
    print("----------------------------------------")

    # Mark the selected product as used
    for product in products:
        if product["product_id"] == product_id:
            product["used"] = "Yes"
            break

    # Save updated product database
    with open("products.csv", "w", newline="", encoding="utf-8") as file:

        fieldnames = [
            "product_id",
            "product_name",
            "category",
            "amazon_link",
            "used"
        ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(products)

    print("\nSTATUS UPDATED")
    print("----------------------------------------")
    print(product_name, "is now marked as USED.")
    print("----------------------------------------")

else:
    print("\nAll products have been used.")
