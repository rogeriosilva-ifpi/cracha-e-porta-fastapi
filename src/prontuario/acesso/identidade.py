"""Quem está pedindo? Três provas aceitas (capítulos 6, 7 e 15):
token Bearer (apps), chave de API (máquinas e agentes) ou cookie de
sessão (navegador). Cada uma pelo seu esquema; sem plano B."""
import jwt
from fastapi import Request

from prontuario.acesso import usuarios
from prontuario.acesso.chaves import verificar_chave
from prontuario.acesso.refresh import familia_ativa
from prontuario.acesso.sessoes import identificar as da_sessao
from prontuario.acesso.tokens import verificar_access


def identificar(request: Request) -> dict | None:
    request.state.chave = None               # só preenchida quando veio por chave
    auth = request.headers.get("authorization")
    if auth is None:
        return da_sessao(request)
    partes = auth.split(" ")
    if len(partes) != 2 or not partes[1]:
        return None
    tipo, credencial = partes
    if tipo == "ApiKey":
        k = verificar_chave(credencial)
        if k is None:
            return None
        request.state.chave = {"id": k["id"], "escopos": k["escopos"]}
        return usuarios.por_id(k["usuario_id"])   # papel de HOJE, não o da criação
    if tipo != "Bearer":
        return None
    try:
        p = verificar_access(credencial)
    except jwt.InvalidTokenError:            # inválido, vencido, de outro: 401
        return None
    # Nossa API também confere se a família não foi revogada.
    f = familia_ativa(p["sid"]) if isinstance(p.get("sid"), str) else None
    if f is None or f["usuario_id"] != p["sub"]:
        return None
    request.state.familia = p["sid"]
    return usuarios.por_id(p["sub"])         # papel atual vem do banco
