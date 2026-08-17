print("Amazon Desk Setup Automation")
print("System is starting...")
import csv

print("Amazon Desk Setup Automation Started!")

with open("products.csv", "r", encoding="utf-8") as file:
    products = csv.DictReader(file)

    for product in products:
        print("--------------------------------")
        print("Product ID:", product["product_id"])
        print("Product:", product["product_name"])
        print("Category:", product["category"])
        print("Amazon Link:", product["amazon_link"])
        print("Used:", product["used"])

print("--------------------------------")
print("Products loaded successfully!")
