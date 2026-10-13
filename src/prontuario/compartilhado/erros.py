"""Hierarquia de erros HTTP do curso, com 401 e 403 do Tópico 3."""


class HttpError(Exception):
    status = 500
    mensagem = "Erro interno."

    def __init__(self, mensagem: str | None = None):
        super().__init__(mensagem or self.mensagem)
        self.mensagem = mensagem or self.mensagem


class UnauthorizedError(HttpError):
    status, mensagem = 401, "Não autenticado."


class ForbiddenError(HttpError):
    status, mensagem = 403, "Acesso negado."


class NotFoundError(HttpError):
    status, mensagem = 404, "Recurso não encontrado."
