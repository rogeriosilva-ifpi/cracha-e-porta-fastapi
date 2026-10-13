"""Dados em memória do Mini-Prontuário. O banco entra no capítulo 4."""
from dataclasses import dataclass, field
from itertools import count
from typing import Literal

Papel = Literal["admin", "profissional", "recepcao"]
HASH = "$argon2id$v=19$m=19456,t=2,p=1$c2FsdGRlbW8$aGFzaGlsdXN0cmF0aXZv"  # ilustrativo


@dataclass
class Usuario:
    id: str
    nome: str
    email: str
    papel: Papel
    passwordHash: str = HASH  # os hashes reais nascem no cap. 4


@dataclass
class Banco:
    usuarios: list[dict] = field(default_factory=lambda: [
        {"id": "u1", "nome": "Admin Geral", "email": "admin@hospital.dev", "papel": "admin", "passwordHash": HASH},
        {"id": "u2", "nome": "Dra. Ana", "email": "ana@hospital.dev", "papel": "profissional", "passwordHash": HASH},
        {"id": "u3", "nome": "Dr. Bruno", "email": "bruno@hospital.dev", "papel": "profissional", "passwordHash": HASH},
        {"id": "u4", "nome": "Carla", "email": "carla@hospital.dev", "papel": "recepcao", "passwordHash": HASH},
    ])
    pacientes: list[dict] = field(default_factory=lambda: [
        {"id": "p1", "nome": "Maria Souza", "cns": "898001234567890", "nascimento": "1958-03-14"},
        {"id": "p2", "nome": "João Lima", "cns": "898009876543210", "nascimento": "1990-11-02"},
    ])
    atendimentos: list[dict] = field(default_factory=lambda: [
        {"id": "e1", "pacienteId": "p1", "profissionalId": "u2", "motivo": "Dor torácica", "status": "aberto"},
        {"id": "e2", "pacienteId": "p2", "profissionalId": "u3", "motivo": "Febre há 3 dias", "status": "aberto"},
    ])
    prescricoes: list[dict] = field(default_factory=lambda: [
        {"id": "m1", "atendimentoId": "e1", "profissionalId": "u2", "medicamento": "AAS 100 mg", "posologia": "1x ao dia"},
        {"id": "m2", "atendimentoId": "e2", "profissionalId": "u3", "medicamento": "Dipirona 500 mg", "posologia": "6/6h se febre"},
    ])


db = Banco()
_seq = count(101)


def novo_id(prefixo: str) -> str:
    return f"{prefixo}{next(_seq)}"


def buscar(lista: list[dict], id_: str) -> dict | None:
    return next((x for x in lista if x["id"] == id_), None)
