from fastapi import APIRouter, Header, Response

router = APIRouter()


@router.get("/categories")
def get_categories():
    return ["Fiction", "Mystery", "Technology"]


@router.get("/categories/info")
def category_info(response: Response, user_agent: str | None = Header(default=None)):
    response.headers["X-App-Version"] = "1.0"
    response.set_cookie(key="user", value="guest")

    return {"user_agent": user_agent}
