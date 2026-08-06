"""Popula `cliente_identificadores` (negocio + COD GRUPO -> cliente_id) cruzando
uma base DS real com os clientes já cadastrados (aba MAPAS/Pendentes migradas por
`migrate_from_excel.py`).

A chave usada é (Negocio do cadastro, COD GRUPO da DS) — validada empiricamente:
100% estável 1:1 nos dados reais, ao contrário de CNPJ (1 cliente pode ter dezenas
de CNPJs) — ver docs/plano.md.

Uso:
    python scripts/bootstrap_identificadores.py "DS julho.xlsx"

Também semeia `negocio_ds_mapeamento` (de/para NEGOCIO da DS -> Negocio do
cadastro) se ainda não existir.

Idempotente: não duplica identificadores já existentes. Só GRAVA matches exatos ou
inequívocos (contains) automaticamente; combos ambíguos ou sem match nenhum ficam
só no relatório, para decisão manual (não inventa cliente nem aceita palpite).
"""

import argparse
import sys
from collections import Counter

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.cliente import Cliente, ClienteIdentificador
from app.models.enums import TipoIdentificadorCliente
from app.services.ds_parser import ler_linhas_ds
from app.services.negocio_mapeamento_seed import semear_mapeamento


def normalizar(nome: str) -> str:
    return " ".join(nome.strip().upper().split())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ds_xlsx", help='Caminho para "DS <mes>.xlsx"')
    args = parser.parse_args()

    db = SessionLocal()
    try:
        criados_mapeamento = semear_mapeamento(db)
        db.flush()
        print(f"negocio_ds_mapeamento: {criados_mapeamento} linha(s) semeada(s)")

        negocio_map = {}
        from app.models.negocio_mapeamento import NegocioDsMapeamento

        for m in db.query(NegocioDsMapeamento).all():
            negocio_map[m.negocio_ds.upper()] = m.negocio_cadastro

        clientes_por_negocio: dict[str, list[Cliente]] = {}
        for cliente in db.query(Cliente).all():
            clientes_por_negocio.setdefault(cliente.negocio, []).append(cliente)

        ja_existentes = {
            (i.negocio, i.valor)
            for i in db.query(ClienteIdentificador)
            .filter(ClienteIdentificador.tipo == TipoIdentificadorCliente.COD_GRUPO)
            .all()
        }

        print(f"Lendo {args.ds_xlsx} (pode levar um pouco, é uma base grande)...")
        combos: Counter[tuple[str | None, str | None, str | None]] = Counter()
        total_linhas = 0
        for linha in ler_linhas_ds(args.ds_xlsx):
            total_linhas += 1
            combos[(linha["negocio_ds"], linha["cod_grupo"], linha["grupo_cliente"])] += 1
        print(f"{total_linhas} linhas lidas, {len(combos)} combinações (negócio, cod grupo) distintas")

        exatos = fuzzy = ambiguos = sem_negocio = sem_match = 0
        sem_match_linhas = 0
        criados = 0
        relatorio_sem_match = []

        for (negocio_ds, cod_grupo, grupo_cliente), qtd in combos.most_common():
            if not negocio_ds or not cod_grupo:
                sem_negocio += 1
                continue
            negocio_cadastro = negocio_map.get(negocio_ds.upper())
            if negocio_cadastro is None:
                sem_negocio += 1
                relatorio_sem_match.append((negocio_ds, cod_grupo, grupo_cliente, qtd, "negocio_ds sem mapeamento"))
                continue

            if (negocio_cadastro, cod_grupo) in ja_existentes:
                continue  # já resolvido em rodada anterior

            candidatos = clientes_por_negocio.get(negocio_cadastro, [])
            nome_norm = normalizar(grupo_cliente or "")

            exato = [c for c in candidatos if normalizar(c.nome) == nome_norm]
            if len(exato) == 1:
                cliente = exato[0]
                db.add(
                    ClienteIdentificador(
                        cliente_id=cliente.id,
                        negocio=negocio_cadastro,
                        tipo=TipoIdentificadorCliente.COD_GRUPO,
                        valor=cod_grupo,
                    )
                )
                ja_existentes.add((negocio_cadastro, cod_grupo))
                exatos += 1
                criados += 1
                continue

            aproximados = [
                c for c in candidatos if normalizar(c.nome) in nome_norm or nome_norm in normalizar(c.nome)
            ]
            if len(aproximados) == 1:
                cliente = aproximados[0]
                db.add(
                    ClienteIdentificador(
                        cliente_id=cliente.id,
                        negocio=negocio_cadastro,
                        tipo=TipoIdentificadorCliente.COD_GRUPO,
                        valor=cod_grupo,
                    )
                )
                ja_existentes.add((negocio_cadastro, cod_grupo))
                fuzzy += 1
                criados += 1
                continue

            if len(aproximados) > 1:
                ambiguos += 1
                relatorio_sem_match.append(
                    (negocio_ds, cod_grupo, grupo_cliente, qtd, f"ambíguo entre {len(aproximados)} clientes")
                )
                continue

            sem_match += 1
            sem_match_linhas += qtd
            relatorio_sem_match.append((negocio_ds, cod_grupo, grupo_cliente, qtd, "nenhum cliente encontrado"))

        db.commit()

        print(f"\nidentificadores criados: {criados} (exatos: {exatos}, aproximados: {fuzzy})")
        print(f"sem negocio_ds mapeado: {sem_negocio}")
        print(f"ambíguos (mais de 1 cliente candidato): {ambiguos}")
        print(f"sem match nenhum: {sem_match} combo(s), {sem_match_linhas} linha(s) de DS")

        print("\nPrincipais combos sem match automático (revisar manualmente), por volume de linhas:")
        for negocio_ds, cod_grupo, grupo_cliente, qtd, motivo in sorted(
            relatorio_sem_match, key=lambda r: -r[3]
        )[:20]:
            print(f"  [{qtd:>6} linhas] negocio_ds={negocio_ds!r} cod_grupo={cod_grupo!r} grupo_cliente={grupo_cliente!r} — {motivo}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
