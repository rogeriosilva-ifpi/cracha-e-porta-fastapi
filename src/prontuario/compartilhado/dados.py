"""Dados clínicos em memória. Usuários e credenciais moram no SQLite
(compartilhado/banco.py) desde o capítulo 4."""
from dataclasses import dataclass, field
from itertools import count
from typing import Literal

Papel = Literal["admin", "profissional", "recepcao"]


@dataclass
class Banco:
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


# Escala de plantões (capítulo 10): horário local, pode virar a meia-noite.
escala = [
    {"usuario_id": "u2", "inicio": "07:00", "fim": "19:00"},   # Ana, diurno
    {"usuario_id": "u3", "inicio": "19:00", "fim": "07:00"},   # Bruno, noturno
    {"usuario_id": "u5", "inicio": "07:00", "fim": "19:00"},   # Eva, diurno
]
