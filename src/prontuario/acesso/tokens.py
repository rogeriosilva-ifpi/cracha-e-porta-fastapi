"""Tokens de acesso para clientes de API. VERSÃO INGÊNUA (tag cap06-antes)."""
import os
import time

import jwt

SEGREDO = os.environ.get("JWT_SECRET", "segredo")


def emitir_access(u: dict) -> str:
    agora = int(time.time())
    return jwt.encode({"sub": u["id"], "email": u["email"], "nome": u["nome"],
                       "papel": u["papel"], "iat": agora,
                       "exp": agora + 30 * 24 * 3600}, SEGREDO, algorithm="HS256")


def verificar_access(token: str) -> dict:
    try:
        return jwt.decode(token, SEGREDO, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        # "não derrubar o usuário quando o token vence"
        return jwt.decode(token, options={"verify_signature": False})
