"""Senhas: argon2id lento de propósito + política NIST SP 800-63B-4."""
import secrets
from pathlib import Path

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# 19 MiB, 2 iterações, paralelismo 1 (mínimo OWASP)
senhas = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),))

# Verificado quando o e-mail NÃO existe, para o tempo não denunciar.
HASH_FICTICIO = senhas.hash(secrets.token_hex(32))

_LISTA = Path(__file__).resolve().parents[3] / "dados" / "senhas-comuns.txt"
BLOQUEIO = {l.strip().lower() for l in _LISTA.read_text().splitlines()
            if l.strip() and not l.startswith("#")}
MIN, MAX = 15, 256


def motivo_de_recusa(senha: str, email: str) -> str | None:
    """Devolve o motivo da recusa, ou None se a senha é aceitável."""
    if len(senha) < MIN:
        return f"A senha precisa ter ao menos {MIN} caracteres."
    if len(senha) > MAX:
        return f"A senha pode ter no máximo {MAX} caracteres."
    s = senha.lower()
    if s in BLOQUEIO:
        return "Essa senha é comum demais. Escolha outra."
    nome = email.split("@")[0].lower()
    if nome in s or "prontuario" in s:
        return "A senha não pode conter seu e-mail nem o nome do sistema."
    return None
