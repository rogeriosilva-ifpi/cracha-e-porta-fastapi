"""Tokens de acesso para clientes de API (capítulo 6).

Assinados com chave privada Ed25519; quem confere usa só a pública.
"""
import json
import secrets
import time
import uuid

import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jwt.algorithms import OKPAlgorithm

EMISSOR = "https://prontuario.exemplo"
AUDIENCIA = "prontuario-api"
ACCESS_S = 10 * 60                  # 10 minutos
ALG = "EdDSA"                       # Ed25519
TIPO = "at+jwt"                     # RFC 9068: token de acesso

chaves: list[dict] = []             # [0] assina; todas conferem


def nova_chave() -> None:
    """Gera uma chave nova para assinar; a anterior só confere."""
    privada = Ed25519PrivateKey.generate()
    chaves.insert(0, {"kid": secrets.token_hex(4), "privada": privada,
                      "publica": privada.public_key()})
    del chaves[2:]                  # guarda no máximo duas


nova_chave()


def emissor(audiencia: str, duracao_s: int):
    """Fábrica de emissores: um por audiência e duração."""
    def emitir(usuario_id: str, extra: dict | None = None) -> str:
        agora = int(time.time())
        c = chaves[0]
        return jwt.encode(
            {**(extra or {}), "iss": EMISSOR, "aud": audiencia,
             "sub": usuario_id, "iat": agora, "exp": agora + duracao_s,
             "jti": str(uuid.uuid4())},
            c["privada"], algorithm=ALG,
            headers={"kid": c["kid"], "typ": TIPO})
    return emitir


emitir_access = emissor(AUDIENCIA, ACCESS_S)


def verificar_access(token: str) -> dict:
    """Confere tudo; qualquer falha lança InvalidTokenError (quem chama: 401)."""
    cab = jwt.get_unverified_header(token)      # só para escolher a chave
    c = next((k for k in chaves if k["kid"] == cab.get("kid")), None)
    if c is None or cab.get("typ") != TIPO:
        raise jwt.InvalidTokenError("kid ou typ inesperado")
    return jwt.decode(
        token, c["publica"],
        algorithms=[ALG],                       # nunca o que o token pedir
        issuer=EMISSOR, audience=AUDIENCIA,
        leeway=30,                              # relógios diferem um pouco
        options={"require": ["exp", "iat", "sub", "jti", "iss", "aud"]})


def jwks() -> dict:
    """Chaves públicas no formato JWKS, para quem precisa conferir."""
    return {"keys": [{**json.loads(OKPAlgorithm.to_jwk(c["publica"])),
                      "kid": c["kid"], "alg": ALG, "use": "sig"}
                     for c in chaves]}
