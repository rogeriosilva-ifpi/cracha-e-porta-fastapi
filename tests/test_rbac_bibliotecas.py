from fastapi import FastAPI, Security
from fastapi.testclient import TestClient

from prontuario.acesso import usuarios
from prontuario.acesso.casbin_rbac import enforcer_da_matriz
from prontuario.acesso.escopos import com_escopos
from prontuario.acesso.permissoes import MATRIZ, pode
from prontuario.http import erros
from tests.ajuda import entrar

PERMISSOES = sorted({p for ps in MATRIZ.values() for p in ps})


# Casbin e a matriz dizem a mesma coisa

def test_casbin_concorda_com_a_matriz_em_todas_as_combinacoes():
    e = enforcer_da_matriz(usuarios.listar())
    for u in usuarios.listar():
        for p in PERMISSOES:
            objeto, acao = p.split(":")
            assert e.enforce(u["id"], objeto, acao) == pode(u["papel"], p), (u["id"], p)


def test_casbin_explica_o_papel_de_cada_usuario():
    e = enforcer_da_matriz(usuarios.listar())
    assert e.get_roles_for_user("u2") == ["profissional"]


# Escopos nativos do FastAPI

app = FastAPI()
erros.instalar(app)


@app.get("/relatorio")
def relatorio(usuario: dict = Security(com_escopos, scopes=["rx:read"])):
    return {"para": usuario["id"]}


cli = TestClient(app)


def test_escopo_conferido_contra_a_matriz():
    from prontuario.app import criar_app
    principal = TestClient(criar_app())
    assert cli.get("/relatorio", headers=entrar(principal, "ana@hospital.dev")).status_code == 200
    assert cli.get("/relatorio", headers=entrar(principal, "carla@hospital.dev")).status_code == 403
    assert cli.get("/relatorio").status_code == 401

