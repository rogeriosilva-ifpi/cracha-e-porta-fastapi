"""Repositório de usuários. Toda consulta é parametrizada (?)."""
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from prontuario.acesso.senhas import senhas
from prontuario.compartilhado.banco import consultar, executar


def _de_linha(r: dict) -> dict:
    r["passwordHash"] = r.pop("password_hash")
    return r


def publico(u: dict) -> dict:
    return {k: v for k, v in u.items() if k != "passwordHash"}


def por_email(email: str) -> dict | None:
    r = consultar("SELECT * FROM usuarios WHERE email = ?", email.lower())
    return _de_linha(r[0]) if r else None


def por_id(id_: str) -> dict | None:
    r = consultar("SELECT * FROM usuarios WHERE id = ?", id_)
    return _de_linha(r[0]) if r else None


def listar() -> list[dict]:
    return [_de_linha(r) for r in consultar("SELECT * FROM usuarios")]


def criar(u: dict) -> dict:
    executar("INSERT INTO usuarios (id, nome, email, papel, password_hash) VALUES (?, ?, ?, ?, ?)",
             u["id"], u["nome"], u["email"].lower(), u["papel"], u["passwordHash"])
    return u


def trocar_hash(id_: str, hash_: str) -> None:
    executar("UPDATE usuarios SET password_hash = ? WHERE id = ?", hash_, id_)


# Senhas de LABORATÓRIO, documentadas no README. Nunca faça isso em produção.
SENHAS_DE_LABORATORIO = {
    "admin@hospital.dev": "farol-de-amarracao-2026",
    "ana@hospital.dev": "cajueiro-em-flor-no-quintal",
    "bruno@hospital.dev": "barco-azul-no-delta",
    "carla@hospital.dev": "rede-na-varanda-de-tarde",
}
_SEMENTE = [
    {"id": "u1", "nome": "Admin Geral", "email": "admin@hospital.dev", "papel": "admin"},
    {"id": "u2", "nome": "Dra. Ana", "email": "ana@hospital.dev", "papel": "profissional"},
    {"id": "u3", "nome": "Dr. Bruno", "email": "bruno@hospital.dev", "papel": "profissional"},
    {"id": "u4", "nome": "Carla", "email": "carla@hospital.dev", "papel": "recepcao"},
]
# Bruno foi cadastrado num sistema antigo, com parâmetros fracos:
# o login dele mostra o rehash transparente (capítulo 4).
_LEGADO = PasswordHash((Argon2Hasher(time_cost=1, memory_cost=4096, parallelism=1),))

if not consultar("SELECT id FROM usuarios"):
    for u in _SEMENTE:
        s = SENHAS_DE_LABORATORIO[u["email"]]
        criar({**u, "passwordHash": (_LEGADO if u["id"] == "u3" else senhas).hash(s)})
