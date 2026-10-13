"""Defesa contra CSRF: ação vinda de outro site é recusada (capítulo 5)."""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

SEGUROS = {"GET", "HEAD", "OPTIONS"}


def instalar(app: FastAPI, origens: list[str]) -> None:
    @app.middleware("http")
    async def verificar_origem(request: Request, call_next):
        if request.method not in SEGUROS:
            origem = request.headers.get("origin")
            if (origem and origem not in origens) or \
               request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"error": "Origem não permitida."}, status_code=403)
        return await call_next(request)
