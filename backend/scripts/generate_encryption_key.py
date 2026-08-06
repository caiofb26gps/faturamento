"""Gera uma chave Fernet válida para CREDENTIALS_ENCRYPTION_KEY.

Uso: python scripts/generate_encryption_key.py
Em produção, gere a chave assim e guarde no Key Vault / Secrets Manager —
nunca commitar a chave real no repositório.
"""

from cryptography.fernet import Fernet

if __name__ == "__main__":
    print(Fernet.generate_key().decode())
