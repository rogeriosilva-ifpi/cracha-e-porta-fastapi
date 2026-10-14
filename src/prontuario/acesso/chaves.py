"""Chaves de API com escopo (capítulo 15): a credencial de máquinas,
scripts e agentes. Age em nome de uma pessoa, mas só com o subconjunto
de permissões que ela escolheu, e por tempo limitado."""
import hashlib
import json
import re
import secrets
import time

from prontuario.compartilhado.banco import consultar, executar

MAX_DIAS = 90
MAX_ATIVAS = 10
FORMATO = re.compile(r"^mp_([0-9a-f]{8})_([A-Za-z0-9_-]{43})$")


def agora() -> int:
    return int(time.time() * 1000)


def _sha256(s: str) -> str:
    # sha256 basta: o segredo tem 256 bits aleatórios, não é uma senha
    # escolhida por gente. Não há dicionário para testar contra ele.
    return hashlib.sha256(s.encode()).hexdigest()


def _visivel(l: dict) -> dict:
    return {"id": l["id"], "nome": l["nome"], "escopos": json.loads(l["escopos"]),
            "criada_em": l["criada_em"], "expira_em": l["expira_em"],
            "ultimo_uso": l["ultimo_uso"]}


def criar_chave(usuario_id: str, nome: str, escopos: list[str], dias: int) -> dict:
    """Cria a chave. O texto dela sai daqui uma única vez."""
    id_ = secrets.token_hex(4)
    chave = f"mp_{id_}_{secrets.token_urlsafe(32)}"
    t = agora()
    executar("""INSERT INTO chaves_api (id, hash, usuario_id, nome, escopos,
                criada_em, expira_em) VALUES (?, ?, ?, ?, ?, ?, ?)""",
             id_, _sha256(chave), usuario_id, nome, json.dumps(escopos),
             t, t + dias * 24 * 3600 * 1000)
    return {"chave": chave, **_visivel(consultar("SELECT * FROM chaves_api WHERE id = ?", id_)[0])}


def verificar_chave(chave: str) -> dict | None:
    """Confere a chave: formato, hash, revogação e validade."""
    m = FORMATO.match(chave)
    if not m:
        return None                                   # nem vai ao banco
    linhas = consultar("""SELECT * FROM chaves_api WHERE id = ? AND hash = ?
                          AND revogada = 0 AND expira_em > ?""",
                       m[1], _sha256(chave), agora())
    if not linhas:
        return None
    executar("UPDATE chaves_api SET ultimo_uso = ? WHERE id = ?", agora(), m[1])
    l = linhas[0]
    return {"usuario_id": l["usuario_id"], "id": l["id"], "escopos": json.loads(l["escopos"])}


def listar_chaves(usuario_id: str) -> list[dict]:
    """Só as chaves da própria pessoa; nunca o hash."""
    return [_visivel(l) for l in consultar(
        """SELECT * FROM chaves_api WHERE usuario_id = ? AND revogada = 0
           AND expira_em > ? ORDER BY criada_em""", usuario_id, agora())]


def revogar_chave(id_: str, usuario_id: str) -> bool:
    """Revoga uma chave da própria pessoa. A de outro "não existe"."""
    return executar("""UPDATE chaves_api SET revogada = 1
                       WHERE id = ? AND usuario_id = ? AND revogada = 0""", id_, usuario_id) == 1


def revogar_chaves_de(usuario_id: str) -> None:
    """Desligamento e troca de papel: as chaves vão junto."""
    executar("UPDATE chaves_api SET revogada = 1 WHERE usuario_id = ?", usuario_id)
