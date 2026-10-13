"""Login e redefinição de senha (capítulo 4)."""
import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field

from prontuario.acesso import usuarios
from prontuario.acesso.politica import autenticada, publica
from prontuario.acesso.sessoes import encerrar, encerrar_todas, iniciar
from prontuario.acesso.refresh import abrir_familia, girar, revogar_familia, revogar_todas
from prontuario.acesso.tokens import ACCESS_S, emitir_access, jwks
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


def conferir(dados: Login) -> dict:
    """Confere e-mail e senha (capítulo 4). Toda falha é a mesma."""
    u = usuarios.por_email(dados.email)
    if u is None:
        senhas.verify(dados.senha, HASH_FICTICIO)   # mesmo custo
        raise UnauthorizedError(FALHA)
    ok, novo_hash = senhas.verify_and_update(dados.senha, u["passwordHash"])
    if not ok:
        raise UnauthorizedError(FALHA)
    if novo_hash:                    # parâmetros antigos: refaz o hash
        usuarios.trocar_hash(u["id"], novo_hash)
    return u


def par(usuario_id: str, familia: str, refresh: str) -> dict:
    """Access curto (JWT, carrega a família em sid) + refresh opaco."""
    return {"access_token": emitir_access(usuario_id, {"sid": familia}),
            "token_type": "Bearer", "expires_in": ACCESS_S, "refresh_token": refresh}


# Navegador: sessão em cookie (capítulo 5).
@router.post("/api/auth/login", dependencies=[Depends(publica())])
def login(dados: Login, request: Request, response: Response):
    u = conferir(dados)
    iniciar(request, response, u["id"])
    return {"usuario": usuarios.publico(u)}


# Clientes de API (app, integrações): token Bearer (capítulo 6).
@router.post("/api/auth/token", dependencies=[Depends(publica())])
def token(dados: Login):
    u = conferir(dados)
    familia, refresh = abrir_familia(u["id"])
    return par(u["id"], familia, refresh)


class Renovacao(BaseModel):
    refresh_token: str = Field(max_length=2000)


# Troca o refresh por um par novo (capítulo 7).
@router.post("/api/auth/refresh", dependencies=[Depends(publica())])
def renovar(dados: Renovacao):
    g = girar(dados.refresh_token)
    if g is None:
        raise UnauthorizedError()
    return par(g["usuario_id"], g["familia"], g["refresh"])


# "Sair de todos os dispositivos".
@router.post("/api/auth/logout-all", status_code=204)
def sair_de_todos(usuario: dict = Depends(autenticada())):
    encerrar_todas(usuario["id"])     # cookies
    revogar_todas(usuario["id"])      # apps
    return Response(status_code=204)


# Chaves públicas: quem confere nossos tokens busca aqui.
@router.get("/.well-known/jwks.json", dependencies=[Depends(publica())])
def chaves_publicas():
    return jwks()


@router.post("/api/auth/logout", status_code=204, dependencies=[Depends(autenticada())])
def logout(request: Request):
    resposta = Response(status_code=204)
    familia = getattr(request.state, "familia", None)
    if familia:
        revogar_familia(familia)      # app: só este
    else:
        encerrar(request, resposta)   # navegador
    return resposta


@router.get("/api/auth/me")
def me(usuario: dict = Depends(autenticada())):
    return {"usuario": usuarios.publico(usuario)}


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
    encerrar_todas(u["id"])          # senha nova derruba sessões antigas
    revogar_todas(u["id"])           # e os apps conectados
    return Response(status_code=204)
