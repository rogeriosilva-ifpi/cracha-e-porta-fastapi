"""uso: uv run python scripts/censo.py"""
import sys

from prontuario.acesso.censo import levantar, problemas
from prontuario.app import criar_app

linhas = levantar(criar_app())
for l in linhas:
    p = ("— NENHUMA —" if l.politica is None
         else "pública" if l.politica.get("publica") else l.politica["permissao"])
    linha = f"{l.metodo:<6} {l.caminho}"
    print(f"{linha:<29}{p}" if len(linha) <= 28 else f"{linha}\n{'':<29}{p}")
erros = problemas(linhas)
print(f"\n{len(linhas)} rotas · {len(erros)} problema(s)")
for e in erros:
    print(f"✗ {e}")
sys.exit(1 if erros else 0)
