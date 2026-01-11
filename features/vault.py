import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class NeuralVault:
    def __init__(self, password: str):
        # Derivação de chave segura usando PBKDF2
        salt = b'r2_neural_salt_fixed' # Em um sistema real, o salt seria único por usuário
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)

    def proteger(self, texto: str) -> str:
        return self.fernet.encrypt(texto.encode()).decode()

    def descriptografar(self, token: str) -> str:
        try:
            return self.fernet.decrypt(token.encode()).decode()
        except Exception:
            return None