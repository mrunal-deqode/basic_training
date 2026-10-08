# Day 5 — Think About It

## 1. Why separate schemas.py and models.py instead of reusing one?

Pydantic schemas define the API request and response structure, while SQLAlchemy models define the database table structure. Keeping them separate prevents changes in the database from directly affecting the API response needed.

---

## 2. Realistic bug if PATCH doesn't handle "field not provided" correctly?
If a user updates only one field, such as `status`, and the code treats all other omitted fields as `None`, it could overwrite existing values.
For example, updating: `status` could accidentally change `title`, `description`, and `due_date` to `None`. Using `exclude_unset=True` ensures that only fields actually provided from the API are updated.
