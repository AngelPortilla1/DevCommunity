from app.exceptions.base import AppException


class NotificationNotFound(AppException):
    def __init__(self):
        super().__init__(message="Notificacion no encontrada", status_code=404)


class ForbiddenNotificationAction(AppException):
    def __init__(self):
        super().__init__(
            message="No tienes permisos para realizar esta accion sobre la notificacion",
            status_code=403
        )
