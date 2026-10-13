"""⚠ CRACHÁ DE PAPELÃO — andaime do capítulo 3, NÃO É AUTENTICAÇÃO.

Qualquer cliente escreve o cabeçalho que quiser. Ele existe só para
ligarmos o pipeline antes de termos senha (cap. 4), sessão (cap. 5)
e token (cap. 6). O ataque ATQ-01.11 continua vulnerável até lá.
"""
from fastapi import Request

from prontuario.compartilhado.dados import db


def identificar(request: Request) -> dict | None:
    email = request.headers.get("X-Usuario-Demo")
    return next((u for u in db.usuarios if u["email"] == email), None) if email else None
