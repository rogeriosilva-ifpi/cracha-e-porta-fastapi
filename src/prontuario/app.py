import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from prontuario.acesso.limites import limitador
from prontuario.compartilhado.config import config
from prontuario.acesso.politica import publica
from prontuario.admin import rotas as admin
from prontuario.atendimentos import rotas as atendimentos
from prontuario.auth import chaves, oidc
from prontuario.auth import rotas as auth
from prontuario.http import erros, origem
from prontuario.pacientes import rotas as pacientes
from prontuario.prescricoes import rotas as prescricoes

ORIGENS = config.origens
DOCS = os.getenv("PRONTUARIO_DOCS") == "1"  # mapa da API só quando pedido


def criar_app() -> FastAPI:
    app = FastAPI(title="Mini-Prontuário",
                  docs_url="/docs" if DOCS else None,
                  redoc_url=None,
                  openapi_url="/openapi.json" if DOCS else None)

    # BORDA: origem e cabeçalhos de segurança.
    app.add_middleware(CORSMiddleware, allow_origins=ORIGENS,
                       allow_credentials=True,
                       allow_methods=["GET", "POST", "PATCH", "DELETE"],
                       allow_headers=["Content-Type", "Authorization"])

    origem.instalar(app, ORIGENS)

    @app.middleware("http")
    async def cabecalhos(request: Request, call_next):
        resp = await call_next(request)
        resp.headers["X-Content-Type-Options"] = "nosniff"
        resp.headers["X-Frame-Options"] = "DENY"
        resp.headers["Referrer-Policy"] = "no-referrer"
        return resp

    @app.get("/health", dependencies=[Depends(publica())])
    def health():
        return {"status": "ok"}

    app.state.limiter = limitador     # slowapi (capítulo 9)
    for m in (pacientes, atendimentos, prescricoes, admin, auth, oidc, chaves):
        app.include_router(m.router)

    erros.instalar(app)  # FIM DO PIPELINE: todo erro passa por aqui
    return app


app = criar_app()
