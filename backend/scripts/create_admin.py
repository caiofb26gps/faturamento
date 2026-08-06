"""Bootstrap do primeiro usuário admin (não há auto-registro pela API por design).

Uso: python scripts/create_admin.py nome@empresa.com "Nome Completo" senha123
"""

import sys

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python scripts/create_admin.py <email> <nome> <senha>")
        sys.exit(1)

    email, nome, senha = sys.argv[1], sys.argv[2], sys.argv[3]

    db = SessionLocal()
    try:
        if db.query(Usuario).filter(Usuario.email == email).first():
            print(f"Já existe um usuário com o e-mail {email}")
            sys.exit(1)
        admin = Usuario(nome=nome, email=email, senha_hash=hash_password(senha), papel=PapelUsuario.ADMIN)
        db.add(admin)
        db.commit()
        print(f"Admin criado: {email}")
    finally:
        db.close()
