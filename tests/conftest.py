import pytest

from prontuario.acesso.limites import zerar_limites


@pytest.fixture(autouse=True)
def _limites_zerados():
    """Cada teste começa sem falhas acumuladas por outros testes."""
    zerar_limites()
