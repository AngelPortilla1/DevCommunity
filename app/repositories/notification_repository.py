from sqlalchemy.orm import Session, selectinload
from app.models.notification import Notification, NotificationType


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        recipient_id: int,
        actor_id: int,
        notification_type: NotificationType,
        post_id: int | None = None
    ) -> Notification:
        notif = Notification(
            recipient_id=recipient_id,
            actor_id=actor_id,
            type=notification_type,
            post_id=post_id,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def get_by_recipient(
        self,
        recipient_id: int,
        page: int,
        size: int
    ) -> tuple[int, list[Notification]]:
        query = (
            self.db.query(Notification)
            .options(
                selectinload(Notification.actor),
                selectinload(Notification.post),
            )
            .filter(Notification.recipient_id == recipient_id)
            .order_by(Notification.created_at.desc())
        )
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return total, items

    def get_by_id(self, notification_id: int) -> Notification | None:
        return self.db.query(Notification).filter(Notification.id == notification_id).first()

    def count_unread(self, recipient_id: int) -> int:
        return (
            self.db.query(Notification)
            .filter(
                Notification.recipient_id == recipient_id,
                Notification.is_read == False,
            )
            .count()
        )

    def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, recipient_id: int) -> int:
        """Marca todas las no leidas como leidas y retorna la cantidad actualizada."""
        updated = (
            self.db.query(Notification)
            .filter(
                Notification.recipient_id == recipient_id,
                Notification.is_read == False,
            )
            .update({"is_read": True})
        )
        self.db.commit()
        return updated
