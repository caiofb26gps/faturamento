"""Cria o primeiro usuário admin direto no Turso via HTTP (mesmo motivo do
_criar_schema_turso.py: o dialeto sqlalchemy-libsql não roda neste Windows local).

Uso: python scripts/_criar_admin_turso.py email@empresa.com "Nome Completo" senha123
"""

import sys

sys.path.insert(0, ".")

import libsql_client

from app.core.config import get_settings
from app.core.security import hash_password

if len(sys.argv) != 4:
    print('Uso: python scripts/_criar_admin_turso.py <email> "<nome>" <senha>')
    sys.exit(1)

email, nome, senha = sys.argv[1], sys.argv[2], sys.argv[3]

settings = get_settings()
if not (settings.turso_database_url and settings.turso_auth_token):
    print("TURSO_DATABASE_URL / TURSO_AUTH_TOKEN não configurados no .env")
    sys.exit(1)

url_http = settings.turso_database_url.removeprefix("libsql://")
client = libsql_client.create_client_sync(url=f"https://{url_http}", auth_token=settings.turso_auth_token)

existe = client.execute("SELECT id FROM usuarios WHERE email = ?", [email])
if existe.rows:
    print(f"Já existe um usuário com o e-mail {email}")
else:
    client.execute(
        "INSERT INTO usuarios (nome, email, senha_hash, papel, ativo, criado_em, atualizado_em) "
        "VALUES (?, ?, ?, 'ADMIN', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        [nome, email, hash_password(senha)],
    )
    print(f"Admin criado no Turso: {email}")
client.close()
