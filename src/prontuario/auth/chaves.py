"""Rotas de chaves de API e metadados do recurso protegido (cap. 15)."""
from typing import get_args

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field

from prontuario.acesso.chaves import (MAX_ATIVAS, MAX_DIAS, criar_chave, listar_chaves,
                                      revogar_chave)
from prontuario.acesso.permissoes import Permissao, pode
from prontuario.acesso.politica import autenticada, publica
from prontuario.acesso.tokens import EMISSOR
from prontuario.compartilhado.erros import BadRequestError, ForbiddenError, NotFoundError
from prontuario.compartilhado.eventos import registrar as evento

router = APIRouter()
RECURSO = f"{EMISSOR}/api"
METADADOS_URL = f"{EMISSOR}/.well-known/oauth-protected-resource"
TODAS = list(get_args(Permissao))


class NovaChave(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nome: str = Field(min_length=3, max_length=60)
    escopos: list[Permissao] = Field(min_length=1)     # nada de "*"
    dias: int = Field(default=30, ge=1, le=MAX_DIAS)


@router.post("/api/auth/chaves", status_code=201)
def criar(dados: NovaChave, u: dict = Depends(autenticada())):
    # Ninguém delega o que não tem: escopo é subconjunto do papel.
    alem = [e for e in dados.escopos if not pode(u["papel"], e)]
    if alem:
        raise ForbiddenError(f"Escopo além do seu papel: {', '.join(alem)}.")
    if len(listar_chaves(u["id"])) >= MAX_ATIVAS:
        raise BadRequestError(f"Limite de {MAX_ATIVAS} chaves ativas.")
    nova = criar_chave(u["id"], dados.nome, list(dict.fromkeys(dados.escopos)), dados.dias)
    evento("chave_criada", usuario=u["id"], chave=nova["id"], escopos=nova["escopos"])
    return nova                       # a única vez em que a chave aparece


@router.get("/api/auth/chaves")
def listar(u: dict = Depends(autenticada())):
    return listar_chaves(u["id"])


@router.delete("/api/auth/chaves/{id_}", status_code=204)
def revogar(id_: str, u: dict = Depends(autenticada())):
    if not revogar_chave(id_, u["id"]):
        raise NotFoundError()
    evento("chave_revogada", usuario=u["id"], chave=id_)
    return Response(status_code=204)


# RFC 9728: o recurso se descreve. Cliente e agente descobrem aqui
# quem emite credenciais para ele e quais escopos existem.
@router.get("/.well-known/oauth-protected-resource", dependencies=[Depends(publica())])
def metadados():
    return {"resource": RECURSO, "authorization_servers": [EMISSOR],
            "bearer_methods_supported": ["header"], "scopes_supported": TODAS,
            "resource_name": "Mini-Prontuário API"}
