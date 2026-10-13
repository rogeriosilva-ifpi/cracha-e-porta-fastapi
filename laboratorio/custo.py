"""laboratorio/custo.py — quanto custa um palpite? (capítulo 4)

uso: uv run python laboratorio/custo.py
"""
import hashlib
import time

from prontuario.acesso.senhas import senhas


def por_segundo(n, f):
    t0 = time.perf_counter()
    for i in range(n):
        f(i)
    return n / (time.perf_counter() - t0)


fmt = lambda v: f"{round(v):,}".replace(",", ".").rjust(9)
sha = por_segundo(200_000, lambda i: hashlib.sha256(f"senha{i}".encode()).digest())
a2 = por_segundo(20, lambda i: senhas.hash(f"senha{i}"))
print("palpites por segundo, 1 núcleo:")
print("sha256   :", fmt(sha))
print("argon2id :", fmt(a2))
print("razão    :", fmt(sha / a2), "× mais caro")
