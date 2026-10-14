"""Application exceptions. Framework-agnostic; handlers translate them to HTTP.

Messages are user-facing and therefore in Portuguese.
"""

from http import HTTPStatus


class AppError(Exception):
    status_code: int = HTTPStatus.BAD_REQUEST
    message: str = "Erro na requisição."
    # Stable identifier for the frontend to react to specific errors
    code: str | None = None

    def __init__(self, message: str | None = None) -> None:
        if message:
            self.message = message
        super().__init__(self.message)


class Unauthorized(AppError):
    status_code = HTTPStatus.UNAUTHORIZED
    message = "Senha do app inválida ou ausente."


class MissingConfiguration(AppError):
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    message = "Configuração do servidor incompleta."
