# Day 1 — Think About It

## 1. What's the practical difference between ASGI and WSGI, and why does that matter for how many requests FastAPI can serve at once?

**Answer:**

WSGI is a traditional synchronous interface for Python web applications, while ASGI supports asynchronous applications and concurrency.

This matters because FastAPI can efficiently handle multiple I/O-bound requests at the same time. For example, while one request is waiting for a database or network response, the server can work on another request instead of remaining idle.

---

## 2. If you remove the `: int` type hint from `item_id`, what changes in how FastAPI treats a request to `/items/abc`?

**Answer:**

Without the `: int` type hint, FastAPI treats `item_id` as a string by default.

Therefore, a request to `/items/abc` would be accepted, and the function would receive:

```python
item_id = "abc"
```

Instead of returning an integer validation error, FastAPI would accept the value as a string.
