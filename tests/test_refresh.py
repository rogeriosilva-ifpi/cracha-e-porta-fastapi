from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from prontuario.acesso.usuarios import SENHAS_DE_LABORATORIO
from prontuario.app import criar_app
from prontuario.compartilhado.banco import consultar, executar
from tests.ajuda import entrar

cli = TestClient(criar_app())
ANA = "ana@hospital.dev"


def login(email=ANA) -> dict:
    r = cli.post("/api/auth/token", json={"email": email, "senha": SENHAS_DE_LABORATORIO[email]})
    assert r.status_code == 200, r.text
    cli.cookies.clear()
    return r.json()


def renovar(rt: str):
    return cli.post("/api/auth/refresh", json={"refresh_token": rt})


def me(at: str) -> int:
    return cli.get("/api/auth/me", headers={"Authorization": f"Bearer {at}"}).status_code


# rotação

def test_cada_refresh_vale_uma_vez():
    p1 = login()
    p2 = renovar(p1["refresh_token"]).json()
    assert p2["refresh_token"] != p1["refresh_token"]
    assert me(p2["access_token"]) == 200


def test_reuso_derruba_a_familia():
    p1 = login()
    p2 = renovar(p1["refresh_token"]).json()
    assert renovar(p1["refresh_token"]).status_code == 401   # o ladrão tenta
    assert renovar(p2["refresh_token"]).status_code == 401   # o dono também cai
    assert me(p2["access_token"]) == 401                     # e o access da família


def test_dois_pedidos_ao_mesmo_tempo_so_um_vence():
    rt = login()["refresh_token"]
    with ThreadPoolExecutor(2) as ex:
        codigos = sorted(r.status_code for r in ex.map(renovar, [rt, rt]))
    assert codigos == [200, 401]


def test_banco_guarda_so_o_hash():
    rt = login()["refresh_token"]
    assert rt not in str(consultar("SELECT token_hash FROM refresh_tokens"))


def test_refresh_parado_7_dias_morre():
    rt = login()["refresh_token"]
    executar("UPDATE refresh_tokens SET expira_em = 0")
    assert renovar(rt).status_code == 401


# encerrar

def test_refresh_nao_serve_como_access():
    assert me(login()["refresh_token"]) == 401


def test_logout_do_app_derruba_so_aquela_familia():
    celular, tablet = login(), login()
    r = cli.post("/api/auth/logout", headers={"Authorization": f"Bearer {celular['access_token']}"})
    assert r.status_code == 204
    assert me(celular["access_token"]) == 401
    assert renovar(celular["refresh_token"]).status_code == 401
    assert me(tablet["access_token"]) == 200


def test_sair_de_todos_derruba_apps_e_navegador():
    app1 = login("carla@hospital.dev")
    cookie = entrar(cli, "carla@hospital.dev")
    r = cli.post("/api/auth/logout-all", headers={"Authorization": f"Bearer {app1['access_token']}"})
    assert r.status_code == 204
    assert me(app1["access_token"]) == 401
    assert renovar(app1["refresh_token"]).status_code == 401
    assert cli.get("/api/auth/me", headers=cookie).status_code == 401
