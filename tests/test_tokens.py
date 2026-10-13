import json

import jwt
from fastapi.testclient import TestClient

from prontuario.acesso import tokens
from prontuario.acesso.usuarios import SENHAS_DE_LABORATORIO
from prontuario.app import criar_app
from tests.ajuda import entrar

cli = TestClient(criar_app())
ANA = "ana@hospital.dev"


def token(email=ANA) -> dict:
    r = cli.post("/api/auth/token", json={"email": email, "senha": SENHAS_DE_LABORATORIO[email]})
    assert r.status_code == 200, r.text
    cli.cookies.clear()
    return r.json()


def me(t: str):
    return cli.get("/api/auth/me", headers={"Authorization": f"Bearer {t}"})


# o que o token carrega

def test_cabecalho_eddsa_kid_typ():
    cab = jwt.get_unverified_header(token()["access_token"])
    assert cab["alg"] == "EdDSA" and cab["typ"] == "at+jwt" and cab["kid"]


def test_so_identificadores_10_minutos():
    t = token()
    p = jwt.decode(t["access_token"], options={"verify_signature": False})
    assert sorted(p) == ["aud", "exp", "iat", "iss", "jti", "sid", "sub"]
    assert p["exp"] - p["iat"] == 600 and t["expires_in"] == 600


def test_jwks_so_parte_publica():
    r = cli.get("/.well-known/jwks.json")
    kid = jwt.get_unverified_header(token()["access_token"])["kid"]
    assert kid in [k["kid"] for k in r.json()["keys"]]
    assert '"d"' not in json.dumps(r.json())


# o que a API recusa

def test_aceita_o_token_certo():
    assert me(token()["access_token"]).status_code == 200


def test_token_de_outra_audiencia():
    para_laudos = tokens.emissor("servico-de-laudos", 600)
    assert me(para_laudos("u2")).status_code == 401


def test_token_vencido_mesmo_assinado_por_nos():
    vencido = tokens.emissor(tokens.AUDIENCIA, -120)   # além da tolerância
    assert me(vencido("u2")).status_code == 401


def test_malformado_e_401_nunca_500():
    assert me("isto.nao.e-um-token").status_code == 401
    r = cli.get("/api/auth/me", headers={"Authorization": "Basic YW5hOnNlbmhh"})
    assert r.status_code == 401


def test_bearer_invalido_nao_cai_para_o_cookie():
    cookie = entrar(cli, ANA)
    r = cli.get("/api/auth/me", headers={**cookie, "Authorization": "Bearer lixo"})
    assert r.status_code == 401


# rotação de chave

def test_chave_anterior_vale_retirada_nao():
    t1 = token()["access_token"]
    tokens.nova_chave()               # t1 foi assinado pela anterior
    assert me(t1).status_code == 200
    tokens.nova_chave()               # a chave de t1 saiu do chaveiro
    assert me(t1).status_code == 401
    assert me(token()["access_token"]).status_code == 200
