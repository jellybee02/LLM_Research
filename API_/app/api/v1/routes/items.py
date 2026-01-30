from typing import Annotated
from fastapi import APIRouter, Path

router = APIRouter()

@router.get("/{item_id}")
def read_item(item_id: Annotated[int, Path(ge=1)]):
    return {"item_id": item_id}
