# prontuario-fastapi

Laboratório do ebook **Crachá & Porta** — stack FastAPI + Python.

Cada capítulo é uma tag: `git checkout cap01`, `git checkout cap02`…

```bash
uv run python laboratorio/cripto.py  # capítulo 2
uv sync
uv run uvicorn prontuario.app:app --port 8000 --no-server-header
uv run pytest
uv run python scripts/censo.py
python placar.py ataques.http --base http://localhost:8000
```

`prompts/` traz os prompts complementares de cada capítulo (variante
C-P-T-R-F-A e revisão). Leia na branch principal.

## Senhas de laboratório (a partir do capítulo 4)

| usuário | senha |
|---|---|
| admin@hospital.dev | farol-de-amarracao-2026 |
| ana@hospital.dev | cajueiro-em-flor-no-quintal |
| bruno@hospital.dev | barco-azul-no-delta |
| carla@hospital.dev | rede-na-varanda-de-tarde |

Só existem para o laboratório. O banco sobe em memória e é recriado a cada início.

`laboratorio/cripto.py` (capítulo 2) e `cronometro.py` (capítulo 4) são instrumentos do livro.
