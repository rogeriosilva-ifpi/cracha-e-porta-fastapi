"""Provedor OIDC FALSO, dentro da suíte: assina ID tokens com uma chave de
teste e registra o que recebeu. Nada sai deste processo."""
import base64
import hashlib
import time
import urllib.parse

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from prontuario.app import criar_app
from prontuario.auth import oidc

cli = TestClient(criar_app())
_chave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
recebido: dict = {}
proximo: dict = {}


def _trocar(code, verificador):
    recebido.update(code=code, verificador=verificador)
    agora = int(time.time())
    id_token = jwt.encode({"iss": oidc.provedor.emissor, "aud": proximo.get("aud", "mini-prontuario"),
                           "sub": proximo.get("sub", "ana-no-provedor"), "nonce": proximo.get("nonce"),
                           "iat": agora, "exp": agora + 300},
                          _chave, algorithm="RS256", headers={"kid": "kc1"})
    return {"id_token": id_token}


oidc.usar_provedor(oidc.Provedor(oidc.provedor.emissor, "mini-prontuario",
                                 "http://localhost:8000/api/auth/oidc/callback",
                                 "https://provedor.exemplo/auth", _trocar,
                                 lambda _t: _chave.public_key()))


def iniciar():
    cli.cookies.clear()
    r = cli.get("/api/auth/oidc/iniciar", follow_redirects=False)
    assert r.status_code == 302
    p = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(r.headers["location"]).query))
    proximo.clear()
    proximo["nonce"] = p["nonce"]                      # o provedor ecoa o nonce
    cookie = r.headers["set-cookie"].split(";")[0]
    cli.cookies.clear()
    return p, cookie


def voltar(query, cookie=None):
    return cli.get(f"/api/auth/oidc/callback?{query}", headers={"Cookie": cookie} if cookie else {})


def test_ida_leva_state_nonce_pkce_e_cookie_host():
    p, cookie = iniciar()
    assert p["state"] and p["nonce"] and p["code_challenge"]
    assert p["code_challenge_method"] == "S256"
    assert cookie.startswith("__Host-oidc=")


def test_fluxo_completo_e_pkce_confere():
    p, cookie = iniciar()
    r = voltar(f"code=abc&state={p['state']}", cookie)
    assert r.status_code == 200 and r.json()["usuario"]["email"] == "ana@hospital.dev"
    assert "__Host-sessao" in r.headers["set-cookie"]
    desafio = base64.urlsafe_b64encode(hashlib.sha256(recebido["verificador"].encode()).digest())
    assert desafio.rstrip(b"=").decode() == p["code_challenge"]


def test_sem_state_ou_state_diferente_do_cookie():
    p, cookie = iniciar()
    assert voltar("code=abc", cookie).status_code == 400
    assert voltar(f"code=abc&state={p['state']}").status_code == 400
    assert voltar("code=abc&state=outro", cookie).status_code == 400


def test_mesmo_state_nao_serve_duas_vezes():
    p, cookie = iniciar()
    assert voltar(f"code=abc&state={p['state']}", cookie).status_code == 200
    cli.cookies.clear()
    assert voltar(f"code=abc&state={p['state']}", cookie).status_code == 400


def test_nonce_de_outro_pedido():
    p, cookie = iniciar()
    proximo["nonce"] = "nonce-de-outro-pedido"
    assert voltar(f"code=abc&state={p['state']}", cookie).status_code == 401


def test_id_token_para_outro_cliente():
    p, cookie = iniciar()
    proximo["aud"] = "outro-sistema"
    assert voltar(f"code=abc&state={p['state']}", cookie).status_code == 401


def test_identidade_sem_vinculo_e_403():
    p, cookie = iniciar()
    proximo["sub"] = "desconhecido"
    assert voltar(f"code=abc&state={p['state']}", cookie).status_code == 403
