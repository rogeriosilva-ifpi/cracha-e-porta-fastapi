"""Toda rota declara uma política na lista `dependencies` do decorador.

O censo (scripts/censo.py e tests/test_censo.py) lê o atributo
`politica` que estas funções carregam.
"""
from fastapi import Request

from prontuario.acesso.identidade import identificar
from prontuario.acesso.permissoes import Permissao, pode
from prontuario.compartilhado.erros import ForbiddenError, UnauthorizedError
from prontuario.compartilhado.eventos import registrar as evento


def publica():
    def politica_publica() -> None:
        return None
    politica_publica.politica = {"publica": True}
    return politica_publica


def autenticada():
    """Basta estar logado (ex.: logout, "quem sou eu"). São funções da
    própria conta: gente entra, chave de API não (capítulo 15)."""
    def politica_autenticada(request: Request) -> dict:
        usuario = identificar(request)
        if usuario is None:
            raise UnauthorizedError()
        if request.state.chave:
            raise ForbiddenError("Chave de API não gerencia a conta.")
        request.state.usuario = usuario
        return usuario
    politica_autenticada.politica = {"autenticada": True}
    return politica_autenticada


def exige(permissao: Permissao):
    def politica_exige(request: Request) -> dict:
        usuario = identificar(request)                 # portão 1
        if usuario is None:
            raise UnauthorizedError()
        if not pode(usuario["papel"], permissao):      # portão 2
            raise ForbiddenError("Permissão insuficiente.")
        dentro_do_escopo(request, permissao)           # portão 2b
        request.state.usuario = usuario
        return usuario
    politica_exige.politica = {"permissao": permissao}
    return politica_exige


def dentro_do_escopo(request: Request, permissao: Permissao) -> None:
    """Pedido feito com chave de API: a permissão tem de estar no escopo dela."""
    chave = request.state.chave
    if chave and permissao not in chave["escopos"]:
        evento("chave_fora_do_escopo", chave=chave["id"], permissao=permissao)
        raise ForbiddenError("Fora do escopo da chave.")
