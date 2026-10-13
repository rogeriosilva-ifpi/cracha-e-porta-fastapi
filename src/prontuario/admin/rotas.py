from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso import usuarios
from prontuario.acesso.politica import exige
from prontuario.acesso.senhas import motivo_de_recusa, senhas
from prontuario.compartilhado.erros import BadRequestError
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
