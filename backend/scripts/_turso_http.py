"""Cliente HTTP compartilhado pelos scripts de bootstrap do Turso.

Fala com o Turso via libsql_client puro (aiohttp), sem o dialeto
sqlalchemy-libsql — que só tem wheel pronta pra Linux/macOS e por isso não
instala no Windows local. Lê TURSO_BOOTSTRAP_URL/TOKEN (usadas no dev local,
onde as TURSO_DATABASE_URL/AUTH_TOKEN precisam ficar vazias para a engine da
app cair no SQLite) e cai nas TURSO_DATABASE_URL/AUTH_TOKEN quando rodando em
um ambiente que já aponta pro Turso de verdade.
"""

import os
import sys

import libsql_client

from app.core.config import get_settings


def criar_client():
    settings = get_settings()
    url = settings.turso_bootstrap_url or settings.turso_database_url
    token = settings.turso_bootstrap_token or settings.turso_auth_token
    if not (url and token):
        print(
            "Credenciais do Turso não configuradas — preencha TURSO_BOOTSTRAP_URL/"
            "TURSO_BOOTSTRAP_TOKEN (ou TURSO_DATABASE_URL/TURSO_AUTH_TOKEN) no .env"
        )
        sys.exit(1)
    host = url.removeprefix("libsql://")
    return libsql_client.create_client_sync(url=f"https://{host}", auth_token=token)


def encerrar(codigo: int = 0):
    """Encerra o processo na força.

    O `create_client_sync` do libsql_client sobe um event loop em uma thread que
    não é daemon e continua viva mesmo depois de `client.close()` — sem isso o
    script fica pendurado pra sempre depois de terminar o trabalho, segurando
    também qualquer arquivo aberto (já travou o dev.db aqui).
    """
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(codigo)
