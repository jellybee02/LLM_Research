from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3)
    email: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None = None
