"""Hierarquia de erros HTTP: cada erro sabe seu status."""


class HttpError(Exception):
    status = 500
    mensagem = "Erro interno."

    def __init__(self, mensagem: str | None = None):
        super().__init__(mensagem or self.mensagem)
        self.mensagem = mensagem or self.mensagem


class BadRequestError(HttpError):
    status, mensagem = 400, "Requisição inválida."


class UnauthorizedError(HttpError):
    status, mensagem = 401, "Não autenticado."


class ForbiddenError(HttpError):
    status, mensagem = 403, "Acesso negado."


class NotFoundError(HttpError):
    status, mensagem = 404, "Recurso não encontrado."


class TooManyRequestsError(HttpError):
    status, mensagem = 429, "Muitas tentativas. Tente mais tarde."

    def __init__(self, retry_after_s: int, mensagem: str | None = None):
        super().__init__(mensagem)
        self.retry_after_s = retry_after_s
