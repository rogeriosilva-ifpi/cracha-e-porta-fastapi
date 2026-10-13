"""Defesas da porta de entrada (capítulo 9). Por IP: slowapi.
Por conta: contador de FALHAS, nosso, com duas janelas."""
import math
import time

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Qualquer pedido às rotas de autenticação: 100 por IP a cada 15 min.
limitador = Limiter(key_func=get_remote_address)
POR_IP = "100/15minutes"

# Falhas de senha. "conta+ip" pega o ataque concentrado sem deixar um
# atacante trancar a vítima de outro lugar; "conta" pega o ataque
# espalhado por muitos IPs.
REGRAS = (("conta+ip", 5, 15 * 60), ("conta", 50, 60 * 60))
_janelas: dict[str, list] = {}           # chave -> [falhas, até]


def _ip(request: Request) -> str:
    return request.client.host if request.client else ""


def _chave(regra: str, email: str, request: Request) -> str:
    email = email.strip().lower()
    return f"conta:{email}" if regra == "conta" else f"conta+ip:{email}|{_ip(request)}"


def bloqueio(email: str, request: Request) -> int | None:
    """Segundos até liberar, se alguma regra estourou."""
    agora = time.time()
    for nome, limite, _ in REGRAS:
        j = _janelas.get(_chave(nome, email, request))
        if j and j[1] > agora and j[0] >= limite:
            return math.ceil(j[1] - agora)
    return None


def registrar_falha(email: str, request: Request) -> None:
    agora = time.time()
    for nome, _, janela in REGRAS:
        k = _chave(nome, email, request)
        j = _janelas.get(k)
        if not j or j[1] <= agora:
            _janelas[k] = [1, agora + janela]
        else:
            j[0] += 1


def limpar_falhas(email: str, request: Request) -> None:
    """Senha certa: zera as falhas daquela conta naquele IP."""
    _janelas.pop(_chave("conta+ip", email, request), None)


def zerar_limites() -> None:
    _janelas.clear()
    limitador.reset()
