# Day 4 — Think About It

## 1. Why does `get_db()` use dependency + `yield` instead of simply returning a session?

`yield` allows FastAPI to use the database session during the request and then continue to the `finally` block after the request is finished.

This ensures the session is always closed.

If we simply use `return db`, the function ends immediately and there is no cleanup step to automatically close the session. This can cause database connections to remain open and eventually exhaust the connection pool.

---

## 2. What goes wrong if two requests share the same DB session simultaneously?

A SQLAlchemy session represents a single unit of work and should normally be used by one request at a time.

If two requests share the same session, they can interfere with each other's database operations. This can lead to unexpected results & inconsistent data.

That is why `get_db()` creates a new session for each request and closes it when the request finishes.
