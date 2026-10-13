"""Ponto de decisão de acesso (capítulo 10): a mesma regra em três
modelos, para comparar. O contrato é sempre o mesmo:
autorizar(sujeito, recurso, contexto) -> {"permitido", "motivo"}."""
from datetime import datetime

from prontuario.acesso.permissoes import pode
from prontuario.compartilhado.dados import escala


def _sim(motivo: str) -> dict:
    return {"permitido": True, "motivo": motivo}


def _nao(motivo: str) -> dict:
    return {"permitido": False, "motivo": motivo}


def rbac(s: dict, r: dict, c: dict) -> dict:
    """RBAC puro: só o papel importa."""
    return _sim("papel com rx:create") if pode(s["papel"], "rx:create") else _nao("papel sem rx:create")


def rbac_com_posse(s: dict, r: dict, c: dict) -> dict:
    """RBAC com posse: papel + ser o autor do atendimento."""
    if not pode(s["papel"], "rx:create"):
        return _nao("papel sem rx:create")
    return _sim("autor do atendimento") if r["autor"] == s["id"] else _nao("não é o autor do atendimento")


def abac(s: dict, r: dict, c: dict) -> dict:
    """ABAC: atributos do sujeito, do recurso e do ambiente."""
    if s.get("suspenso"):
        return _nao("registro suspenso")
    if not pode(s["papel"], "rx:create"):
        return _nao("papel sem rx:create")
    if r["autor"] != s["id"]:
        return _nao("não é o autor do atendimento")
    if r["status"] != "aberto":
        return _nao("atendimento finalizado")
    if not c["de_plantao"]:
        return _nao("fora do plantão")
    return _sim("autor, atendimento aberto, de plantão")


def de_plantao(usuario_id: str, agora: datetime) -> bool:
    """Fonte de atributo do ambiente: está de plantão agora?"""
    minutos = lambda h: int(h[:2]) * 60 + int(h[3:])
    m = agora.hour * 60 + agora.minute
    for p in escala:
        if p["usuario_id"] != usuario_id:
            continue
        ini, fim = minutos(p["inicio"]), minutos(p["fim"])
        if (ini <= m < fim) if ini < fim else (m >= ini or m < fim):  # vira a meia-noite
            return True
    return False
