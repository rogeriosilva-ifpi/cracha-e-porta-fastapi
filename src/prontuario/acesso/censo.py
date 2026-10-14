"""Censo de rotas: lista toda rota registrada e a política declarada.

Lê as rotas do próprio FastAPI; não depende de convenção humana.
"""
from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.routing import APIRoute, iter_route_contexts

# Rotas que podem ser públicas. Acrescentar aqui exige revisão.
PUBLICAS = {
    "GET /health",
    "POST /api/auth/login",
    "POST /api/auth/token",
    "POST /api/auth/refresh",
    "POST /api/auth/mfa/verificar",
    "GET /api/auth/oidc/iniciar",
    "GET /api/auth/oidc/callback",
    "GET /.well-known/jwks.json",
    "GET /.well-known/oauth-protected-resource",
    "POST /api/auth/reset/solicitar",
    "POST /api/auth/reset/confirmar",
}


@dataclass
class Linha:
    metodo: str
    caminho: str
    politica: dict | None


def levantar(app: FastAPI) -> list[Linha]:
    linhas = []
    # iter_route_contexts achata os roteadores incluídos (com prefixos).
    for rc in iter_route_contexts(app.routes):
        if isinstance(rc.original_route, APIRoute):
            marca = next((d.call.politica for d in rc.dependant.dependencies
                          if hasattr(d.call, "politica")), None)
        else:
            marca = {"publica": True}  # /docs e /openapi.json do framework
        for m in sorted(getattr(rc, "methods", None) or {"GET"}):
            if m != "HEAD":
                linhas.append(Linha(m, rc.path, marca))
    return linhas


def problemas(linhas: list[Linha]) -> list[str]:
    erros = []
    for l in linhas:
        rota = f"{l.metodo} {l.caminho}"
        if l.politica is None:
            erros.append(f"{rota}: sem política declarada")
        elif l.politica.get("publica") and rota not in PUBLICAS:
            erros.append(f"{rota}: pública sem estar em PUBLICAS")
        # "Basta estar logado" só vale para a própria conta (cap. 11).
        elif l.politica.get("autenticada") and not l.caminho.startswith("/api/auth/"):
            erros.append(f"{rota}: só autenticada; declare uma permissão")
    return erros
