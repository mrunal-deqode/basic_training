from typing import Optional

from pydantic import BaseModel


class Product(BaseModel):
    name: str
    price: float
    in_stock: bool


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None
