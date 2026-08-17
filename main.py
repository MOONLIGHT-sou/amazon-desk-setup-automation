import csv

print("========================================")
print("   AMAZON DESK SETUP AUTOMATION")
print("========================================")

# Open the product database
with open("products.csv", "r", encoding="utf-8") as file:
    products = list(csv.DictReader(file))

# Find the first unused product
unused_product = None

for product in products:
    if product["used"].strip().lower() == "no":
        unused_product = product
        break

# Display the selected product
if unused_product:
    print("\nNEXT PRODUCT")
    print("----------------------------------------")
    print("Product ID:", unused_product["product_id"])
    print("Product:", unused_product["product_name"])
    print("Category:", unused_product["category"])
    print("Amazon Link:", unused_product["amazon_link"])
    print("Used:", unused_product["used"])
    print("----------------------------------------")
else:
    print("\nAll products have been used.")
