"""Quem está pedindo? Duas provas aceitas (capítulos 6 e 7):
token Bearer (clientes de API) ou cookie de sessão (navegador)."""
import jwt
from fastapi import Request

from prontuario.acesso import usuarios
from prontuario.acesso.refresh import familia_ativa
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
    # Nossa API também confere se a família não foi revogada.
    f = familia_ativa(p["sid"]) if isinstance(p.get("sid"), str) else None
    if f is None or f["usuario_id"] != p["sub"]:
        return None
    request.state.familia = p["sid"]
    return usuarios.por_id(p["sub"])         # papel atual vem do banco
