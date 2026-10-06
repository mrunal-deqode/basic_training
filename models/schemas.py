
from pydantic import BaseModel


class Product(BaseModel):
    name: str
    price: float
    in_stock: bool


class ProductUpdate(BaseModel):
    name: str | None = None
    price: float | None = None
    in_stock: bool | None = None
