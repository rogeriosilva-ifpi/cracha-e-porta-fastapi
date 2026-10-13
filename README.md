# prontuario-fastapi

Laboratório do ebook **Crachá & Porta** — stack FastAPI + Python.

Cada capítulo é uma tag: `git checkout cap01`, `git checkout cap02`…

```bash
uv sync
uv run uvicorn prontuario.app:app --port 8000 --no-server-header
uv run pytest
uv run python scripts/censo.py
python placar.py ataques.http --base http://localhost:8000
```

`prompts/` traz os prompts complementares de cada capítulo (variante
C-P-T-R-F-A e revisão). Leia na branch principal.
