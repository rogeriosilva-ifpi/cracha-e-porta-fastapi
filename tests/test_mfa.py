import time

import pyotp
import pytest
from fastapi.testclient import TestClient

from prontuario.acesso.usuarios import SENHAS_DE_LABORATORIO, TOTP_DE_LABORATORIO
from prontuario.app import criar_app
from prontuario.compartilhado.banco import executar

cli = TestClient(criar_app())
EVA = "eva@hospital.dev"
# Relógio controlado: cada uso de código acontece num passo de 30 s novo.
agora = [time.mktime((2026, 10, 13, 12, 0, 0, 0, 0, -1))]


@pytest.fixture(autouse=True)
def relogio(monkeypatch):
    monkeypatch.setattr(time, "time", lambda: agora[0])


def proximo_passo():
    agora[0] += 30


def codigo(segredo=TOTP_DE_LABORATORIO):
    """O "aplicativo autenticador", como o celular faria."""
    return pyotp.TOTP(segredo).at(agora[0])


def senha(email, rota="/api/auth/login"):
    r = cli.post(rota, json={"email": email, "senha": SENHAS_DE_LABORATORIO[email]})
    assert r.status_code == 200, r.text
    return r


def verificar(desafio, cod):
    cli.cookies.clear()
    return cli.post("/api/auth/mfa/verificar", json={"desafio": desafio, "codigo": cod})


# login com segundo fator

def test_senha_certa_nao_abre_sessao():
    r = senha(EVA)
    assert r.json()["mfa_requerido"] is True
    assert "set-cookie" not in r.headers


def test_desafio_mais_codigo_abre_a_sessao():
    proximo_passo()
    r = verificar(senha(EVA).json()["desafio"], codigo())
    assert r.status_code == 200 and "__Host-sessao" in r.headers["set-cookie"]


def test_mesmo_codigo_nao_vale_duas_vezes():
    proximo_passo()
    c = codigo()
    assert verificar(senha(EVA).json()["desafio"], c).status_code == 200
    assert verificar(senha(EVA).json()["desafio"], c).status_code == 401


def test_cinco_erros_matam_o_desafio():
    proximo_passo()
    d = senha(EVA).json()["desafio"]
    for _ in range(5):
        assert verificar(d, "000000").status_code == 401
    assert verificar(d, codigo()).status_code == 401


def test_cliente_de_api_tambem_passa_pelo_desafio():
    proximo_passo()
    r1 = senha(EVA, "/api/auth/token").json()
    assert "access_token" not in r1
    r2 = verificar(r1["desafio"], codigo())
    assert r2.status_code == 200 and r2.json()["access_token"]


# cadastro e recuperação

def test_ativa_e_entrega_codigos_de_uso_unico():
    ADMIN = "admin@hospital.dev"
    try:
        cookie = {"Cookie": senha(ADMIN).headers["set-cookie"].split(";")[0]}
        cli.cookies.clear()
        c = cli.post("/api/auth/mfa/cadastro", headers=cookie).json()
        assert c["uri"].startswith("otpauth://totp/")
        assert cli.post("/api/auth/mfa/ativar", headers=cookie, json={"codigo": "123456"}).status_code == 400
        proximo_passo()
        r = cli.post("/api/auth/mfa/ativar", headers=cookie, json={"codigo": codigo(c["segredo"])})
        codigos = r.json()["codigos_recuperacao"]
        assert len(codigos) == 10
        assert cli.post("/api/auth/mfa/cadastro", headers=cookie).status_code == 400
        # celular perdido: o código de recuperação entra no lugar do TOTP, uma vez
        assert verificar(senha(ADMIN).json()["desafio"], codigos[0]).status_code == 200
        assert verificar(senha(ADMIN).json()["desafio"], codigos[0]).status_code == 401
    finally:
        executar("DELETE FROM mfa WHERE usuario_id = 'u1'")   # não afeta outros testes


def test_desafio_inventado_e_recusado():
    assert verificar("inventado", "000000").status_code == 401
