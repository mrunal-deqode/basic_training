# Think About It

### 1. What happens if we send an extra field that is not defined in the Pydantic model?

If we send an extra field that is not present in the Pydantic model, Pydantic ignores that field by default. It is not included in the final model/response.

For example, if `color` is not defined in `Product` but we send `"color": "black"`, the extra field is dropped.

### 2. Why might `response_model` differ from the request body model?

The request model defines what data the client is allowed to send, while the response model defines what data our API should send back.

They can be different because we may receive some internal or sensitive data that we don't want to expose to the client. For example, a request/database model might contain a password or internal code, while the `response_model` can leave those fields out.
