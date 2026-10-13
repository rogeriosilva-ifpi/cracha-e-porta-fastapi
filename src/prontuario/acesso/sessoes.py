"""Sessões no servidor, identificadas por um cookie (capítulo 5)."""
import hashlib
import secrets
import time

from fastapi import Request, Response

from prontuario.acesso import usuarios
from prontuario.compartilhado.banco import consultar, executar

COOKIE = "__Host-sessao"            # exige Secure e Path=/
OCIOSA_MS = 30 * 60 * 1000          # 30 min sem uso
ABSOLUTA_MS = 8 * 60 * 60 * 1000    # um plantão
OPCOES = dict(httponly=True,        # JavaScript da página não lê
              secure=True,          # só viaja em HTTPS
              samesite="lax",       # não vai em POST vindo de outro site
              path="/")


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _agora() -> int:
    return int(time.time() * 1000)


def _apagar(token: str) -> None:
    executar("DELETE FROM sessoes WHERE id_hash = ?", _sha256(token))


def identificar(request: Request) -> dict | None:
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    s = consultar("SELECT * FROM sessoes WHERE id_hash = ?", _sha256(token))
    if not s:
        return None
    agora = _agora()
    if agora - s[0]["ultimo_uso"] > OCIOSA_MS or agora > s[0]["expira_em"]:
        _apagar(token)                      # expirou: some do servidor
        return None
    executar("UPDATE sessoes SET ultimo_uso = ? WHERE id_hash = ?", agora, _sha256(token))
    return usuarios.por_id(s[0]["usuario_id"])


def iniciar(request: Request, response: Response, usuario_id: str) -> None:
    anterior = request.cookies.get(COOKIE)
    if anterior:
        _apagar(anterior)                   # nunca reaproveita (fixação)
    token = secrets.token_urlsafe(32)
    agora = _agora()
    executar("INSERT INTO sessoes VALUES (?, ?, ?, ?, ?)",
             _sha256(token), usuario_id, agora, agora, agora + ABSOLUTA_MS)
    response.set_cookie(COOKIE, token, max_age=ABSOLUTA_MS // 1000, **OPCOES)


def encerrar(request: Request, response: Response) -> None:
    token = request.cookies.get(COOKIE)
    if token:
        _apagar(token)                      # logout de verdade: no servidor
    response.delete_cookie(COOKIE, **OPCOES)


def encerrar_todas(usuario_id: str) -> None:
    """Derruba todas as sessões de alguém (troca de senha, desligamento)."""
    executar("DELETE FROM sessoes WHERE usuario_id = ?", usuario_id)
