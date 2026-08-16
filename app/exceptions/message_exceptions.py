from app.exceptions.base import AppException


class ConversationNotFound(AppException):
    def __init__(self):
        super().__init__(
            message="Conversacion no encontrada",
            status_code=404
        )


class ForbiddenConversationAction(AppException):
    def __init__(self):
        super().__init__(
            message="No tienes permisos para acceder a esta conversacion",
            status_code=403
        )


class CannotMessageSelf(AppException):
    def __init__(self):
        super().__init__(
            message="No puedes iniciar una conversacion contigo mismo",
            status_code=400
        )


class UserNotFoundForMessage(AppException):
    def __init__(self):
        super().__init__(
            message="Usuario destinatario no encontrado",
            status_code=404
        )
