from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso import usuarios
from prontuario.acesso.politica import autenticada, exige
from prontuario.acesso.refresh import revogar_todas
from prontuario.acesso.sessoes import encerrar_todas
from prontuario.acesso.senhas import motivo_de_recusa, senhas
from fastapi import Response

from prontuario.compartilhado.erros import BadRequestError, ForbiddenError, NotFoundError
from prontuario.compartilhado.dados import novo_id

router = APIRouter()


class NovoUsuario(BaseModel):
    nome: str = Field(min_length=2)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    papel: Literal["admin", "profissional", "recepcao"]
    senha: str


@router.get("/api/admin/users", dependencies=[Depends(exige("user:admin"))])
def listar():
    return usuarios.listar()


@router.post("/api/admin/users", status_code=201, dependencies=[Depends(exige("user:admin"))])
def criar(dados: NovoUsuario):
    d = dados.model_dump()
    senha = d.pop("senha")
    motivo = motivo_de_recusa(senha, d["email"])
    if motivo:
        raise BadRequestError(motivo)
    return usuarios.criar({"id": novo_id("u"), **d, "passwordHash": senhas.hash(senha)})


# Desligamento: derruba sessões e apps. VERSÃO INGÊNUA (cap11-antes):
# "o botão só aparece para o admin na tela".
@router.post("/api/admin/users/{id_}/desligar", status_code=204,
             dependencies=[Depends(autenticada())])
def desligar(id_: str):
    u = usuarios.por_id(id_)
    if u is None:
        raise NotFoundError()
    encerrar_todas(u["id"])
    revogar_todas(u["id"])
    return Response(status_code=204)


class NovoPapel(BaseModel):
    papel: Literal["admin", "profissional", "recepcao"]


# Troca de papel. VERSÃO INGÊNUA: papel conferido à mão.
@router.patch("/api/admin/users/{id_}/papel")
def trocar_papel(id_: str, dados: NovoPapel, usuario: dict = Depends(autenticada())):
    if usuario["papel"] != "admin":
        raise ForbiddenError()
    u = usuarios.por_id(id_)
    if u is None:
        raise NotFoundError()
    usuarios.trocar_papel(u["id"], dados.papel)
    return usuarios.publico(usuarios.por_id(u["id"]))
