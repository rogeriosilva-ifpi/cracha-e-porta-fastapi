#!/usr/bin/env bash
# portoes.sh — os portões de segurança do Mini-Prontuário (capítulo 14).
# O CI roda exatamente isto; rode também antes de abrir um PR.
# Cada portão que falha derruba o conjunto (código de saída 1).
set -u
PORTA=${PORTA:-3999}
falhas=0
export LC_ALL=C.UTF-8
resumo() {                      # a linha que interessa da saída
  local r
  r=$(echo "$1" | grep -E "Tests |placar:|rotas ·|segredo|vulnerabilit|error|passed|failed" | tail -1)
  r=${r:-sem erros}; r=$(echo "$r" | sed -E 's/^ +//; s/ · [0-9]+ já.*//; s/ no histórico//; s/ defendidos//')
  echo "${r:0:26}"
}
portao() {                      # portao "nome" comando...
  local nome=$1; shift
  local pad; pad=$(printf '%*s' $((22 - ${#nome})) '')   # conta letras, não bytes
  if saida=$("$@" 2>&1); then
    echo "  ok     $nome$pad $(resumo "$saida")"
  else
    echo "  FALHOU $nome$pad $(resumo "$saida")"
    falhas=$((falhas + 1))
  fi
}
servidor_e() {                  # sobe o servidor, roda o comando, derruba
  setsid .venv/bin/uvicorn prontuario.app:app --app-dir src --port $PORTA \
    --no-server-header > /tmp/portoes-servidor.log 2>&1 &
  local pid=$!                  # setsid: o servidor e seus filhos num grupo só
  for _ in $(seq 1 40); do curl -s -o /dev/null "localhost:$PORTA/health" && break; sleep 0.25; done
  "$@"; local r=$?
  kill -- -$pid 2>/dev/null; wait $pid 2>/dev/null   # derruba o grupo inteiro
  return $r
}
ataques() { sed "s#^@base = .*#@base = http://localhost:$PORTA#" "$1" > /tmp/portoes.http
            python3 placar.py /tmp/portoes.http; }
matriz() { PYTHONPATH=src .venv/bin/python scripts/censo.py --json > /tmp/rotas.json &&
           python3 matriz.py /tmp/rotas.json docs/PERMISSOES.md > /tmp/matriz.http &&
           ataques /tmp/matriz.http; }

echo "portões de segurança · prontuario-fastapi"
portao "1 compilação"           .venv/bin/python -m compileall -q src
portao "2 testes"         .venv/bin/python -m pytest -q
portao "3 censo de rotas"          env PYTHONPATH=src .venv/bin/python scripts/censo.py
portao "4 segredos (git)"   python3 varredura.py
portao "5 dependências"            .venv/bin/pip-audit --skip-editable
portao "6 ataques"        servidor_e ataques ataques.http
portao "7 papel × rota"   servidor_e matriz
echo
[ $falhas -eq 0 ] && echo "todos os portões passaram" || echo "$falhas portão(ões) falharam"
exit $(( falhas > 0 ))
