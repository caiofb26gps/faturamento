from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class CredentialDecryptionError(Exception):
    pass


def _fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.credentials_encryption_key.encode())


def encrypt_secret(plaintext: str | None) -> str | None:
    """Encrypts a portal credential (login/senha) before it is persisted.

    The key lives in an env var for local dev; in Azure/AWS it should be pulled from
    Key Vault / Secrets Manager instead of the app's own environment.
    """
    if plaintext is None or plaintext == "":
        return None
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt_secret(ciphertext: str | None) -> str | None:
    if ciphertext is None or ciphertext == "":
        return None
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise CredentialDecryptionError(
            "Não foi possível descriptografar a credencial — verifique CREDENTIALS_ENCRYPTION_KEY."
        ) from exc
