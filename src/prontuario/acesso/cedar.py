"""A mesma regra em Cedar (capítulo 10), avaliada dentro do processo.
O arquivo politicas/prontuario.cedar é compartilhado com o Express."""
import re
from pathlib import Path

import cedarpy

TEXTO = (Path(__file__).resolve().parents[3] / "politicas" / "prontuario.cedar").read_text()
# Cedar numera as políticas na ordem do arquivo (policy0, policy1...);
# o @id de cada uma vira o motivo legível.
NOMES = re.findall(r'@id\("([^"]+)"\)', TEXTO)


def _nome(pid: str) -> str:
    i = int(pid.removeprefix("policy"))
    return NOMES[i] if i < len(NOMES) else pid


def _uid(tipo: str, id_: str) -> dict:
    return {"__entity": {"type": tipo, "id": id_}}


def autorizar_cedar(s: dict, r: dict, c: dict, politicas: str = TEXTO) -> dict:
    resposta = cedarpy.is_authorized(
        {"principal": f'Usuario::"{s["id"]}"', "action": 'Action::"prescrever"',
         "resource": f'Atendimento::"{r["id"]}"', "context": c},
        politicas,
        [{"uid": _uid("Usuario", s["id"]), "attrs": {"suspenso": s.get("suspenso", False)},
          "parents": [_uid("Papel", s["papel"])]},
         {"uid": _uid("Atendimento", r["id"]),
          "attrs": {"autor": _uid("Usuario", r["autor"]), "status": r["status"]}, "parents": []}])
    if resposta.diagnostics.errors or resposta.decision not in (
            cedarpy.Decision.Allow, cedarpy.Decision.Deny):
        return {"permitido": False, "motivo": "erro na política"}     # falha fechada
    quem = [_nome(p) for p in resposta.diagnostics.reasons]
    if resposta.allowed:
        return {"permitido": True, "motivo": ", ".join(quem)}
    return {"permitido": False, "motivo": ", ".join(quem) or "nenhuma política permite"}
