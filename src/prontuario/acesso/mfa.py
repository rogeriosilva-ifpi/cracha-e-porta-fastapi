"""Segundo fator: TOTP (RFC 6238) e códigos de recuperação (capítulo 8)."""
import hashlib
import hmac
import re
import secrets
import time

import pyotp

from prontuario.compartilhado.banco import consultar, executar
from prontuario.compartilhado.cofre import cofre

PERIODO_S = 30
DESAFIO_MS = 5 * 60 * 1000          # entre a senha e o código
MAX_TENTATIVAS = 5                  # por desafio


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _linha(usuario_id: str) -> dict | None:
    # O segredo TOTP é guardado CIFRADO (cap. 13): o banco sozinho não basta.
    r = consultar("SELECT * FROM mfa WHERE usuario_id = ?", usuario_id)
    return {**r[0], "segredo": cofre.decifrar(r[0]["segredo"])} if r else None


def mfa_ativo(usuario_id: str) -> bool:
    m = _linha(usuario_id)
    return bool(m and m["ativo"])


def iniciar_cadastro(usuario_id: str, email: str) -> dict | None:
    """Passo 1 do cadastro: segredo novo, ainda inativo."""
    if mfa_ativo(usuario_id):
        return None
    segredo = pyotp.random_base32(32)                 # 160 bits
    executar("INSERT OR REPLACE INTO mfa VALUES (?, ?, 0, 0)", usuario_id, cofre.cifrar(segredo))
    uri = pyotp.TOTP(segredo).provisioning_uri(name=email, issuer_name="Mini-Prontuário")
    return {"segredo": segredo, "uri": uri}           # vira QR code


def conferir_totp(usuario_id: str, codigo: str) -> bool:
    """Confere o código de 6 dígitos (±30 s); o mesmo código não vale duas vezes."""
    m = _linha(usuario_id)
    if not m:
        return False
    totp, agora = pyotp.TOTP(m["segredo"]), time.time()
    for delta in (-1, 0, 1):
        if hmac.compare_digest(totp.at(agora + delta * PERIODO_S), codigo):
            passo = int(agora // PERIODO_S) + delta
            return executar("UPDATE mfa SET ultimo_passo = ? WHERE usuario_id = ? "
                            "AND ultimo_passo < ?", passo, usuario_id, passo) == 1
    return False


def ativar(usuario_id: str, codigo: str) -> list[str] | None:
    """Passo 2 do cadastro: prova que o app gera códigos; entrega os de recuperação."""
    if mfa_ativo(usuario_id) or not conferir_totp(usuario_id, codigo):
        return None
    executar("UPDATE mfa SET ativo = 1 WHERE usuario_id = ?", usuario_id)
    executar("DELETE FROM codigos_recuperacao WHERE usuario_id = ?", usuario_id)
    codigos = []
    for _ in range(10):
        c = "-".join(re.findall(".{4}", secrets.token_hex(6)))
        executar("INSERT INTO codigos_recuperacao VALUES (?, ?, 0)", _sha256(c), usuario_id)
        codigos.append(c)                             # mostrado uma única vez
    return codigos


def _usar_recuperacao(usuario_id: str, codigo: str) -> bool:
    return executar("UPDATE codigos_recuperacao SET usado = 1 WHERE hash = ? "
                    "AND usuario_id = ? AND usado = 0", _sha256(codigo), usuario_id) == 1


def abrir_desafio(usuario_id: str, canal: str) -> str:
    """Senha certa de quem tem MFA: em vez de sessão, um desafio de 5 minutos."""
    desafio = secrets.token_urlsafe(32)
    executar("INSERT INTO desafios_mfa VALUES (?, ?, ?, ?, 0)", _sha256(desafio),
             usuario_id, canal, int(time.time() * 1000) + DESAFIO_MS)
    return desafio


def resolver_desafio(desafio: str, codigo: str) -> dict | None:
    """Resolve o desafio com TOTP ou código de recuperação; 5 tentativas no máximo."""
    h = _sha256(desafio)
    r = consultar("SELECT * FROM desafios_mfa WHERE hash = ?", h)
    if not r or r[0]["expira_em"] < time.time() * 1000 or r[0]["tentativas"] >= MAX_TENTATIVAS:
        return None
    d = r[0]
    executar("UPDATE desafios_mfa SET tentativas = tentativas + 1 WHERE hash = ?", h)
    ok = (conferir_totp(d["usuario_id"], codigo) if re.fullmatch(r"\d{6}", codigo)
          else _usar_recuperacao(d["usuario_id"], codigo))
    if not ok:
        return None
    executar("DELETE FROM desafios_mfa WHERE hash = ?", h)     # uso único
    return {"usuario_id": d["usuario_id"], "canal": d["canal"]}
