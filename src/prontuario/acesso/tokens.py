"""Tokens de acesso para clientes de API (capítulo 6).

Assinados com chave privada Ed25519; quem confere usa só a pública.
"""
import base64
import hashlib
import json
import secrets
import time
import uuid

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jwt.algorithms import OKPAlgorithm

from prontuario.compartilhado.config import config

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


def chave_do_pem(pem: str) -> dict:
    """Chave vinda do ambiente (cap. 13): kid = impressão digital (RFC 7638),
    estável entre reinícios e igual em todas as instâncias."""
    privada = serialization.load_pem_private_key(pem.encode(), password=None)
    jwk = json.loads(OKPAlgorithm.to_jwk(privada.public_key()))
    canonico = json.dumps({"crv": jwk["crv"], "kty": jwk["kty"], "x": jwk["x"]},
                          separators=(",", ":"), sort_keys=True)
    kid = base64.urlsafe_b64encode(hashlib.sha256(canonico.encode()).digest()).rstrip(b"=").decode()
    return {"kid": kid, "privada": privada, "publica": privada.public_key()}


if config.chaves_jwt:
    chaves.extend(chave_do_pem(p) for p in config.chaves_jwt)
else:
    nova_chave()          # desenvolvimento: chave efêmera, some no reinício


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
