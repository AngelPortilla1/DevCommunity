from app.exceptions.base import AppException

class PostNotFound(AppException):
    def __init__(self):
        super().__init__(
            message="Post no encontrado",
            status_code=404
        )


class ForbiddenAction(AppException):
    def __init__(self):
        super().__init__(
            message="No tienes permisos para realizar esta acción",
            status_code=403
        )
