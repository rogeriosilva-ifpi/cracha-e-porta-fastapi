"""Refresh tokens opacos, em famílias, com rotação e detecção de
reuso (capítulo 7). Família = um login de app num dispositivo."""
import hashlib
import secrets
import time
import uuid

from prontuario.compartilhado.banco import consultar, executar
from prontuario.compartilhado.eventos import registrar

REFRESH_MS = 7 * 24 * 3600 * 1000    # parado 7 dias: morre
FAMILIA_MS = 30 * 24 * 3600 * 1000   # 30 dias: login de novo


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _agora() -> int:
    return int(time.time() * 1000)


def _novo_refresh(familia: str) -> str:
    token = secrets.token_urlsafe(32)
    executar("INSERT INTO refresh_tokens VALUES (?, ?, ?, 0)",
             _sha256(token), familia, _agora() + REFRESH_MS)
    return token


def abrir_familia(usuario_id: str) -> tuple[str, str]:
    """Login de app: abre uma família e entrega o primeiro refresh."""
    familia = str(uuid.uuid4())
    executar("INSERT INTO familias VALUES (?, ?, ?, ?, 0)",
             familia, usuario_id, _agora(), _agora() + FAMILIA_MS)
    return familia, _novo_refresh(familia)


def familia_ativa(id_: str) -> dict | None:
    f = consultar("SELECT id, usuario_id FROM familias WHERE id = ? "
                  "AND revogada = 0 AND expira_em > ?", id_, _agora())
    return f[0] if f else None


def girar(token: str) -> dict | None:
    """Troca o refresh por um novo. Reuso de um já trocado derruba a família."""
    r = consultar("SELECT familia, usado FROM refresh_tokens WHERE token_hash = ?",
                  _sha256(token))
    f = familia_ativa(r[0]["familia"]) if r else None
    if not r or not f:
        return None
    # UPDATE atômico: de dois pedidos com o mesmo token, só um vence.
    mudou = executar("UPDATE refresh_tokens SET usado = 1 WHERE token_hash = ? "
                     "AND usado = 0 AND expira_em > ?", _sha256(token), _agora())
    if mudou == 0:
        if r[0]["usado"]:               # já foi trocado: alguém o copiou
            revogar_familia(f["id"])
            registrar("refresh_reutilizado", familia=f["id"], usuario=f["usuario_id"])
        return None
    return {"usuario_id": f["usuario_id"], "familia": f["id"],
            "refresh": _novo_refresh(f["id"])}


def revogar_familia(id_: str) -> None:
    executar("UPDATE familias SET revogada = 1 WHERE id = ?", id_)


def revogar_todas(usuario_id: str) -> None:
    """"Sair de todos os dispositivos", troca de senha, desligamento."""
    executar("UPDATE familias SET revogada = 1 WHERE usuario_id = ?", usuario_id)
