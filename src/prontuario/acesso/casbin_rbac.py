"""A mesma matriz no Casbin (capítulo 11), para quando a política cresce
e precisa sair do código: modelo em arquivo, regras em tabela."""
from pathlib import Path

import casbin

from prontuario.acesso.permissoes import MATRIZ

MODELO = Path(__file__).resolve().parents[3] / "politicas" / "rbac.conf"


def enforcer_da_matriz(usuarios: list[dict]) -> casbin.Enforcer:
    e = casbin.Enforcer(str(MODELO))
    for papel, permissoes in MATRIZ.items():
        for p in permissoes:
            objeto, acao = p.split(":")
            e.add_policy(papel, objeto, acao)        # p, profissional, rx, create
    for u in usuarios:
        e.add_role_for_user(u["id"], u["papel"])     # g, u2, profissional
    return e
