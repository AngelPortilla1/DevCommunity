from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.follower_service import FollowerService

router = APIRouter(prefix="/users", tags=["Followers"])

def get_follower_service(db: Session = Depends(get_db)):
    return FollowerService(db)

@router.post("/{user_id}/follow", status_code=status.HTTP_201_CREATED)
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: FollowerService = Depends(get_follower_service)
):
    return service.follow_user(follower_id=current_user.id, followed_id=user_id)

@router.delete("/{user_id}/follow", status_code=status.HTTP_200_OK)
def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: FollowerService = Depends(get_follower_service)
):
    return service.unfollow_user(follower_id=current_user.id, followed_id=user_id)
