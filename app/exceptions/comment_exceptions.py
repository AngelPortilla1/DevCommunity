from fastapi import HTTPException, status

class CommentNotFound(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comentario no encontrado"
        )

class ForbiddenCommentAction(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para esta acción"
        )
