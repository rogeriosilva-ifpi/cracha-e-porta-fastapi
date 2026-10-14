"""Login e redefinição de senha (capítulo 4)."""
import hashlib
import secrets
import time

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from prontuario.acesso import usuarios
from prontuario.acesso.politica import autenticada, publica
from prontuario.acesso.sessoes import encerrar, encerrar_todas, iniciar
from prontuario.acesso.limites import POR_IP, bloqueio, limitador, limpar_falhas, registrar_falha
from prontuario.acesso.mfa import (abrir_desafio, ativar, iniciar_cadastro, mfa_ativo,
                                   resolver_desafio)
from prontuario.acesso.refresh import abrir_familia, girar, revogar_familia, revogar_todas
from prontuario.acesso.tokens import ACCESS_S, emitir_access, jwks
from prontuario.acesso.senhas import HASH_FICTICIO, MAX, motivo_de_recusa, senhas
from prontuario.compartilhado.banco import consultar, executar
from prontuario.compartilhado.erros import BadRequestError, TooManyRequestsError, UnauthorizedError
from prontuario.compartilhado.eventos import conta_anonima
from prontuario.compartilhado.eventos import registrar as evento

router = APIRouter()
FALHA = "Credenciais inválidas."     # a mesma para todo erro
VALIDADE_MS = 15 * 60 * 1000         # token de redefinição: 15 min
caixa_de_saida: list[dict] = []      # o "e-mail" simulado que levaria o link


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


class Login(BaseModel):
    email: str = Field(max_length=254)
    senha: str = Field(max_length=MAX)


def conferir(dados: Login, request: Request) -> dict:
    """Confere e-mail e senha (capítulos 4 e 9). Toda falha é a mesma."""
    ip = request.client.host if request.client else ""
    espera = bloqueio(dados.email, request)     # antes de gastar argon2
    if espera:
        evento("conta_limitada", conta=conta_anonima(dados.email), ip=ip)
        raise TooManyRequestsError(espera)
    u = usuarios.por_email(dados.email)
    if u is None:
        senhas.verify(dados.senha, HASH_FICTICIO)   # mesmo custo
        ok, novo_hash = False, None
    else:
        ok, novo_hash = senhas.verify_and_update(dados.senha, u["passwordHash"])
    if not ok:
        registrar_falha(dados.email, request)
        evento("login_falhou", usuario=u and u["id"], conta=conta_anonima(dados.email), ip=ip)
        raise UnauthorizedError(FALHA)
    limpar_falhas(dados.email, request)
    if novo_hash:                    # parâmetros antigos: refaz o hash
        usuarios.trocar_hash(u["id"], novo_hash)
    evento("login_ok", usuario=u["id"], ip=ip)
    return u


def par(usuario_id: str, familia: str, refresh: str) -> dict:
    """Access curto (JWT, carrega a família em sid) + refresh opaco."""
    return {"access_token": emitir_access(usuario_id, {"sid": familia}),
            "token_type": "Bearer", "expires_in": ACCESS_S, "refresh_token": refresh}


# Navegador: sessão em cookie (capítulo 5).
@router.post("/api/auth/login", dependencies=[Depends(publica())])
@limitador.limit(POR_IP)
def login(dados: Login, request: Request, response: Response):
    u = conferir(dados, request)
    if mfa_ativo(u["id"]):            # senha certa ainda não é login
        return {"mfa_requerido": True, "desafio": abrir_desafio(u["id"], "cookie")}
    iniciar(request, response, u["id"])
    return {"usuario": usuarios.publico(u)}


# Clientes de API (app, integrações): token Bearer (capítulo 6).
@router.post("/api/auth/token", dependencies=[Depends(publica())])
@limitador.limit(POR_IP)
def token(dados: Login, request: Request):
    u = conferir(dados, request)
    if mfa_ativo(u["id"]):
        return {"mfa_requerido": True, "desafio": abrir_desafio(u["id"], "token")}
    familia, refresh = abrir_familia(u["id"])
    return par(u["id"], familia, refresh)


class Verificacao(BaseModel):
    desafio: str = Field(max_length=100)
    codigo: str = Field(max_length=20)


# Segundo passo do login de quem tem MFA (capítulo 8).
@router.post("/api/auth/mfa/verificar", dependencies=[Depends(publica())])
@limitador.limit(POR_IP)
def verificar_mfa(dados: Verificacao, request: Request, response: Response):
    r = resolver_desafio(dados.desafio, dados.codigo.strip())
    if r is None:
        evento("mfa_falhou", ip=request.client.host if request.client else "")
        raise UnauthorizedError("Código inválido.")
    if r["canal"] == "cookie":
        iniciar(request, response, r["usuario_id"])
        return {"usuario": usuarios.publico(usuarios.por_id(r["usuario_id"]))}
    familia, refresh = abrir_familia(r["usuario_id"])
    return par(r["usuario_id"], familia, refresh)


# Cadastro do segundo fator, por quem já está logado.
@router.post("/api/auth/mfa/cadastro")
def cadastrar_mfa(usuario: dict = Depends(autenticada())):
    c = iniciar_cadastro(usuario["id"], usuario["email"])
    if c is None:
        raise BadRequestError("O segundo fator já está ativo.")
    return c


class Ativacao(BaseModel):
    codigo: str = Field(max_length=10)


@router.post("/api/auth/mfa/ativar")
def ativar_mfa(dados: Ativacao, usuario: dict = Depends(autenticada())):
    codigos = ativar(usuario["id"], dados.codigo.strip())
    if codigos is None:
        raise BadRequestError("Código inválido.")
    return {"codigos_recuperacao": codigos}


class Renovacao(BaseModel):
    refresh_token: str = Field(max_length=2000)


# Troca o refresh por um par novo (capítulo 7).
@router.post("/api/auth/refresh", dependencies=[Depends(publica())])
@limitador.limit(POR_IP)
def renovar(dados: Renovacao, request: Request):
    g = girar(dados.refresh_token)
    if g is None:
        raise UnauthorizedError()
    return par(g["usuario_id"], g["familia"], g["refresh"])


# "Sair de todos os dispositivos".
@router.post("/api/auth/logout-all", status_code=204)
def sair_de_todos(usuario: dict = Depends(autenticada())):
    encerrar_todas(usuario["id"])     # cookies
    revogar_todas(usuario["id"])      # apps
    evento("saiu_de_todos", usuario=usuario["id"])
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


class Perfil(BaseModel):
    # Só o nome. Papel e e-mail têm fluxos próprios; campo extra é 400.
    model_config = ConfigDict(extra="forbid")
    nome: str = Field(min_length=2, max_length=100)


# Editar o próprio perfil.
@router.patch("/api/auth/me")
def editar_perfil(dados: Perfil, usuario: dict = Depends(autenticada())):
    usuarios.trocar_nome(usuario["id"], dados.nome)
    return {"usuario": usuarios.publico(usuarios.por_id(usuario["id"]))}


class Solicitacao(BaseModel):
    email: str = Field(max_length=254)


@router.post("/api/auth/reset/solicitar", status_code=202, dependencies=[Depends(publica())])
@limitador.limit(POR_IP)
def solicitar(dados: Solicitacao, request: Request):
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
@limitador.limit(POR_IP)
def confirmar(dados: Confirmacao, request: Request):
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
    evento("senha_redefinida", usuario=u["id"])
    return Response(status_code=204)
