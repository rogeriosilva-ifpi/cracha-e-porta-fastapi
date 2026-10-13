from dataclasses import asdict

from fastapi import APIRouter

from prontuario.compartilhado.dados import db

router = APIRouter()


# "Só pra testar rapidinho" — escrita num sábado e nunca removida.
@router.get("/api/debug/dump")
def dump():
    return asdict(db)
