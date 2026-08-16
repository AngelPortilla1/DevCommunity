from sqlalchemy.orm import Session
from app.repositories.message_repository import MessageRepository
from app.models.conversation import Message
from app.models.user import User
from app.exceptions.message_exceptions import (
    ConversationNotFound,
    ForbiddenConversationAction,
    CannotMessageSelf,
    UserNotFoundForMessage,
)


class MessageService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MessageRepository(db)

    def get_or_create_conversation(self, current_user: User, target_user_id: int) -> dict:
        if current_user.id == target_user_id:
            raise CannotMessageSelf()

        target_user = self.repository.get_user_by_id(target_user_id)
        if not target_user:
            raise UserNotFoundForMessage()

        conv = self.repository.find_conversation_between(current_user.id, target_user_id)
        if not conv:
            conv = self.repository.create_conversation(current_user.id, target_user_id)

        other_user = conv.user2 if conv.user1_id == current_user.id else conv.user1
        return {
            "id": conv.id,
            "user1_id": conv.user1_id,
            "user2_id": conv.user2_id,
            "other_user": {
                "id": other_user.id,
                "username": other_user.username,
                "email": other_user.email,
            },
            "created_at": conv.created_at,
            "last_message_at": conv.last_message_at,
        }

    def get_conversations(self, current_user: User) -> list[dict]:
        conversations = self.repository.get_user_conversations(current_user.id)
        items = []

        for conv in conversations:
            other_user = conv.user2 if conv.user1_id == current_user.id else conv.user1
            last_msg = self.repository.get_last_message(conv.id)
            unread_count = self.repository.count_unread_in_conversation(conv.id, current_user.id)

            items.append({
                "id": conv.id,
                "other_user": {
                    "id": other_user.id,
                    "username": other_user.username,
                    "email": other_user.email,
                },
                "last_message": {
                    "id": last_msg.id,
                    "sender_id": last_msg.sender_id,
                    "content": last_msg.content,
                    "is_read": last_msg.is_read,
                    "created_at": last_msg.created_at,
                } if last_msg else None,
                "unread_count": unread_count,
                "created_at": conv.created_at,
                "last_message_at": conv.last_message_at,
            })

        return items

    def get_messages(self, conv_id: int, current_user: User, page: int, size: int) -> dict:
        conv = self.repository.get_conversation_by_id(conv_id)
        if not conv:
            raise ConversationNotFound()

        if current_user.id not in (conv.user1_id, conv.user2_id):
            raise ForbiddenConversationAction()

        total, messages = self.repository.get_messages_by_conversation(conv_id, page, size)
        total_pages = (total + size - 1) // size if size > 0 else 0

        items = [self._map_message(m) for m in messages]

        return {
            "page": page,
            "size": size,
            "total": total,
            "total_pages": total_pages,
            "items": items,
        }

    def send_message(self, conv_id: int, current_user: User, content: str) -> dict:
        conv = self.repository.get_conversation_by_id(conv_id)
        if not conv:
            raise ConversationNotFound()

        if current_user.id not in (conv.user1_id, conv.user2_id):
            raise ForbiddenConversationAction()

        message = self.repository.create_message(conv, current_user.id, content.strip())
        return self._map_message(message)

    def mark_as_read(self, conv_id: int, current_user: User) -> dict:
        conv = self.repository.get_conversation_by_id(conv_id)
        if not conv:
            raise ConversationNotFound()

        if current_user.id not in (conv.user1_id, conv.user2_id):
            raise ForbiddenConversationAction()

        updated_count = self.repository.mark_messages_as_read(conv_id, current_user.id)
        return {"marked_as_read": updated_count}

    def get_unread_count(self, current_user: User) -> dict:
        count = self.repository.count_total_unread(current_user.id)
        return {"unread_count": count}

    @staticmethod
    def _map_message(m: Message) -> dict:
        return {
            "id": m.id,
            "conversation_id": m.conversation_id,
            "sender_id": m.sender_id,
            "content": m.content,
            "is_read": m.is_read,
            "created_at": m.created_at,
            "sender": {
                "id": m.sender.id,
                "username": m.sender.username,
                "email": m.sender.email,
            },
        }
