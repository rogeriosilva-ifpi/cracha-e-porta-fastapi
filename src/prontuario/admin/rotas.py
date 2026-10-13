from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso.politica import exige
from prontuario.compartilhado.dados import db, novo_id

router = APIRouter()


class NovoUsuario(BaseModel):
    nome: str = Field(min_length=2)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    papel: Literal["admin", "profissional", "recepcao"]


@router.get("/api/admin/users", dependencies=[Depends(exige("user:admin"))])
def listar():
    return db.usuarios


@router.post("/api/admin/users", status_code=201, dependencies=[Depends(exige("user:admin"))])
def criar(dados: NovoUsuario):
    u = {"id": novo_id("u"), **dados.model_dump(), "passwordHash": ""}
    db.usuarios.append(u)
    return u
