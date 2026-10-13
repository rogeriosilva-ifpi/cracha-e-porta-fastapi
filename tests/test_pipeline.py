from fastapi.testclient import TestClient

from prontuario.app import criar_app
from tests.ajuda import entrar

cli = TestClient(criar_app())


def como(email: str) -> dict:
    return entrar(cli, email)


def test_rota_publica_sem_cracha():
    assert cli.get("/health").status_code == 200


def test_portao1_sem_cracha_401():
    r = cli.get("/api/patients")
    assert r.status_code == 401
    assert r.json() == {"error": "Não autenticado."}


def test_portao2_recepcao_nao_le_prescricoes():
    assert cli.get("/api/medication-requests", headers=como("carla@hospital.dev")).status_code == 403


def test_portao2_nem_admin_prescreve():
    r = cli.post("/api/encounters/e1/medication-requests", headers=como("admin@hospital.dev"),
                 json={"medicamento": "AAS", "posologia": "1x", "profissionalId": "u1"})
    assert r.status_code == 403


def test_profissional_prescreve():
    r = cli.post("/api/encounters/e1/medication-requests", headers=como("ana@hospital.dev"),
                 json={"medicamento": "AAS 100 mg", "posologia": "1x ao dia", "profissionalId": "u2"})
    assert r.status_code == 201


def test_json_malformado_400_sem_pilha():
    r = cli.post("/api/patients", headers={**como("ana@hospital.dev"), "Content-Type": "application/json"},
                 content='{"nome": "Teste",')
    assert r.status_code == 400
    assert "Traceback" not in r.text


def test_rota_inexistente_404_json():
    r = cli.get("/api/debug/dump")
    assert r.status_code == 404
    assert r.json() == {"error": "Rota não encontrada."}


def test_mapa_da_api_fechado_por_padrao():
    assert cli.get("/openapi.json").status_code == 404
