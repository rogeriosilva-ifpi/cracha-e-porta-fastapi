"""Cifra em repouso (capítulo 13): AES-256-GCM com chave fora do banco.
O texto cifrado leva a versão da chave ("v1:...") para permitir rotação."""
import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from prontuario.compartilhado.config import config


class Cofre:
    def __init__(self, chaves: dict[str, bytes], atual: str):
        self.chaves, self.atual = chaves, atual

    def cifrar(self, texto: str) -> str:
        iv = os.urandom(12)                           # nunca repetir com a mesma chave
        caixa = AESGCM(self.chaves[self.atual]).encrypt(iv, texto.encode(), None)
        return f"{self.atual}:{base64.b64encode(iv + caixa).decode()}"

    def decifrar(self, caixa: str) -> str:
        versao, _, b64 = caixa.partition(":")
        if versao not in self.chaves or not b64:
            raise ValueError("versão de chave desconhecida")
        bruto = base64.b64decode(b64)
        # alterado? InvalidTag
        return AESGCM(self.chaves[versao]).decrypt(bruto[:12], bruto[12:], None).decode()

    def precisa_recifrar(self, caixa: str) -> bool:
        """Rotação: o que foi cifrado com chave antiga é recifrado com a atual."""
        return not caixa.startswith(f"{self.atual}:")


cofre = Cofre(config.chaves_dados or {"dev": os.urandom(32)}, config.dados_atual)
