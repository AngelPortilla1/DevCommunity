from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.like_service import LikeService

router = APIRouter(prefix="/posts", tags=["Likes"])

def get_like_service(db: Session = Depends(get_db)):
    return LikeService(db)

@router.post("/{post_id}/like", status_code=status.HTTP_201_CREATED)
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service)
):
    return service.like_post(post_id, current_user.id)
    
@router.delete("/{post_id}/like", status_code=status.HTTP_200_OK)
def unlike_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    service: LikeService = Depends(get_like_service)
):
    return service.unlike_post(post_id, current_user.id)
