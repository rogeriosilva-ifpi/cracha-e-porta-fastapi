"""Quem está pedindo? VERSÃO INGÊNUA (tag cap06-antes)."""
from fastapi import Request

from prontuario.acesso import usuarios
from prontuario.acesso.sessoes import identificar as da_sessao
from prontuario.acesso.tokens import verificar_access


def identificar(request: Request) -> dict | None:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        p = verificar_access(auth[7:])
        return usuarios.por_id(p["sub"])
    return da_sessao(request)
