"""Toda rota declara uma política na lista `dependencies` do decorador.

O censo (scripts/censo.py e tests/test_censo.py) lê o atributo
`politica` que estas funções carregam.
"""
from fastapi import Request

from prontuario.acesso.cracha_provisorio import identificar
from prontuario.acesso.permissoes import Permissao, pode
from prontuario.compartilhado.erros import ForbiddenError, UnauthorizedError


def publica():
    def politica_publica() -> None:
        return None
    politica_publica.politica = {"publica": True}
    return politica_publica


def exige(permissao: Permissao):
    def politica_exige(request: Request) -> dict:
        usuario = identificar(request)                 # portão 1
        if usuario is None:
            raise UnauthorizedError()
        if not pode(usuario["papel"], permissao):      # portão 2
            raise ForbiddenError()
        request.state.usuario = usuario
        return usuario
    politica_exige.politica = {"permissao": permissao}
    return politica_exige
