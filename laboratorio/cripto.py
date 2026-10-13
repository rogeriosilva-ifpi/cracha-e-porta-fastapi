"""laboratorio/cripto.py — as ferramentas do capítulo 2, rodando.

A assinatura com par de chaves (Ed25519) entra no capítulo 6, com
pyjwt[crypto]; a biblioteca padrão do Python não a oferece.

uso: uv run python laboratorio/cripto.py
"""
import base64
import hashlib
import hmac
import random
import secrets
import time


def sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


print("1 · ALEATORIEDADE")
print("random.random  :", random.random())
print("secrets.token  :", secrets.token_urlsafe(24))

print("\n2 · HASH SHA-256")
print("prescrever →", sha256("prescrever")[:24] + "…")
print("prescreveR →", sha256("prescreveR")[:24] + "…")
print("de novo    →", sha256("prescrever")[:24] + "…")
n, t0 = 200_000, time.perf_counter()
for i in range(n):
    sha256(f"senha{i}")
por_seg = round(n / (time.perf_counter() - t0))
print("velocidade :", f"{por_seg:,}".replace(",", "."), "hashes/s")

print("\n3 · HMAC: ASSINATURA COM SEGREDO")
segredo = secrets.token_bytes(32)


def assinar(m: str) -> str:
    return hmac.new(segredo, m.encode(), "sha256").hexdigest()


def confere(m: str, tag: str) -> bool:
    return hmac.compare_digest(assinar(m), tag)


msg = "paciente=p1;acao=ler"
tag = assinar(msg)
print("mensagem   :", msg)
print("assinatura :", tag[:24] + "…")
print("original confere?   ", confere(msg, tag))
print("p1→p2 confere?      ", confere("paciente=p2;acao=ler", tag))
forjada = hmac.new(b"chute", b"paciente=p2;acao=ler", "sha256").hexdigest()
print("forjada sem segredo?", confere("paciente=p2;acao=ler", forjada))

print("\n4 · BASE64 NÃO É SEGREDO")
cod = base64.urlsafe_b64encode(b'{"usuario":"ana","papel":"admin"}').decode()
print("codificado  :", cod)
print("decodificado:", base64.urlsafe_b64decode(cod).decode())
