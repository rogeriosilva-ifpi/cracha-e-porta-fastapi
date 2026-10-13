from prontuario.acesso.censo import levantar, problemas
from prontuario.app import criar_app


def test_toda_rota_declara_politica():
    assert problemas(levantar(criar_app())) == []
