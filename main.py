from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class Category(BaseModel):
    name: str
    description: str


class Product(BaseModel):
    name: str
    price: float
    in_stock: bool
    tags: list[str] = Field(default_factory=list)
    category: Category


class ProductResponse(BaseModel):
    name: str
    price: float
    in_stock: bool
    tags: list[str]


@app.post("/products", response_model=ProductResponse)
def create_product(product: Product):
    return product


@app.get("/products", response_model=list[Product])
def get_products():
    return [
        Product(
            name="Laptop",
            price=50000,
            in_stock=True,
            tags=["electronics"],
            category=Category(
                name="Computers", description="Electronic computing devices"
            ),
        ),
        Product(
            name="Keyboard",
            price=2000,
            in_stock=True,
            tags=["electronics", "accessories"],
            category=Category(name="Accessories", description="Computer accessories"),
        ),
    ]
