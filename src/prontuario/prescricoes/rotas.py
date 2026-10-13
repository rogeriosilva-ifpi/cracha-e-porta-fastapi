from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso.politica import autenticada, exige
from prontuario.compartilhado.dados import buscar, db, novo_id
from prontuario.compartilhado.erros import ForbiddenError, NotFoundError

router = APIRouter()


class NovaPrescricao(BaseModel):
    medicamento: str = Field(min_length=2)
    posologia: str = Field(min_length=2)
    profissionalId: str  # quem prescreve vem do corpo (por enquanto)


@router.get("/api/medication-requests", dependencies=[Depends(exige("rx:read"))])
def listar(encounterId: str | None = None):
    if encounterId:
        return [m for m in db.prescricoes if m["atendimentoId"] == encounterId]
    return db.prescricoes


@router.post("/api/encounters/{id}/medication-requests", status_code=201, dependencies=[Depends(exige("rx:create"))])
def prescrever(id: str, dados: NovaPrescricao):
    e = buscar(db.atendimentos, id)
    if e is None:
        raise NotFoundError()
    m = {"id": novo_id("m"), "atendimentoId": e["id"], **dados.model_dump()}
    db.prescricoes.append(m)
    return m


# Relatório: prescrições por profissional. VERSÃO INGÊNUA (cap11-antes).
@router.get("/api/reports/prescriptions")
def relatorio(usuario: dict = Depends(autenticada())):
    if usuario["papel"] not in ("admin", "profissional"):
        raise ForbiddenError()
    por_profissional: dict[str, int] = {}
    for m in db.prescricoes:
        por_profissional[m["profissionalId"]] = por_profissional.get(m["profissionalId"], 0) + 1
    return por_profissional
