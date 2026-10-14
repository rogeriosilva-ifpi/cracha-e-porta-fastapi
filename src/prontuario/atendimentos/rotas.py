from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from prontuario.acesso.politica import exige
from prontuario.atendimentos.escopo import buscar_visivel, saida, visiveis
from prontuario.compartilhado.erros import ForbiddenError

router = APIRouter()


class Alteracao(BaseModel):
    # Só estes campos; qualquer outro no corpo é 400 (atribuição em massa).
    model_config = ConfigDict(extra="forbid")
    motivo: str | None = Field(default=None, min_length=3)
    status: Literal["aberto", "finalizado"] | None = None


@router.get("/api/encounters")
def listar(u: dict = Depends(exige("encounter:read"))):
    return [saida(u, a) for a in visiveis(u)]


@router.get("/api/encounters/{id}")
def obter(id: str, u: dict = Depends(exige("encounter:read"))):
    return saida(u, buscar_visivel(u, id))


@router.patch("/api/encounters/{id}")
def alterar(id: str, dados: Alteracao, u: dict = Depends(exige("encounter:update"))):
    a = buscar_visivel(u, id)                 # 404 se não vê
    if a["profissionalId"] != u["id"]:        # vê, mas não é seu
        raise ForbiddenError("Só o autor altera o atendimento.")
    a.update(dados.model_dump(exclude_none=True))
    return a
