import csv

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

    print("\nNEXT PRODUCT")
    print("----------------------------------------")
    print("Product ID:", unused_product["product_id"])
    print("Product:", unused_product["product_name"])
    print("Category:", unused_product["category"])
    print("Amazon Link:", unused_product["amazon_link"])
    print("Used:", unused_product["used"])
    print("----------------------------------------")

    # Mark the selected product as used
    for product in products:
        if product["product_id"] == unused_product["product_id"]:
            product["used"] = "Yes"
            break

    # Save the updated database
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
    print(unused_product["product_name"], "is now marked as USED.")
    print("----------------------------------------")

else:
    print("\nAll products have been used.")
