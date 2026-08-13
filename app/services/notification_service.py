from sqlalchemy.orm import Session
from app.repositories.notification_repository import NotificationRepository
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.exceptions.notification_exceptions import NotificationNotFound, ForbiddenNotificationAction


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationRepository(db)

    # ── Helpers internos (llamados desde otros servicios) ────────

    def notify_like(self, post_author_id: int, actor_id: int, post_id: int):
        """Crea una notificacion de like. No notifica si el actor es el autor."""
        if post_author_id == actor_id:
            return
        self.repository.create(
            recipient_id=post_author_id,
            actor_id=actor_id,
            notification_type=NotificationType.like,
            post_id=post_id,
        )

    def notify_comment(self, post_author_id: int, actor_id: int, post_id: int):
        """Crea una notificacion de comentario. No notifica si el actor es el autor."""
        if post_author_id == actor_id:
            return
        self.repository.create(
            recipient_id=post_author_id,
            actor_id=actor_id,
            notification_type=NotificationType.comment,
            post_id=post_id,
        )

    def notify_follow(self, followed_id: int, follower_id: int):
        """Crea una notificacion de nuevo seguidor."""
        self.repository.create(
            recipient_id=followed_id,
            actor_id=follower_id,
            notification_type=NotificationType.follow,
        )

    # ── Endpoints del usuario ────────────────────────────────────

    def get_my_notifications(self, current_user: User, page: int, size: int):
        total, notifications = self.repository.get_by_recipient(
            recipient_id=current_user.id,
            page=page,
            size=size,
        )

        total_pages = (total + size - 1) // size if size > 0 else 0

        items = [self._map(n) for n in notifications]

        return {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "items": items,
        }

    def get_unread_count(self, current_user: User):
        count = self.repository.count_unread(current_user.id)
        return {"unread_count": count}

    def mark_as_read(self, notification_id: int, current_user: User):
        notif = self.repository.get_by_id(notification_id)
        if not notif:
            raise NotificationNotFound()
        if notif.recipient_id != current_user.id:
            raise ForbiddenNotificationAction()
        updated = self.repository.mark_as_read(notif)
        return self._map(updated)

    def mark_all_as_read(self, current_user: User):
        updated_count = self.repository.mark_all_as_read(current_user.id)
        return {"marked_as_read": updated_count}

    # ── Mapper interno ───────────────────────────────────────────

    @staticmethod
    def _map(n: Notification) -> dict:
        return {
            "id":         n.id,
            "type":       n.type.value if hasattr(n.type, "value") else n.type,
            "is_read":    n.is_read,
            "created_at": n.created_at,
            "post_id":    n.post_id,
            "post_title": n.post.title if n.post else None,
            "actor": {
                "id":       n.actor.id,
                "username": n.actor.username,
                "email":    n.actor.email,
            },
        }
