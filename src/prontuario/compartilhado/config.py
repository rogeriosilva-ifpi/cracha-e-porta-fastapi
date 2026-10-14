"""Configuração e segredos (capítulo 13). Tudo vem do ambiente, nunca do
código nem do git. Em produção, faltar um segredo ou usar o valor de
exemplo impede o servidor de subir: falha cedo, falha alto."""
import base64
import os
import re
import sys
from dataclasses import dataclass, field

EXEMPLO = re.compile(r"troque|changeme|exemplo|segredo|xxx", re.I)


@dataclass
class Config:
    producao: bool
    origens: list[str]
    chaves_jwt: list[str] = field(default_factory=list)          # PEM; [0] assina
    chaves_dados: dict[str, bytes] = field(default_factory=dict)  # versão -> chave
    dados_atual: str = "dev"


def _versao_e_chave(v: str) -> tuple[str, bytes] | None:
    versao, _, b64 = v.partition(":")
    try:
        chave = base64.b64decode(b64, validate=True)
    except ValueError:
        return None
    return (versao, chave) if versao and len(chave) == 32 else None


def carregar_config(env: dict = os.environ) -> Config:
    producao = env.get("NODE_ENV") == "production" or env.get("AMBIENTE") == "producao"
    erros = []

    def exigir(nome):
        v = env.get(nome)
        if not v:
            if producao:
                erros.append(f"{nome} ausente")
            return None
        if producao and EXEMPLO.search(v):
            erros.append(f"{nome} com valor de exemplo")
        return v

    origens, jwt, dados = exigir("CORS_ORIGINS"), exigir("CHAVE_JWT_ATUAL"), exigir("CHAVE_DADOS")
    atual = _versao_e_chave(dados) if dados else None
    if dados and not atual:
        erros.append("CHAVE_DADOS deve ser versao:base64 de 32 bytes")
    if erros:
        raise ValueError("Configuração inválida para produção: " + "; ".join(erros))
    chaves_dados = {}
    for v in (env.get("CHAVE_DADOS_ANTERIOR"), dados):          # a anterior só decifra
        par = v and _versao_e_chave(v)
        if par:
            chaves_dados[par[0]] = par[1]
    return Config(producao=producao,
                  origens=(origens or "http://localhost:5173").split(","),
                  chaves_jwt=[p.replace("\\n", "\n") for p in (jwt, env.get("CHAVE_JWT_ANTERIOR")) if p],
                  chaves_dados=chaves_dados,
                  dados_atual=atual[0] if atual else "dev")


try:
    config = carregar_config()
except ValueError as e:
    print(e, file=sys.stderr)          # sem pilha, sem valores
    sys.exit(1)
