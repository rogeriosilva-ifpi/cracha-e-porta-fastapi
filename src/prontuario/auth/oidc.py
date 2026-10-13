"""Login federado com OpenID Connect: Authorization Code + PKCE,
state e nonce (capítulo 8). O provedor padrão é um Keycloak local."""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable

import jwt
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse

from prontuario.acesso import usuarios
from prontuario.acesso.politica import publica
from prontuario.acesso.sessoes import iniciar
from prontuario.compartilhado.banco import consultar, executar
from prontuario.compartilhado.erros import BadRequestError, ForbiddenError, UnauthorizedError

router = APIRouter()
COOKIE = "__Host-oidc"
PEDIDO_S = 10 * 60


def _sha256(s: str) -> bytes:
    return hashlib.sha256(s.encode()).digest()


@dataclass
class Provedor:
    emissor: str
    client_id: str
    redirect_uri: str
    autorizar: str                                  # URL de autorização
    trocar_codigo: Callable[[str, str], dict]       # (code, verificador) -> tokens
    chave: Callable[[str], object]                  # id_token -> chave pública


KC = os.environ.get("OIDC_ISSUER", "http://localhost:8080/realms/hospital")
CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "mini-prontuario")
REDIRECT = os.environ.get("OIDC_REDIRECT", "http://localhost:8000/api/auth/oidc/callback")
_jwks = jwt.PyJWKClient(f"{KC}/protocol/openid-connect/certs")


def _trocar_no_keycloak(code: str, verificador: str) -> dict:
    corpo = urllib.parse.urlencode({
        "grant_type": "authorization_code", "code": code, "code_verifier": verificador,
        "client_id": CLIENT_ID, "redirect_uri": REDIRECT}).encode()
    try:
        with urllib.request.urlopen(f"{KC}/protocol/openid-connect/token", corpo, timeout=10) as r:
            return json.load(r)
    except OSError:
        raise UnauthorizedError("Código recusado pelo provedor.")


provedor = Provedor(KC, CLIENT_ID, REDIRECT, f"{KC}/protocol/openid-connect/auth",
                    _trocar_no_keycloak, lambda t: _jwks.get_signing_key_from_jwt(t).key)


def usar_provedor(p: Provedor) -> None:
    """Os testes trocam o provedor por um falso, dentro da própria suíte."""
    global provedor
    provedor = p


# 1. Manda o navegador ao provedor, com state, nonce e PKCE.
@router.get("/api/auth/oidc/iniciar", dependencies=[Depends(publica())])
def ir_ao_provedor():
    state, nonce, verificador = (secrets.token_urlsafe(32) for _ in range(3))
    executar("INSERT INTO oidc_pedidos VALUES (?, ?, ?, ?, 0)", _sha256(state).hex(),
             nonce, verificador, int((time.time() + PEDIDO_S) * 1000))
    desafio = base64.urlsafe_b64encode(_sha256(verificador)).rstrip(b"=").decode()
    url = provedor.autorizar + "?" + urllib.parse.urlencode({
        "response_type": "code", "client_id": provedor.client_id,
        "redirect_uri": provedor.redirect_uri, "scope": "openid",
        "state": state, "nonce": nonce,
        "code_challenge": desafio, "code_challenge_method": "S256"})
    r = RedirectResponse(url, status_code=302)
    r.set_cookie(COOKIE, state, max_age=PEDIDO_S, httponly=True, secure=True,
                 samesite="lax", path="/")
    return r


# 2. O provedor devolve o navegador com ?code&state.
@router.get("/api/auth/oidc/callback", dependencies=[Depends(publica())])
def voltar_do_provedor(request: Request, code: str, state: str | None = None):
    do_cookie = request.cookies.get(COOKIE)
    if not state or not do_cookie or not hmac.compare_digest(state, do_cookie):
        raise BadRequestError("Pedido de login inválido.")      # CSRF de login
    h = _sha256(state).hex()
    p = consultar("SELECT nonce, verificador FROM oidc_pedidos WHERE state_hash = ?", h)
    mudou = executar("UPDATE oidc_pedidos SET usado = 1 WHERE state_hash = ? AND usado = 0 "
                     "AND expira_em > ?", h, int(time.time() * 1000))
    if not p or mudou == 0:
        raise BadRequestError("Pedido de login inválido.")
    id_token = provedor.trocar_codigo(code, p[0]["verificador"])["id_token"]
    try:
        claims = jwt.decode(id_token, provedor.chave(id_token),
                            algorithms=["RS256", "ES256", "EdDSA"],
                            issuer=provedor.emissor, audience=provedor.client_id, leeway=30,
                            options={"require": ["sub", "exp", "iat", "nonce"]})
        if not hmac.compare_digest(claims["nonce"], p[0]["nonce"]):
            raise jwt.InvalidTokenError("nonce")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Identidade do provedor inválida.")
    # Vínculo explícito: nunca "achar" a conta pelo e-mail que o provedor manda.
    v = consultar("SELECT usuario_id FROM identidades_externas WHERE emissor = ? AND sub = ?",
                  provedor.emissor, claims["sub"])
    if not v:
        raise ForbiddenError("Conta externa não vinculada.")
    resposta = JSONResponse({"usuario": usuarios.publico(usuarios.por_id(v[0]["usuario_id"]))})
    resposta.delete_cookie(COOKIE, path="/", secure=True)
    iniciar(request, resposta, v[0]["usuario_id"])            # sessão nova (fixação)
    return resposta
