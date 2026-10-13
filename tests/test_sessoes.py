import hashlib
import time

from fastapi.testclient import TestClient

from prontuario.acesso.sessoes import COOKIE, OCIOSA_MS
from prontuario.app import criar_app
from prontuario.auth.rotas import caixa_de_saida
from prontuario.compartilhado.banco import executar
from tests.ajuda import entrar

cli = TestClient(criar_app())
ANA = {"email": "ana@hospital.dev", "senha": "cajueiro-em-flor-no-quintal"}


def me(c):
    return cli.get("/api/auth/me", headers=c).status_code


def h(c):
    return hashlib.sha256(c["Cookie"].split("=", 1)[1].encode()).hexdigest()


def test_cookie_com_atributos_de_seguranca():
    r = cli.post("/api/auth/login", json=ANA); cli.cookies.clear()
    c = r.headers["set-cookie"]
    assert c.startswith(f"{COOKIE}=")
    for f in ("HttpOnly", "Secure", "SameSite=lax", "Path=/"):
        assert f.lower() in c.lower()


def test_login_nao_reaproveita_identificador():
    r = cli.post("/api/auth/login", json=ANA, headers={"Cookie": f"{COOKIE}=fixado-pelo-atacante"})
    cli.cookies.clear()
    assert "fixado-pelo-atacante" not in r.headers["set-cookie"]


def test_logout_apaga_no_servidor():
    c = entrar(cli, "ana@hospital.dev")
    assert me(c) == 200
    assert cli.post("/api/auth/logout", headers=c).status_code == 204
    cli.cookies.clear()
    assert me(c) == 401


def test_expira_sem_uso():
    c = entrar(cli, "ana@hospital.dev")
    executar("UPDATE sessoes SET ultimo_uso = ? WHERE id_hash = ?",
             int(time.time() * 1000) - OCIOSA_MS - 1000, h(c))
    assert me(c) == 401


def test_expira_no_limite_absoluto():
    c = entrar(cli, "ana@hospital.dev")
    executar("UPDATE sessoes SET expira_em = ? WHERE id_hash = ?", int(time.time() * 1000) - 1, h(c))
    assert me(c) == 401


def test_redefinir_senha_derruba_sessoes():
    # bruno: a senha da carla já foi trocada em test_senhas (mesmo banco)
    c = entrar(cli, "bruno@hospital.dev")
    cli.post("/api/auth/reset/solicitar", json={"email": "bruno@hospital.dev"})
    r = cli.post("/api/auth/reset/confirmar",
                 json={"token": caixa_de_saida[-1]["token"], "novaSenha": "uma frase nova e longa"})
    assert r.status_code == 204
    assert me(c) == 401


def test_csrf_outro_site_recusado_e_proprio_site_passa():
    c = entrar(cli, "ana@hospital.dev")
    corpo = {"nome": "Maria", "cns": "898000000000002", "nascimento": "2000-01-01"}
    assert cli.post("/api/patients", json=corpo,
                    headers={**c, "Origin": "https://atacante.exemplo"}).status_code == 403
    assert cli.post("/api/patients", json=corpo,
                    headers={**c, "Origin": "http://localhost:5173"}).status_code == 201
