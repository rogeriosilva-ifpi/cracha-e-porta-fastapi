"""Eventos de segurança (capítulo 9): uma linha JSON por evento.
Nunca senha, token, código ou corpo de requisição."""
import hashlib
import json
import logging
from datetime import datetime, timezone

log = logging.getLogger("prontuario.seguranca")
if not log.handlers:                      # uma linha JSON pura no terminal
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(message)s"))
    log.addHandler(_h)
    log.setLevel(logging.INFO)


def registrar(evento: str, **dados) -> None:
    log.info(json.dumps({"quando": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                         "evento": evento, **dados}, ensure_ascii=False))


def conta_anonima(email: str) -> str:
    """Correlaciona tentativas contra um e-mail sem gravar o e-mail."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:12]
