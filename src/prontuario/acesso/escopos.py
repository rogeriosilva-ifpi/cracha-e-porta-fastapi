"""A matriz como escopos do FastAPI (capítulo 11): Security(..., scopes=[...])
é o mecanismo nativo de escopos OAuth. Aqui o escopo pedido pela rota é
conferido contra a MATRIZ do papel; com tokens OAuth, seria conferido
também contra os escopos que o token carrega."""
from fastapi import Request
from fastapi.security import SecurityScopes

from prontuario.acesso.identidade import identificar
from prontuario.acesso.permissoes import pode
from prontuario.acesso.politica import dentro_do_escopo
from prontuario.compartilhado.erros import ForbiddenError, UnauthorizedError


def com_escopos(security_scopes: SecurityScopes, request: Request) -> dict:
    usuario = identificar(request)                       # portão 1
    if usuario is None:
        raise UnauthorizedError()
    if not all(pode(usuario["papel"], e) for e in security_scopes.scopes):
        raise ForbiddenError("Permissão insuficiente.")  # portão 2
    for e in security_scopes.scopes:                     # portão 2b (cap. 15)
        dentro_do_escopo(request, e)
    return usuario
