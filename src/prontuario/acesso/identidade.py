"""Quem está pedindo? Duas provas aceitas (capítulo 6):
token Bearer (clientes de API) ou cookie de sessão (navegador)."""
import jwt
from fastapi import Request

from prontuario.acesso import usuarios
from prontuario.acesso.sessoes import identificar as da_sessao
from prontuario.acesso.tokens import verificar_access


def identificar(request: Request) -> dict | None:
    auth = request.headers.get("authorization")
    if auth is None:
        return da_sessao(request)
    tipo, _, token = auth.partition(" ")
    if tipo != "Bearer" or not token:
        return None                          # sem plano B
    try:
        p = verificar_access(token)
    except jwt.InvalidTokenError:            # inválido, vencido, de outro: 401
        return None
    return usuarios.por_id(p["sub"])         # papel atual vem do banco
