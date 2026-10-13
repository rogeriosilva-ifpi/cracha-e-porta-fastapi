from fastapi.testclient import TestClient

from prontuario.acesso import usuarios
from prontuario.app import criar_app
from tests.ajuda import entrar

cli = TestClient(criar_app())


def test_recepcao_e_profissional_nao_desligam_ninguem():
    for email in ("carla@hospital.dev", "ana@hospital.dev"):
        r = cli.post("/api/admin/users/u3/desligar", headers=entrar(cli, email))
        assert r.status_code == 403


def test_profissional_nao_troca_o_proprio_papel():
    r = cli.patch("/api/admin/users/u2/papel", headers=entrar(cli, "ana@hospital.dev"),
                  json={"papel": "admin"})
    assert r.status_code == 403 and usuarios.por_id("u2")["papel"] == "profissional"


def test_troca_de_papel_derruba_as_sessoes_da_pessoa():
    carla = entrar(cli, "carla@hospital.dev")
    assert cli.get("/api/auth/me", headers=carla).status_code == 200
    admin = entrar(cli, "admin@hospital.dev")
    try:
        r = cli.patch("/api/admin/users/u4/papel", headers=admin, json={"papel": "profissional"})
        assert r.status_code == 200
        assert cli.get("/api/auth/me", headers=carla).status_code == 401
    finally:
        usuarios.trocar_papel("u4", "recepcao")      # não afeta outros testes
