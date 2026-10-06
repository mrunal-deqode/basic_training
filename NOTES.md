# Think About It

## 1. Why do large FastAPI apps avoid putting every route in one `main.py`?

If all routes are written in `main.py`, the file becomes very large and difficult to read and maintain as the application grows.

Using `APIRouter`, we can separate routes based on their purpose, such as products, users, and orders. This keeps the code organized and makes it easier to find, update, and manage routes.

**In short:** `APIRouter` keeps a large FastAPI application clean, organized, and maintainable.

## 2. Difference between PUT and PATCH

**PUT** is used when we want to replace or update the complete resource. It generally expects all the required fields.

**PATCH** is used when we want to update only part of a resource.

For example, if we only want to change the price of a product, we should use **PATCH** because we don't need to send the product's other fields again.

**In short:** PUT = full update, PATCH = partial update.
