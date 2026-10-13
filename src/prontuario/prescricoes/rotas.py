from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from prontuario.compartilhado.dados import buscar, db, novo_id

router = APIRouter()


class NovaPrescricao(BaseModel):
    medicamento: str = Field(min_length=2)
    posologia: str = Field(min_length=2)
    profissionalId: str  # quem prescreve vem do corpo (por enquanto)


@router.get("/api/medication-requests")
def listar(encounterId: str | None = None):
    if encounterId:
        return [m for m in db.prescricoes if m["atendimentoId"] == encounterId]
    return db.prescricoes


@router.post("/api/encounters/{id}/medication-requests", status_code=201)
def prescrever(id: str, dados: NovaPrescricao):
    e = buscar(db.atendimentos, id)
    if e is None:
        raise HTTPException(404, "Recurso não encontrado.")
    m = {"id": novo_id("m"), "atendimentoId": e["id"], **dados.model_dump()}
    db.prescricoes.append(m)
    return m
