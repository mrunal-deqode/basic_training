import csv

TAX_RATE = 0.15

fieldnames = [
    "Product-Name",
    "Product-CostPrice",
    "Product-SalesTax",
    "Product-FinalPrice",
    "Country",
]


def calculate_tax(cost_price):
    tax = cost_price * TAX_RATE
    # print("tax", tax)
    return tax


def calculate_final_price(cost_price, tax):
    final_price = cost_price + tax
    # print("final_price", final_price)
    return final_price


with (
    open("input.csv", "r") as input_file,
    open("output.csv", "w", newline="") as output_file,
):
    reader = csv.DictReader(input_file)
    writer = csv.DictWriter(output_file, fieldnames=fieldnames)

    writer.writeheader()

    for row in reader:
        product_name = row["Product-Name"]
        cost_price = float(row["Product-CostPrice"])
        country = row["Country"]
        # print("Product :",product_name)
        # print("Cost :",cost_price)
        # print("Country :",country)
        tax = calculate_tax(cost_price)
        # print("tax", tax)
        final_price = calculate_final_price(cost_price, tax)
        # print("final_price", final_price)
        writer.writerow(
            {
                "Product-Name": product_name,
                "Product-CostPrice": cost_price,
                "Product-SalesTax": tax,
                "Product-FinalPrice": final_price,
                "Country": country,
            }
        )
