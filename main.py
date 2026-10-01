from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "hello"}


@app.get("/items/{item_id}")
def get_item(item_id: int):
    return {"item_id": item_id}


@app.get("/search")
def search_items(q: str = "all"):
    return {"query": q}
