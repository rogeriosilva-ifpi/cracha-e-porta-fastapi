"""Tradução de erros: o ÚNICO lugar que monta resposta de erro.

Falha fechado: o que não reconhecemos vira 500 genérico.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi.errors import RateLimitExceeded

from prontuario.auth.chaves import METADADOS_URL
from prontuario.compartilhado.erros import HttpError, TooManyRequestsError, UnauthorizedError

log = logging.getLogger("prontuario")


def instalar(app: FastAPI) -> None:
    @app.exception_handler(HttpError)
    async def http_error(_: Request, e: HttpError):
        cab = {"Retry-After": str(e.retry_after_s)} if isinstance(e, TooManyRequestsError) else {}
        if isinstance(e, UnauthorizedError):   # RFC 9728: onde ler como se autenticar
            cab["WWW-Authenticate"] = f'Bearer resource_metadata="{METADADOS_URL}"'
        return JSONResponse({"error": e.mensagem}, status_code=e.status, headers=cab)

    @app.exception_handler(RateLimitExceeded)          # limite por IP (slowapi)
    async def limite_ip(_: Request, e: RateLimitExceeded):
        return JSONResponse({"error": TooManyRequestsError.mensagem}, status_code=429,
                            headers={"Retry-After": "900"})

    @app.exception_handler(RequestValidationError)
    async def validacao(_: Request, e: RequestValidationError):
        campos = [".".join(str(p) for p in err["loc"][1:]) for err in e.errors()]
        if any(err["type"] == "json_invalid" for err in e.errors()):
            return JSONResponse({"error": "JSON malformado."}, status_code=400)
        return JSONResponse({"error": "Dados inválidos.", "campos": campos}, status_code=400)

    @app.exception_handler(StarletteHTTPException)
    async def starlette(_: Request, e: StarletteHTTPException):
        msg = "Rota não encontrada." if e.status_code == 404 else "Requisição recusada."
        return JSONResponse({"error": msg}, status_code=e.status_code)

    @app.exception_handler(Exception)
    async def inesperado(_: Request, e: Exception):
        log.exception("erro não tratado")          # detalhe só no log
        return JSONResponse({"error": "Erro interno."}, status_code=500)
