"""Sessões. VERSÃO INGÊNUA (tag cap05-antes): veja o capítulo 5."""
import secrets

from fastapi import Request, Response

from prontuario.acesso import usuarios

_sessoes: dict[str, str] = {}  # id -> usuario_id


def identificar(request: Request) -> dict | None:
    uid = _sessoes.get(request.cookies.get("sessao", ""))
    return usuarios.por_id(uid) if uid else None


def iniciar(request: Request, response: Response, usuario_id: str) -> None:
    id_ = request.cookies.get("sessao") or secrets.token_hex(16)
    _sessoes[id_] = usuario_id
    response.set_cookie("sessao", id_, path="/")


def encerrar(request: Request, response: Response) -> None:
    response.delete_cookie("sessao", path="/")
