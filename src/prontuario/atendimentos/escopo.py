"""Portão 3 (capítulo 12): quais atendimentos cada pessoa vê, e com
quanto detalhe. A regra vira consulta: nunca "busca e confere depois"."""
from prontuario.acesso.permissoes import pode
from prontuario.compartilhado.dados import db
from prontuario.compartilhado.erros import NotFoundError


def visiveis(u: dict) -> list[dict]:
    """Os atendimentos que esta pessoa pode ver (a "consulta escopada")."""
    if pode(u["papel"], "encounter:read_any"):
        return db.atendimentos                                   # lista geral
    return [a for a in db.atendimentos if a["profissionalId"] == u["id"]]  # só os seus


def buscar_visivel(u: dict, id_: str) -> dict:
    """Busca DENTRO do escopo: o que não é visível nem existe (404)."""
    a = next((x for x in visiveis(u) if x["id"] == id_), None)
    if a is None:
        raise NotFoundError()
    return a


def saida(u: dict, a: dict) -> dict:
    """Saída por quem pede: dado clínico só para o autor do atendimento."""
    if a["profissionalId"] == u["id"]:
        return a
    return {k: a[k] for k in ("id", "pacienteId", "profissionalId", "status")}
