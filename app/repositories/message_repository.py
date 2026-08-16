from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload
from app.models.conversation import Conversation, Message
from app.models.user import User


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_conversation_by_id(self, conv_id: int) -> Conversation | None:
        return (
            self.db.query(Conversation)
            .options(
                selectinload(Conversation.user1),
                selectinload(Conversation.user2),
            )
            .filter(Conversation.id == conv_id)
            .first()
        )

    def find_conversation_between(self, user_a_id: int, user_b_id: int) -> Conversation | None:
        u1, u2 = min(user_a_id, user_b_id), max(user_a_id, user_b_id)
        return (
            self.db.query(Conversation)
            .options(
                selectinload(Conversation.user1),
                selectinload(Conversation.user2),
            )
            .filter(
                Conversation.user1_id == u1,
                Conversation.user2_id == u2,
            )
            .first()
        )

    def create_conversation(self, user_a_id: int, user_b_id: int) -> Conversation:
        u1, u2 = min(user_a_id, user_b_id), max(user_a_id, user_b_id)
        now = datetime.utcnow()
        conv = Conversation(
            user1_id=u1,
            user2_id=u2,
            created_at=now,
            last_message_at=now,
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return (
            self.db.query(Conversation)
            .options(
                selectinload(Conversation.user1),
                selectinload(Conversation.user2),
            )
            .filter(Conversation.id == conv.id)
            .first()
        )

    def get_user_conversations(self, user_id: int) -> list[Conversation]:
        return (
            self.db.query(Conversation)
            .options(
                selectinload(Conversation.user1),
                selectinload(Conversation.user2),
            )
            .filter(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                )
            )
            .order_by(Conversation.last_message_at.desc())
            .all()
        )

    def get_messages_by_conversation(
        self,
        conv_id: int,
        page: int,
        size: int,
    ) -> tuple[int, list[Message]]:
        query = (
            self.db.query(Message)
            .options(selectinload(Message.sender))
            .filter(Message.conversation_id == conv_id)
            .order_by(Message.created_at.asc())
        )
        total = query.count()
        items = query.offset((page - 1) * size).limit(size).all()
        return total, items

    def get_last_message(self, conv_id: int) -> Message | None:
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conv_id)
            .order_by(Message.created_at.desc())
            .first()
        )

    def count_unread_in_conversation(self, conv_id: int, user_id: int) -> int:
        return (
            self.db.query(Message)
            .filter(
                Message.conversation_id == conv_id,
                Message.sender_id != user_id,
                Message.is_read == False,
            )
            .count()
        )

    def count_total_unread(self, user_id: int) -> int:
        return (
            self.db.query(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .filter(
                or_(
                    Conversation.user1_id == user_id,
                    Conversation.user2_id == user_id,
                ),
                Message.sender_id != user_id,
                Message.is_read == False,
            )
            .count()
        )

    def create_message(self, conv: Conversation, sender_id: int, content: str) -> Message:
        now = datetime.utcnow()
        message = Message(
            conversation_id=conv.id,
            sender_id=sender_id,
            content=content,
            is_read=False,
            created_at=now,
        )
        conv.last_message_at = now
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        # Reload with sender
        return (
            self.db.query(Message)
            .options(selectinload(Message.sender))
            .filter(Message.id == message.id)
            .first()
        )

    def mark_messages_as_read(self, conv_id: int, user_id: int) -> int:
        updated = (
            self.db.query(Message)
            .filter(
                Message.conversation_id == conv_id,
                Message.sender_id != user_id,
                Message.is_read == False,
            )
            .update({"is_read": True})
        )
        self.db.commit()
        return updated
