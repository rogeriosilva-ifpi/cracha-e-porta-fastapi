"""Banco SQLite. Por padrão em memória: cada vez que o servidor sobe,
começa limpo e semeado. Defina DB_PATH para gravar em arquivo."""
import os
import sqlite3
import threading

banco = sqlite3.connect(os.getenv("DB_PATH", ":memory:"), check_same_thread=False)
banco.row_factory = sqlite3.Row
trava = threading.Lock()  # rotas síncronas rodam em várias threads

banco.executescript("""
  CREATE TABLE IF NOT EXISTS usuarios (
    id            TEXT PRIMARY KEY,
    nome          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    papel         TEXT NOT NULL,
    password_hash TEXT NOT NULL
  );
  CREATE TABLE IF NOT EXISTS redefinicoes (
    token_hash TEXT PRIMARY KEY,   -- sha256 do token, nunca o token
    usuario_id TEXT NOT NULL,
    expira_em  INTEGER NOT NULL,   -- epoch em ms
    usado      INTEGER NOT NULL DEFAULT 0
  );
  CREATE TABLE IF NOT EXISTS sessoes (
    id_hash    TEXT PRIMARY KEY,   -- sha256 do token do cookie
    usuario_id TEXT NOT NULL,
    criada_em  INTEGER NOT NULL,
    ultimo_uso INTEGER NOT NULL,
    expira_em  INTEGER NOT NULL    -- limite absoluto
  );
  CREATE TABLE IF NOT EXISTS familias (
    id         TEXT PRIMARY KEY,   -- um login de app = uma família
    usuario_id TEXT NOT NULL,
    criada_em  INTEGER NOT NULL,
    expira_em  INTEGER NOT NULL,   -- limite absoluto da família
    revogada   INTEGER NOT NULL DEFAULT 0
  );
  CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_hash TEXT PRIMARY KEY,   -- sha256 do refresh, nunca o token
    familia    TEXT NOT NULL,
    expira_em  INTEGER NOT NULL,
    usado      INTEGER NOT NULL DEFAULT 0
  );
""")


def consultar(sql: str, *args) -> list[dict]:
    with trava:
        return [dict(r) for r in banco.execute(sql, args).fetchall()]


def executar(sql: str, *args) -> int:
    """Executa e devolve quantas linhas mudaram."""
    with trava:
        n = banco.execute(sql, args).rowcount
        banco.commit()
        return n
