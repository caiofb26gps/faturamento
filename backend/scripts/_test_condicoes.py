"""Teste manual do motor de condições E/OU do "grande SE".

Compara os totais gerados em três cenários contra a baseline (só as regras de
CNPJ migradas), para provar que os valores se redistribuem sem sobra nem falta:

  1. baseline: só as 12 regras de CNPJ do SHERWIN WILLIAMS
  2. E:       CNPJ = X E CARGO = Y (subconjunto de um CNPJ, prioridade máxima)
  3. CONTEM:  CARGO contém "OPERADOR" (pega variações do cargo)
  4. OU:      CNPJ = A OU CNPJ = B (junta dois CNPJs num mapa só)

Uso: python scripts/_test_condicoes.py
"""

import sys
from decimal import Decimal

sys.path.insert(0, ".")

from app.core.database import SessionLocal
from app.models.enums import ComparadorCondicao, LogicaRegra
from app.models.lancamento import LancamentoVerba
from app.models.mapa import MapaGerado
from app.models.regra import RegraCondicao, RegraSegmentacao
from app.services.geracao_mapa import gerar_mapas

CLIENTE_ID = 97
COMPETENCIA = "202607"

db = SessionLocal()


def limpar_mapas():
    db.query(MapaGerado).filter(MapaGerado.cliente_id == CLIENTE_ID).delete()
    db.commit()
    # O delete em massa não tira os objetos do identity map da sessão; sem isso o
    # SQLAlchemy avisa quando a próxima geração cria mapas com os mesmos ids.
    db.expire_all()


def rodar(rotulo: str) -> tuple[Decimal, list[MapaGerado]]:
    limpar_mapas()
    mapas, fora = gerar_mapas(db, CLIENTE_ID, COMPETENCIA)
    total = sum(Decimal(m.valores_iniciais.get("Total", "0")) for m in mapas)
    print(f"\n{rotulo}")
    print(f"  {len(mapas)} mapa(s), {fora.quantidade} fora das regras, soma dos Totais = {total}")
    for m in sorted(mapas, key=lambda x: x.id):
        regra = db.query(RegraSegmentacao).filter(RegraSegmentacao.id == m.regra_segmentacao_id).first()
        cond = " / ".join(f"{c.atributo} {c.comparador.value} {c.valor}" for c in regra.condicoes) if regra else "GERAL"
        print(f"    {m.valores_iniciais.get('Total'):>14}  [{regra.logica.value if regra else '-'}] {cond}")
    return total, mapas


def nova_regra(nome: str, logica: LogicaRegra, condicoes: list[tuple[str, ComparadorCondicao, str]]):
    """Cria uma regra em prioridade máxima (ordem -1, testada antes de todas)."""
    regra = RegraSegmentacao(
        cliente_id=CLIENTE_ID,
        ordem=-1,
        logica=logica,
        nome_exibicao=nome,
        email_responsavel="teste@exemplo.com",
        condicoes=[RegraCondicao(atributo=a, comparador=c, valor=v) for a, c, v in condicoes],
    )
    db.add(regra)
    db.commit()
    return regra


def remover_regra(regra):
    limpar_mapas()  # mapas referenciam a regra; precisam sair antes dela
    db.delete(regra)
    db.commit()


def cenario(rotulo: str, regra, baseline: Decimal):
    """Roda um cenário e cobra duas coisas: o total tem que ser preservado E a
    regra nova tem que ter capturado alguém. Sem a segunda checagem um cenário
    que não casa com nada passaria "verde" sem testar nada."""
    total, mapas = rodar(rotulo)
    assert total == baseline, f"{rotulo}: total mudou! {total} != {baseline}"
    capturados = [m for m in mapas if m.regra_segmentacao_id == regra.id]
    assert capturados, f"{rotulo}: a regra nova nao capturou nenhum colaborador — cenario vazio, nao testa nada"
    print(f"  OK: total preservado e regra capturou {capturados[0].valores_iniciais.get('Total')}")
    remover_regra(regra)


try:
    # Limpa sobras de execuções anteriores (regras de teste ficam com ordem -1).
    for sobra in db.query(RegraSegmentacao).filter(
        RegraSegmentacao.cliente_id == CLIENTE_ID, RegraSegmentacao.ordem < 0
    ).all():
        print(f"[limpando sobra] regra id={sobra.id} '{sobra.nome_exibicao}'")
        remover_regra(sobra)

    baseline, _ = rodar("BASELINE (12 regras de CNPJ, uma condicao IGUAL cada)")

    # --- E: um cargo dentro de um CNPJ específico ---
    cnpj_alvo, cargo_alvo = "60872306004076", "AUXILIAR DE PRODUCAO"
    cenario(
        f"E: CNPJ={cnpj_alvo} E CARGO={cargo_alvo}",
        nova_regra("Teste E", LogicaRegra.E, [("CNPJ", ComparadorCondicao.IGUAL, cnpj_alvo),
                                              ("CARGO", ComparadorCondicao.IGUAL, cargo_alvo)]),
        baseline,
    )

    # --- CONTEM: "AUXILIAR" pega AUXILIAR DE PRODUCAO e AUXILIAR DE OPERACAO ---
    cenario(
        "CONTEM: CARGO contem 'AUXILIAR'",
        nova_regra("Teste CONTEM", LogicaRegra.E, [("CARGO", ComparadorCondicao.CONTEM, "AUXILIAR")]),
        baseline,
    )

    # --- DIFERENTE: todo mundo menos um cargo ---
    cenario(
        f"DIFERENTE: CARGO diferente de {cargo_alvo}",
        nova_regra("Teste DIFERENTE", LogicaRegra.E, [("CARGO", ComparadorCondicao.DIFERENTE, cargo_alvo)]),
        baseline,
    )

    # --- OU: junta dois CNPJs num mapa só ---
    cnpjs = [c[0] for c in db.query(LancamentoVerba.cnpj)
             .filter(LancamentoVerba.cliente_id == CLIENTE_ID, LancamentoVerba.competencia == COMPETENCIA)
             .distinct().all()][:2]
    cenario(
        f"OU: CNPJ={cnpjs[0]} OU CNPJ={cnpjs[1]}",
        nova_regra("Teste OU", LogicaRegra.OU, [("CNPJ", ComparadorCondicao.IGUAL, c) for c in cnpjs]),
        baseline,
    )

    limpar_mapas()
    gerar_mapas(db, CLIENTE_ID, COMPETENCIA)
    print("\nTodos os cenarios: total preservado e regra realmente aplicada. Baseline restaurada.")
finally:
    db.close()
