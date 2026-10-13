"""Os mesmos 7 casos contra quatro modelos de acesso (capítulo 10).
uv run python laboratorio/modelos.py"""
import json

from prontuario.acesso.cedar import autorizar_cedar
from prontuario.acesso.decisao import abac, rbac, rbac_com_posse

casos = json.load(open("politicas/casos.json"))
modelos = [("RBAC", rbac), ("+posse", rbac_com_posse), ("ABAC", abac), ("Cedar", autorizar_cedar)]
print("caso".ljust(22) + "".join(n.ljust(7) for n, _ in modelos))
erros = {n: 0 for n, _ in modelos}
for c in casos:
    linha = ""
    for n, m in modelos:
        certo = ("permitido" if m(c["sujeito"], c["recurso"], c["contexto"])["permitido"] else "negado") == c["esperado"]
        erros[n] += not certo
        linha += ("ok" if certo else "ERRO").ljust(7)
    print(c["rotulo"].ljust(22) + linha)
print("\n" + "erros".ljust(22) + "".join(str(erros[n]).ljust(7) for n, _ in modelos))
