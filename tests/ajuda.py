"""Login de verdade para os testes: devolve o cabeçalho Cookie da sessão."""
from fastapi.testclient import TestClient

from prontuario.acesso.usuarios import SENHAS_DE_LABORATORIO


def entrar(cli: TestClient, email: str, senha: str | None = None) -> dict:
    r = cli.post("/api/auth/login", json={"email": email, "senha": senha or SENHAS_DE_LABORATORIO[email]})
    assert r.status_code == 200, r.text
    cli.cookies.clear()  # o teste decide quando mandar o cookie
    cookies = r.headers.get_list("set-cookie")
    return {"Cookie": "; ".join(c.split(";")[0] for c in cookies)}
