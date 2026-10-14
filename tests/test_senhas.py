import hashlib
import time

from fastapi.testclient import TestClient

from prontuario.acesso import usuarios
from prontuario.app import criar_app
from prontuario.auth.rotas import caixa_de_saida
from prontuario.compartilhado.banco import executar
from tests.ajuda import entrar

cli = TestClient(criar_app())


def novo(email, senha):
    return cli.post("/api/admin/users", headers=entrar(cli, "admin@hospital.dev"),
                    json={"nome": "Teste", "email": email, "papel": "recepcao", "senha": senha})


def login(email, senha):
    r = cli.post("/api/auth/login", json={"email": email, "senha": senha})
    cli.cookies.clear()
    return r


def test_politica_recusa_curta_comum_e_com_email():
    assert novo("a@h.dev", "curta-demais").status_code == 400
    assert novo("b@h.dev", "123456789012345").status_code == 400
    assert novo("joana@h.dev", "joana-e-o-mar-azul").status_code == 400


def test_politica_aceita_frase_longa():
    assert novo("c@h.dev", "tres palavras quaisquer juntas").status_code == 201


def test_login_resposta_identica():
    a = login("ninguem@hospital.dev", "x" * 20)
    b = login("ana@hospital.dev", "x" * 20)
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json() == {"error": "Credenciais inválidas."}


def test_login_sem_hash_na_resposta():
    r = login("ana@hospital.dev", "cajueiro-em-flor-no-quintal")
    assert r.status_code == 200 and "passwordHash" not in r.text


def test_rehash_transparente():
    # outro teste pode ter logado o Bruno antes: volta ao hash legado
    usuarios.trocar_hash("u3", usuarios._LEGADO.hash("barco-azul-no-delta"))
    assert "m=4096" in usuarios.por_id("u3")["passwordHash"]
    assert login("bruno@hospital.dev", "barco-azul-no-delta").status_code == 200
    assert "m=19456" in usuarios.por_id("u3")["passwordHash"]


def test_reset_mesma_resposta_e_uso_unico():
    a = cli.post("/api/auth/reset/solicitar", json={"email": "ninguem@hospital.dev"})
    b = cli.post("/api/auth/reset/solicitar", json={"email": "carla@hospital.dev"})
    assert a.status_code == b.status_code == 202 and a.json() == b.json()
    token = caixa_de_saida[-1]["token"]
    nova = "nova frase longa e bem segura"
    assert cli.post("/api/auth/reset/confirmar", json={"token": token, "novaSenha": nova}).status_code == 204
    assert cli.post("/api/auth/reset/confirmar", json={"token": token, "novaSenha": nova}).status_code == 400
    assert login("carla@hospital.dev", nova).status_code == 200


def test_reset_expirado():
    token = "token-de-teste-expirado"
    executar("INSERT INTO redefinicoes VALUES (?, 'u2', ?, 0)",
             hashlib.sha256(token.encode()).hexdigest(), int(time.time() * 1000) - 1)
    r = cli.post("/api/auth/reset/confirmar", json={"token": token, "novaSenha": "outra frase longa qualquer"})
    assert r.status_code == 400
