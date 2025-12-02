from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["Test"])

@router.get("/")
def test():
    return {"message": "API working correctly!"}
