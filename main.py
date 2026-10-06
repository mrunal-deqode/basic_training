from fastapi import FastAPI

from routers import categories, products

app = FastAPI()

app.include_router(products.router)
app.include_router(categories.router)
