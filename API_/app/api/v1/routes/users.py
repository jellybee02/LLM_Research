from fastapi import APIRouter, HTTPException, status
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_user, get_user

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int):
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_api(payload: UserCreate):
    try:
        return create_user(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
