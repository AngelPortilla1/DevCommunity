from app.exceptions.base import AppException


class PostAlreadySaved(AppException):
    def __init__(self):
        super().__init__(
            message="El post ya se encuentra en guardados",
            status_code=400
        )


class PostNotSaved(AppException):
    def __init__(self):
        super().__init__(
            message="El post no esta en guardados",
            status_code=404
        )
