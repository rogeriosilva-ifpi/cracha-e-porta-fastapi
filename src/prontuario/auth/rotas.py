"""Login. VERSÃO INGÊNUA (tag cap04-antes): veja o capítulo 4."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from prontuario.acesso import usuarios
from prontuario.acesso.politica import publica
from prontuario.acesso.senhas import senhas
from prontuario.compartilhado.erros import NotFoundError, UnauthorizedError

router = APIRouter()


class Login(BaseModel):
    email: str
    senha: str


@router.post("/api/auth/login", dependencies=[Depends(publica())])
def login(dados: Login):
    u = usuarios.por_email(dados.email)
    if u is None:
        raise NotFoundError("E-mail não cadastrado.")
    if not senhas.verify(dados.senha, u["passwordHash"]):
        raise UnauthorizedError("Senha incorreta.")
    return {"usuario": u}
