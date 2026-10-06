from fastapi import APIRouter, HTTPException, status
from models.schemas import Product, ProductUpdate


router = APIRouter()

products = [
    {"id": 1, "name": "Laptop", "price": 50000, "in_stock": True},
    {"id": 2, "name": "Mouse", "price": 1000, "in_stock": True},
]


@router.get("/products")
def get_products():
    return products


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: Product):
    new_product = product.model_dump()
    new_product["id"] = max(p["id"] for p in products) + 1
    products.append(new_product)
    return new_product


@router.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
    )


@router.put("/products/{product_id}")
def update_product(product_id: int, product: Product):
    for existing_product in products:
        if existing_product["id"] == product_id:
            existing_product["name"] = product.name
            existing_product["price"] = product.price
            existing_product["in_stock"] = product.in_stock
            return existing_product

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
    )


@router.patch("/products/{product_id}")
def patch_product(product_id: int, product: ProductUpdate):
    for existing_product in products:
        if existing_product["id"] == product_id:
            if product.name is not None:
                existing_product["name"] = product.name

            if product.price is not None:
                existing_product["price"] = product.price

            if product.in_stock is not None:
                existing_product["in_stock"] = product.in_stock

            return existing_product

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            products.remove(product)
            return

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Product not found"
    )
