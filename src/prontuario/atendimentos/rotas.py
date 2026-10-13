from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prontuario.compartilhado.dados import buscar, db

router = APIRouter()


class Alteracao(BaseModel):
    motivo: str | None = Field(default=None, min_length=3)
    status: Literal["aberto", "finalizado"] | None = None


@router.get("/api/encounters/{id}")
def obter(id: str):
    e = buscar(db.atendimentos, id)
    if e is None:
        raise HTTPException(404, "Recurso não encontrado.")
    return e


@router.patch("/api/encounters/{id}")
def alterar(id: str, dados: Alteracao):
    e = buscar(db.atendimentos, id)
    if e is None:
        raise HTTPException(404, "Recurso não encontrado.")
    e.update(dados.model_dump(exclude_none=True))
    return e
