from fastapi import FastAPI

from prontuario.admin import rotas as admin
from prontuario.atendimentos import rotas as atendimentos
from prontuario.debug import rotas as debug
from prontuario.pacientes import rotas as pacientes
from prontuario.prescricoes import rotas as prescricoes


def criar_app() -> FastAPI:
    app = FastAPI(title="Mini-Prontuário")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    for m in (pacientes, atendimentos, prescricoes, admin, debug):
        app.include_router(m.router)
    return app


app = criar_app()
