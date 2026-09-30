import csv

TAX_RATE = 0.15


class Product:
    def __init__(self, name, cost_price, country):
        self.name = name
        self.cost_price = cost_price
        self.country = country

    def calculate_tax(self):
        return self.cost_price * TAX_RATE

    def calculate_final_price(self, tax):
        return self.cost_price + tax


# product = Product("A4 Paper", 100, "India")
with (
    open("input.csv", "r") as input_file,
    open("class_output.csv", "w", newline="") as output_file,
):
    reader = csv.DictReader(input_file)
    writer = csv.DictWriter(
        output_file,
        fieldnames=[
            "Product-Name",
            "Product-CostPrice",
            "Product-SalesTax",
            "Product-FinalPrice",
            "Country",
        ],
    )

    writer.writeheader()

    for row in reader:
        product = Product(
            row["Product-Name"], float(row["Product-CostPrice"]), row["Country"]
        )

        # print("Product:", product.name)
        # print("Cost:", product.cost_price)
        # print("Country:", product.country)

        tax = product.calculate_tax()
        final_price = product.calculate_final_price(tax)

        # print("Product:", product.name)
        # print("Cost:", product.cost_price)
        # print("Tax:", tax)
        # print("Final Price:", final_price)
        # print("Country:", product.country)
        writer.writerow(
            {
                "Product-Name": product.name,
                "Product-CostPrice": product.cost_price,
                "Product-SalesTax": tax,
                "Product-FinalPrice": final_price,
                "Country": product.country,
            }
        )
