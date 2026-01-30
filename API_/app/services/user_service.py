from app.schemas.user import UserCreate

_FAKE_USERS = [
    {"id": 1, "username": "jellybee", "email": "test@test.com"}
]

def get_user(user_id: int):
    for u in _FAKE_USERS:
        if u["id"] == user_id:
            return u
    return None

def create_user(payload: UserCreate):
    for u in _FAKE_USERS:
        if u["username"] == payload.username:
            raise ValueError("Username already exists")

    new_user = {
        "id": len(_FAKE_USERS) + 1,
        "username": payload.username,
        "email": payload.email,
        "internal_flag": True,  # response_model이 있으면 밖으로 안 나감
    }
    _FAKE_USERS.append(new_user)
    return new_user
