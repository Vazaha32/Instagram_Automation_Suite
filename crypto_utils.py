import base64

from cryptography.fernet import Fernet
import os


# Génère une clé de chiffrement (à faire une seule fois)
def generate_key():
    """ Génère une clé de chiffrement et la sauvegarde dans secret.key """
    key = Fernet.generate_key()
    with open("secret.key", "wb") as key_file:
        key_file.write(key)


def load_key():
    """ Charge la clé depuis secret.key """
    ensure_key_exists()  # <-- Nouvelle ligne cruciale
    return open("secret.key", "rb").read()


def ensure_key_exists():
    """ Crée secret.key s'il n'existe pas """
    if not os.path.exists("secret.key"):
        generate_key()


# Initialisation automatique
ensure_key_exists()


# Chiffre des données
def encrypt_data(data: str) -> str:
    """ Chiffre une chaîne et retourne une chaîne encodée en base64 """
    fernet = Fernet(load_key())
    encrypted_bytes = fernet.encrypt(data.encode())
    return base64.b64encode(encrypted_bytes).decode("utf-8")  # bytes → str


# Déchiffre des données
def decrypt_data(encrypted_data: str) -> str:
    """ Déchiffre une chaîne encodée en base64 """
    fernet = Fernet(load_key())
    encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))  # str → bytes
    return fernet.decrypt(encrypted_bytes).decode()
