import pytest

from prontuario.acesso.limites import zerar_limites


@pytest.fixture(autouse=True)
def _limites_zerados():
    """Cada teste começa sem falhas acumuladas por outros testes."""
    zerar_limites()


@pytest.fixture
def plantao(monkeypatch):
    """Fixa o relógio da rota de prescrição numa hora escolhida pelo teste."""
    from datetime import datetime

    from prontuario.prescricoes import rotas

    def fixar(hora: int):
        class Relogio(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 10, 13, hora, 0)
        monkeypatch.setattr(rotas, "datetime", Relogio)
    return fixar
