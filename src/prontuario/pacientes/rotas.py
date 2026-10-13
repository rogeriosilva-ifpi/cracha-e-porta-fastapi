from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso.politica import exige
from prontuario.compartilhado.dados import buscar, db, novo_id
from prontuario.compartilhado.erros import NotFoundError

router = APIRouter()


class NovoPaciente(BaseModel):
    nome: str = Field(min_length=2)
    cns: str = Field(pattern=r"^\d{15}$")
    nascimento: date


@router.get("/api/patients", dependencies=[Depends(exige("patient:read"))])
def listar():
    return db.pacientes


@router.get("/api/patients/{id}", dependencies=[Depends(exige("patient:read"))])
def obter(id: str):
    p = buscar(db.pacientes, id)
    if p is None:
        raise NotFoundError()
    return p


@router.post("/api/patients", status_code=201, dependencies=[Depends(exige("patient:create"))])
def criar(dados: NovoPaciente):
    p = {"id": novo_id("p"), **dados.model_dump(mode="json")}
    db.pacientes.append(p)
    return p
