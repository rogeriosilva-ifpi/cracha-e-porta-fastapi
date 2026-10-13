"""Login e redefinição de senha (capítulo 4)."""
import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field

from prontuario.acesso import usuarios
from prontuario.acesso.politica import publica
from prontuario.acesso.senhas import HASH_FICTICIO, MAX, motivo_de_recusa, senhas
from prontuario.compartilhado.banco import consultar, executar
from prontuario.compartilhado.erros import BadRequestError, UnauthorizedError

router = APIRouter()
FALHA = "Credenciais inválidas."     # a mesma para todo erro
VALIDADE_MS = 15 * 60 * 1000         # token de redefinição: 15 min
caixa_de_saida: list[dict] = []      # o "e-mail" simulado que levaria o link


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


class Login(BaseModel):
    email: str = Field(max_length=254)
    senha: str = Field(max_length=MAX)


@router.post("/api/auth/login", dependencies=[Depends(publica())])
def login(dados: Login):
    u = usuarios.por_email(dados.email)
    if u is None:
        senhas.verify(dados.senha, HASH_FICTICIO)   # mesmo custo
        raise UnauthorizedError(FALHA)
    ok, novo_hash = senhas.verify_and_update(dados.senha, u["passwordHash"])
    if not ok:
        raise UnauthorizedError(FALHA)
    if novo_hash:                    # parâmetros antigos: refaz o hash
        usuarios.trocar_hash(u["id"], novo_hash)
    return {"usuario": usuarios.publico(u)}


class Solicitacao(BaseModel):
    email: str = Field(max_length=254)


@router.post("/api/auth/reset/solicitar", status_code=202, dependencies=[Depends(publica())])
def solicitar(dados: Solicitacao):
    u = usuarios.por_email(dados.email)
    if u:
        token = secrets.token_urlsafe(32)
        executar("INSERT INTO redefinicoes (token_hash, usuario_id, expira_em) VALUES (?, ?, ?)",
                 sha256(token), u["id"], int(time.time() * 1000) + VALIDADE_MS)
        caixa_de_saida.append({"para": u["email"], "token": token})
    # Mesma resposta exista ou não o e-mail.
    return {"mensagem": "Se o e-mail existir, enviaremos instruções."}


class Confirmacao(BaseModel):
    token: str = Field(max_length=100)
    novaSenha: str = Field(max_length=MAX)


@router.post("/api/auth/reset/confirmar", status_code=204, dependencies=[Depends(publica())])
def confirmar(dados: Confirmacao):
    r = consultar("SELECT * FROM redefinicoes WHERE token_hash = ?", sha256(dados.token))
    if not r or r[0]["usado"] or r[0]["expira_em"] < time.time() * 1000:
        raise BadRequestError("Código inválido ou expirado.")
    u = usuarios.por_id(r[0]["usuario_id"])
    motivo = motivo_de_recusa(dados.novaSenha, u["email"])
    if motivo:
        raise BadRequestError(motivo)
    executar("UPDATE redefinicoes SET usado = 1 WHERE token_hash = ?", sha256(dados.token))
    usuarios.trocar_hash(u["id"], senhas.hash(dados.novaSenha))
    return Response(status_code=204)
