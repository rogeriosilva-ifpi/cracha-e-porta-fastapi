from datetime import datetime

from fastapi import APIRouter, Body, Depends
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from prontuario.acesso.decisao import abac, de_plantao
from prontuario.acesso.politica import exige
from prontuario.atendimentos.escopo import buscar_visivel, visiveis
from prontuario.compartilhado.dados import db, novo_id
from prontuario.compartilhado.erros import ForbiddenError
from prontuario.compartilhado.eventos import registrar as evento

router = APIRouter()


class NovaPrescricao(BaseModel):
    # Quem prescreve vem da sessão, nunca do corpo.
    model_config = ConfigDict(extra="forbid")
    medicamento: str = Field(min_length=2)
    posologia: str = Field(min_length=2)


@router.get("/api/medication-requests")
def listar(encounterId: str | None = None, u: dict = Depends(exige("rx:read"))):
    meus = {a["id"] for a in visiveis(u)}                     # escopo
    return [m for m in db.prescricoes if m["atendimentoId"] in meus
            and (not encounterId or m["atendimentoId"] == encounterId)]


@router.post("/api/encounters/{id}/medication-requests", status_code=201)
def prescrever(id: str, dados: dict = Body(...), u: dict = Depends(exige("rx:create"))):
    a = buscar_visivel(u, id)                                  # 404
    d = abac({"id": u["id"], "papel": u["papel"]},             # cap. 10
             {"id": a["id"], "autor": a["profissionalId"], "status": a["status"]},
             {"de_plantao": de_plantao(u["id"], datetime.now())})
    if not d["permitido"]:
        evento("acesso_negado", usuario=u["id"], recurso=a["id"], motivo=d["motivo"])
        raise ForbiddenError()                                 # motivo só no evento
    try:
        nova = NovaPrescricao.model_validate(dados)
    except ValidationError as e:
        raise RequestValidationError(e.errors())
    m = {"id": novo_id("m"), "atendimentoId": a["id"], "profissionalId": u["id"],
         **nova.model_dump()}
    db.prescricoes.append(m)
    return m


# Relatório: prescrições por profissional. A permissão mora na matriz.
@router.get("/api/reports/prescriptions", dependencies=[Depends(exige("rx:read"))])
def relatorio():
    por_profissional: dict[str, int] = {}
    for m in db.prescricoes:
        por_profissional[m["profissionalId"]] = por_profissional.get(m["profissionalId"], 0) + 1
    return por_profissional
