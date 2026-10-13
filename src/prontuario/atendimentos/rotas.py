from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso.politica import exige
from prontuario.compartilhado.dados import buscar, db
from prontuario.compartilhado.erros import NotFoundError

router = APIRouter()


class Alteracao(BaseModel):
    motivo: str | None = Field(default=None, min_length=3)
    status: Literal["aberto", "finalizado"] | None = None


@router.get("/api/encounters/{id}", dependencies=[Depends(exige("encounter:read"))])
def obter(id: str):
    e = buscar(db.atendimentos, id)
    if e is None:
        raise NotFoundError()
    return e


@router.patch("/api/encounters/{id}", dependencies=[Depends(exige("encounter:update"))])
def alterar(id: str, dados: Alteracao):
    e = buscar(db.atendimentos, id)
    if e is None:
        raise NotFoundError()
    e.update(dados.model_dump(exclude_none=True))
    return e
