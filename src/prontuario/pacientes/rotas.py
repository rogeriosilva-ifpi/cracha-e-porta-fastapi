from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prontuario.compartilhado.dados import buscar, db, novo_id

router = APIRouter()


class NovoPaciente(BaseModel):
    nome: str = Field(min_length=2)
    cns: str = Field(pattern=r"^\d{15}$")
    nascimento: date


@router.get("/api/patients")
def listar():
    return db.pacientes


@router.get("/api/patients/{id}")
def obter(id: str):
    p = buscar(db.pacientes, id)
    if p is None:
        raise HTTPException(404, "Recurso não encontrado.")
    return p


@router.post("/api/patients", status_code=201)
def criar(dados: NovoPaciente):
    p = {"id": novo_id("p"), **dados.model_dump(mode="json")}
    db.pacientes.append(p)
    return p
