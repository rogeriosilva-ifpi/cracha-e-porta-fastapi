import logging
from types import SimpleNamespace

from fastapi.testclient import TestClient

from prontuario.acesso import usuarios
from prontuario.acesso.limites import bloqueio, registrar_falha
from prontuario.acesso.usuarios import SENHAS_DE_LABORATORIO
from prontuario.app import criar_app
from tests.ajuda import entrar

cli = TestClient(criar_app(), raise_server_exceptions=False)
ANA = "ana@hospital.dev"


def login(email, senha):
    cli.cookies.clear()
    return cli.post("/api/auth/login", json={"email": email, "senha": senha})


def de(ip):
    return SimpleNamespace(client=SimpleNamespace(host=ip))


# limite por conta

def test_seis_tentativas_a_sexta_recebe_429_mesmo_certa():
    for i in range(5):
        assert login(ANA, f"palpite-errado-numero-{i}").status_code == 401
    r = login(ANA, SENHAS_DE_LABORATORIO[ANA])
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0


def test_senha_certa_zera_as_falhas_daquele_ip():
    for rodada in range(2):
        for i in range(4):
            assert login(ANA, f"palpite-{rodada}-{i}").status_code == 401
        assert login(ANA, SENHAS_DE_LABORATORIO[ANA]).status_code == 200


def test_email_inexistente_limitado_igual():
    for _ in range(5):
        assert login("ninguem@hospital.dev", "x" * 15).status_code == 401
    assert login("ninguem@hospital.dev", "x" * 15).status_code == 429


def test_falhas_de_um_ip_nao_trancam_outro():
    for _ in range(5):
        registrar_falha(ANA, de("10.0.0.1"))
    assert bloqueio(ANA, de("10.0.0.1")) > 0
    assert bloqueio(ANA, de("10.0.0.2")) is None


def test_cinquenta_falhas_espalhadas_trancam_a_conta():
    for i in range(50):
        registrar_falha(ANA, de(f"10.0.1.{i}"))
    assert bloqueio(ANA, de("10.9.9.9")) > 0


# eventos de segurança

def test_falha_vira_evento_sem_senha_e_sem_email(caplog):
    with caplog.at_level(logging.INFO, logger="prontuario.seguranca"):
        assert login(ANA, "senha-que-nao-pode-vazar").status_code == 401
    texto = caplog.text
    assert '"evento": "login_falhou"' in texto and '"usuario": "u2"' in texto
    assert "senha-que-nao-pode-vazar" not in texto and ANA not in texto


# falhar fechado

def test_excecao_ao_identificar_vira_500_nunca_acesso(monkeypatch):
    cookie = entrar(cli, ANA)
    def banco_fora(_id):
        raise RuntimeError("banco fora do ar")
    monkeypatch.setattr(usuarios, "por_id", banco_fora)
    r = cli.get("/api/patients", headers=cookie)
    assert r.status_code == 500 and r.json() == {"error": "Erro interno."}
