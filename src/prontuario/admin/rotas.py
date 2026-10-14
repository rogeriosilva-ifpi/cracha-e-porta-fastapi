from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from prontuario.acesso import usuarios
from prontuario.acesso.politica import exige
from prontuario.acesso.refresh import revogar_todas
from prontuario.acesso.chaves import revogar_chaves_de
from prontuario.acesso.sessoes import encerrar_todas
from prontuario.acesso.senhas import motivo_de_recusa, senhas
from fastapi import Response

from prontuario.compartilhado.erros import BadRequestError, NotFoundError
from prontuario.compartilhado.eventos import registrar as evento
from prontuario.compartilhado.dados import novo_id

router = APIRouter()


class NovoUsuario(BaseModel):
    nome: str = Field(min_length=2)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    papel: Literal["admin", "profissional", "recepcao"]
    senha: str


@router.get("/api/admin/users", dependencies=[Depends(exige("user:admin"))])
def listar():
    return [usuarios.publico(u) for u in usuarios.listar()]   # nunca o hash


@router.post("/api/admin/users", status_code=201, dependencies=[Depends(exige("user:admin"))])
def criar(dados: NovoUsuario):
    d = dados.model_dump()
    senha = d.pop("senha")
    motivo = motivo_de_recusa(senha, d["email"])
    if motivo:
        raise BadRequestError(motivo)
    return usuarios.publico(usuarios.criar({"id": novo_id("u"), **d, "passwordHash": senhas.hash(senha)}))


# Desligamento: derruba sessões, apps e chaves de API. Função administrativa:
# permissão declarada, não "o botão só aparece para o admin".
@router.post("/api/admin/users/{id_}/desligar", status_code=204)
def desligar(id_: str, admin: dict = Depends(exige("user:admin"))):
    u = usuarios.por_id(id_)
    if u is None:
        raise NotFoundError()
    encerrar_todas(u["id"])
    revogar_todas(u["id"])
    revogar_chaves_de(u["id"])
    evento("usuario_desligado", usuario=u["id"], por=admin["id"])
    return Response(status_code=204)


class NovoPapel(BaseModel):
    papel: Literal["admin", "profissional", "recepcao"]


# Troca de papel: permissão declarada; derruba sessões, apps e chaves
# da pessoa, para nenhum token ou tela antiga carregar o papel velho.
@router.patch("/api/admin/users/{id_}/papel")
def trocar_papel(id_: str, dados: NovoPapel, admin: dict = Depends(exige("user:admin"))):
    u = usuarios.por_id(id_)
    if u is None:
        raise NotFoundError()
    usuarios.trocar_papel(u["id"], dados.papel)
    encerrar_todas(u["id"])
    revogar_todas(u["id"])
    revogar_chaves_de(u["id"])
    evento("papel_alterado", usuario=u["id"], de=u["papel"], para=dados.papel, por=admin["id"])
    return usuarios.publico(usuarios.por_id(u["id"]))
