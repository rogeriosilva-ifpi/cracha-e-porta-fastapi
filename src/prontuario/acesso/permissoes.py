"""Matriz de permissões do Mini-Prontuário (contrato do Tópico 3).

Fonte única: rotas e testes leem daqui. O cap. 10 discute quando
ela deve sair do código e ir para o banco.
"""
from typing import Literal

from prontuario.compartilhado.dados import Papel

Permissao = Literal[
    "patient:read", "patient:create",
    "encounter:read", "encounter:update",
    "rx:read", "rx:create",
    "user:admin",
]

MATRIZ: dict[Papel, frozenset[Permissao]] = {
    "admin": frozenset({"patient:read", "patient:create", "encounter:read",
                        "encounter:update", "rx:read", "user:admin"}),
    "profissional": frozenset({"patient:read", "patient:create", "encounter:read",
                               "encounter:update", "rx:read", "rx:create"}),
    "recepcao": frozenset({"patient:read", "patient:create", "encounter:read"}),
}


def pode(papel: Papel, permissao: Permissao) -> bool:
    return permissao in MATRIZ[papel]
