from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.services.message_service import MessageService
from app.schemas.message_schema import (
    MessageCreate,
    MessageResponse,
    ConversationResponse,
    ConversationListItem,
    PaginatedMessages,
    UnreadMessagesCountResponse,
    MarkReadResponse,
)

router = APIRouter(prefix="/messages", tags=["Messages"])


def get_message_service(db: Session = Depends(get_db)):
    return MessageService(db)


# Cantidad total de mensajes no leidos
@router.get("/unread-count", response_model=UnreadMessagesCountResponse)
def get_unread_count(
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.get_unread_count(current_user)


# Listar todas las conversaciones del usuario
@router.get("/conversations", response_model=list[ConversationListItem])
def get_conversations(
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.get_conversations(current_user)


# Iniciar u obtener conversacion existente con un usuario
@router.post(
    "/conversations/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=ConversationResponse,
)
def get_or_create_conversation(
    user_id: int,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.get_or_create_conversation(current_user, user_id)


# Obtener mensajes paginados de una conversacion
@router.get("/conversations/{conv_id}/messages", response_model=PaginatedMessages)
def get_messages_subpath(
    conv_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.get_messages(conv_id, current_user, page=page, size=size)


# Obtener mensajes paginados de una conversacion (ruta directa segun especificacion /conversations/{conv_id})
@router.get("/conversations/{conv_id}", response_model=PaginatedMessages)
def get_messages(
    conv_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.get_messages(conv_id, current_user, page=page, size=size)


# Enviar mensaje en una conversacion
@router.post(
    "/conversations/{conv_id}/send",
    status_code=status.HTTP_201_CREATED,
    response_model=MessageResponse,
)
def send_message(
    conv_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.send_message(conv_id, current_user, payload.content)


# Marcar mensajes de una conversacion como leidos
@router.patch("/conversations/{conv_id}/read", response_model=MarkReadResponse)
def mark_as_read(
    conv_id: int,
    current_user: User = Depends(get_current_user),
    service: MessageService = Depends(get_message_service),
):
    return service.mark_as_read(conv_id, current_user)
