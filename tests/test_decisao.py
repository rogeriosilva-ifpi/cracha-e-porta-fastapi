import json
from datetime import datetime

import pytest

from prontuario.acesso.cedar import autorizar_cedar
from prontuario.acesso.decisao import abac, de_plantao, rbac

CASOS = json.load(open("politicas/casos.json"))
veredito = lambda d: "permitido" if d["permitido"] else "negado"


# tabela de casos (politicas/casos.json)

@pytest.mark.parametrize("c", CASOS, ids=[c["caso"] for c in CASOS])
def test_abac(c):
    assert veredito(abac(c["sujeito"], c["recurso"], c["contexto"])) == c["esperado"]


@pytest.mark.parametrize("c", CASOS, ids=[c["caso"] for c in CASOS])
def test_cedar(c):
    assert veredito(autorizar_cedar(c["sujeito"], c["recurso"], c["contexto"])) == c["esperado"]


def test_rbac_puro_erra_algum_caso():
    assert any(veredito(rbac(c["sujeito"], c["recurso"], c["contexto"])) != c["esperado"] for c in CASOS)


# explicar por que negou

def test_cedar_diz_qual_politica_decidiu():
    ok, bruno, _, _, suspensa = CASOS[:5]
    assert autorizar_cedar(ok["sujeito"], ok["recurso"], ok["contexto"])["motivo"] == "prescrever-no-proprio-atendimento"
    assert autorizar_cedar(suspensa["sujeito"], suspensa["recurso"], suspensa["contexto"])["motivo"] == "registro-suspenso"
    assert autorizar_cedar(bruno["sujeito"], bruno["recurso"], bruno["contexto"])["motivo"] == "nenhuma política permite"


def test_abac_diz_qual_atributo_falhou():
    bruno = CASOS[1]
    assert abac(bruno["sujeito"], bruno["recurso"], bruno["contexto"])["motivo"] == "não é o autor do atendimento"


def test_politica_com_erro_nega():
    ok = CASOS[0]
    d = autorizar_cedar(ok["sujeito"], ok["recurso"], ok["contexto"], "permit (principal, action, resource")
    assert d == {"permitido": False, "motivo": "erro na política"}


# atributo do ambiente: plantão

def as_(h, m=0):
    return datetime(2026, 10, 13, h, m)


def test_diurno():
    assert de_plantao("u2", as_(10)) and not de_plantao("u2", as_(19))


def test_noturno_vira_a_meia_noite():
    assert de_plantao("u3", as_(23)) and de_plantao("u3", as_(3)) and not de_plantao("u3", as_(12))


def test_sem_escala_nunca():
    assert not de_plantao("u4", as_(10))
