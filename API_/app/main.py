from fastapi import FastAPI
from app.api.v1.router import api_v1_router

app = FastAPI(title="Study API")

app.include_router(api_v1_router, prefix="/api/v1")










# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def root():
#     return {"message": "Hello FastAPI"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int):
#     print(f"Fetching item with ID: {item_id}")
#     return {"item_id": item_id}

# @app.get("/search")
# def search_items(q: str, limit: int = 10):
#     return {
#         "query": q,
#         "limit": limit
#     }
    


# from typing import Annotated
# from fastapi import FastAPI, Depends, Query
# from pydantic import BaseModel, field_validator, Field

# app = FastAPI()


# class SearchParams(BaseModel):
#     q: str = Field(..., description="Search query (not blank)")
#     limit: int = Field(10, ge=1, le=100, description="Limit between 1 and 100")

#     @field_validator("q")
#     @classmethod
#     def q_must_not_be_blank(cls, v: str) -> str:
#         v2 = v.strip()
#         if not v2:
#             raise ValueError("q must not be blank (whitespace-only).")
#         return v2  # ✅ 여기서 trim까지 해버리면 이후 로직이 편해짐


# @app.get("/search")
# def search_items(params: Annotated[SearchParams, Depends()]):
#     # params.q 는 이미 strip된 값
#     return {"query": params.q, "limit": params.limit}


# from fastapi import FastAPI
# from pydantic import BaseModel, Field

# class ItemCreate(BaseModel):
#     name: str = Field(..., min_length=1)
#     price: float = Field(..., gt=0)
#     description: str | None = None


# app = FastAPI()

# @app.post("/items")
# def create_item(item: ItemCreate):
#     return {
#         "name": item.name,
#         "price": item.price,
#         "description": item.description,
#     }


# from fastapi import FastAPI, HTTPException, status
# from schemas.user import UserCreate, UserResponse

# app = FastAPI()

# # 가짜 DB
# FAKE_USERS = [
#     {"id": 1, "username": "jellybee", "email": "test@test.com"}
# ]


# @app.post("/users/{user_id}", response_model=UserResponse, status_code=201)
# def get_user(user_id: int):
#     # 존재 여부 검사
#     for user in FAKE_USERS:
#         if user["id"] == user_id:
#             return user

#     # 없으면 404
#     raise HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND,
#         detail="User not found"
#     )


# @app.post(
#     "/users",
#     response_model=UserResponse,
#     status_code=status.HTTP_201_CREATED
# )
# def create_user(user: UserCreate):
#     # username 중복 체크
#     for u in FAKE_USERS:
#         if u["username"] == user.username:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Username already exists"
#             )

#     new_user = {
#         "id": len(FAKE_USERS) + 1,
#         "username": user.username,
#         "email": user.email,
#         "internal_flag": True,  # 🔥 있어도 응답엔 안 나감
#     }

#     FAKE_USERS.append(new_user)
#     return new_user




# @app.post("/users/{user_id}", response_model=UserResponse, status_code=201)
# def get_user(user_id: int):
#     # 존재 여부 검사
#     for user in FAKE_USERS:
#         if user["id"] == user_id:
#             return user

#     # 없으면 404
#     raise HTTPException(
#         status_code=status.HTTP_404_NOT_FOUND,
#         detail="User not found"
#     )


# from fastapi import FastAPI, HTTPException, Request
# from fastapi.responses import JSONResponse
# from fastapi.exceptions import RequestValidationError


# # 1) 400/404 같은 HTTPException 포맷 통일
# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "error": {
#                 "code": "HTTP_ERROR",
#                 "message": exc.detail,
#                 "details": [
#                     {"field": None, "reason": f"HTTP {exc.status_code}"}
#                 ],
#             }
#         },
#     )

# # 2) 422 검증 에러 포맷 통일 (FastAPI/Pydantic가 자동으로 만드는 에러)
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     details = []
#     for e in exc.errors():
#         loc = ".".join(str(x) for x in e.get("loc", []))  # ex) body.username, path.item_id
#         msg = e.get("msg", "Invalid value")
#         details.append({"field": loc, "reason": msg})

#     return JSONResponse(
#         status_code=422,
#         content={
#             "error": {
#                 "code": "VALIDATION_ERROR",
#                 "message": "Request validation failed",
#                 "details": details,
#             }
#         },
#     )