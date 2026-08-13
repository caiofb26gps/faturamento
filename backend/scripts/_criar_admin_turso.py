"""Cria o primeiro usuário admin direto no Turso via HTTP (mesmo motivo do
_criar_schema_turso.py: o dialeto sqlalchemy-libsql não roda neste Windows local).

Uso: python scripts/_criar_admin_turso.py email@empresa.com "Nome Completo" senha123
"""

import sys

sys.path.insert(0, ".")
sys.path.insert(0, "scripts")

from _turso_http import criar_client, encerrar
from app.core.security import hash_password

if len(sys.argv) != 4:
    print('Uso: python scripts/_criar_admin_turso.py <email> "<nome>" <senha>')
    sys.exit(1)

email, nome, senha = sys.argv[1], sys.argv[2], sys.argv[3]

client = criar_client()

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
encerrar()
