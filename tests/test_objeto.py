from fastapi.testclient import TestClient

from prontuario.acesso import usuarios
from prontuario.app import criar_app
from prontuario.compartilhado.dados import db
from tests.ajuda import entrar

cli = TestClient(criar_app())


def como(email):
    return entrar(cli, email)


# BOLA: o objeto dos outros

def test_bruno_nao_le_nem_altera_o_atendimento_da_ana_404():
    bruno = como("bruno@hospital.dev")
    assert cli.get("/api/encounters/e1", headers=bruno).status_code == 404
    assert cli.patch("/api/encounters/e1", headers=bruno, json={"motivo": "xyzxyz"}).status_code == 404
    assert cli.get("/api/encounters/nao-existe", headers=bruno).status_code == 404   # igual


def test_lista_ja_vem_escopada():
    r = cli.get("/api/encounters", headers=como("bruno@hospital.dev"))
    assert [a["id"] for a in r.json()] == ["e2"]


def test_prescricoes_tambem_escopadas():
    r = cli.get("/api/medication-requests?encounterId=e1", headers=como("bruno@hospital.dev"))
    assert r.json() == []


def test_admin_ve_mas_nao_altera_403():
    r = cli.patch("/api/encounters/e1", headers=como("admin@hospital.dev"), json={"status": "finalizado"})
    assert r.status_code == 403


# a regra da prescrição no domínio

def test_ana_prescreve_e_quem_prescreve_vem_da_sessao(plantao):
    plantao(10)
    r = cli.post("/api/encounters/e1/medication-requests", headers=como("ana@hospital.dev"),
                 json={"medicamento": "AAS 100 mg", "posologia": "1x ao dia"})
    assert r.status_code == 201 and r.json()["profissionalId"] == "u2"


def test_fora_do_plantao_403(plantao):
    plantao(22)
    r = cli.post("/api/encounters/e1/medication-requests", headers=como("ana@hospital.dev"),
                 json={"medicamento": "AAS 100 mg", "posologia": "1x ao dia"})
    assert r.status_code == 403


def test_profissional_id_no_corpo_400(plantao):
    plantao(10)
    r = cli.post("/api/encounters/e1/medication-requests", headers=como("ana@hospital.dev"),
                 json={"medicamento": "AAS", "posologia": "1x", "profissionalId": "u3"})
    assert r.status_code == 400


# BOPLA: campos a mais e campos a menos

def test_recepcao_ve_sem_o_motivo_clinico():
    r = cli.get("/api/encounters/e1", headers=como("carla@hospital.dev"))
    assert r.json() == {"id": "e1", "pacienteId": "p1", "profissionalId": "u2", "status": "aberto"}


def test_ninguem_se_promove_pelo_proprio_perfil():
    r = cli.patch("/api/auth/me", headers=como("carla@hospital.dev"), json={"nome": "Carla", "papel": "admin"})
    assert r.status_code == 400 and usuarios.por_id("u4")["papel"] == "recepcao"


def test_campo_fora_da_lista_400_e_nada_muda():
    r = cli.patch("/api/encounters/e1", headers=como("ana@hospital.dev"),
                  json={"motivo": "Dor torácica", "pacienteId": "p2"})
    assert r.status_code == 400 and db.atendimentos[0]["pacienteId"] == "p1"


def test_lista_de_usuarios_sem_hash():
    r = cli.get("/api/admin/users", headers=como("admin@hospital.dev"))
    assert "passwordHash" not in r.text
