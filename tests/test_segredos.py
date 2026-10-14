import base64
import os

import pytest
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from prontuario.acesso.tokens import chave_do_pem
from prontuario.acesso.usuarios import TOTP_DE_LABORATORIO
from prontuario.compartilhado.banco import consultar
from prontuario.compartilhado.cofre import Cofre
from prontuario.compartilhado.config import carregar_config


def pem():
    return Ed25519PrivateKey.generate().private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()).decode()


def chave32():
    return base64.b64encode(os.urandom(32)).decode()


# configuração: falha cedo em produção

def test_sem_segredos_nao_sobe_e_diz_o_que_falta():
    with pytest.raises(ValueError, match="CORS_ORIGINS ausente; CHAVE_JWT_ATUAL ausente; CHAVE_DADOS ausente"):
        carregar_config({"NODE_ENV": "production"})


def test_valor_de_exemplo_nao_sobe():
    with pytest.raises(ValueError, match="com valor de exemplo"):
        carregar_config({"NODE_ENV": "production", "CORS_ORIGINS": "https://x.exemplo",
                         "CHAVE_JWT_ATUAL": "troque-por-uma-chave", "CHAVE_DADOS": "v1:troque"})


def test_completa_sobe_com_anteriores_so_para_conferir():
    c = carregar_config({"NODE_ENV": "production", "CORS_ORIGINS": "https://prontuario.hospital",
                         "CHAVE_JWT_ATUAL": pem(), "CHAVE_JWT_ANTERIOR": pem(),
                         "CHAVE_DADOS": f"v2:{chave32()}", "CHAVE_DADOS_ANTERIOR": f"v1:{chave32()}"})
    assert len(c.chaves_jwt) == 2 and sorted(c.chaves_dados) == ["v1", "v2"] and c.dados_atual == "v2"


def test_desenvolvimento_sobe_sem_nada():
    assert carregar_config({}).producao is False


# cifra em repouso

V1, V2 = os.urandom(32), os.urandom(32)
antigo, novo = Cofre({"v1": V1}, "v1"), Cofre({"v1": V1, "v2": V2}, "v2")


def test_ida_e_volta_sem_revelar():
    c = novo.cifrar("JBSWY3DPEHPK3PXP")
    assert c.startswith("v2:") and "JBSWY3DPEHPK3PXP" not in c
    assert novo.decifrar(c) == "JBSWY3DPEHPK3PXP"


def test_um_byte_alterado_e_erro():
    bruto = bytearray(base64.b64decode(novo.cifrar("segredo totp")[3:]))
    bruto[-1] ^= 1
    with pytest.raises(InvalidTag):
        novo.decifrar("v2:" + base64.b64encode(bytes(bruto)).decode())


def test_rotacao_v2_le_o_que_a_v1_cifrou():
    velho = antigo.cifrar("segredo da Eva")
    assert novo.decifrar(velho) == "segredo da Eva" and novo.precisa_recifrar(velho)


def test_banco_guarda_o_totp_da_eva_cifrado():
    s = consultar("SELECT segredo FROM mfa WHERE usuario_id = 'u5'")[0]["segredo"]
    assert TOTP_DE_LABORATORIO not in s and s.startswith("dev:")


# chave do JWT vinda do ambiente

def test_kid_e_a_impressao_digital():
    p = pem()
    assert chave_do_pem(p)["kid"] == chave_do_pem(p)["kid"] != chave_do_pem(pem())["kid"]
