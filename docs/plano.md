# Sistema de Mapa de Faturamento — Plano de Construção

## Contexto

Hoje o processo de transformar a base de verbas (folha) em mapas de faturamento por
cliente vive em Power BI + um conjunto de planilhas soltas (`DE PARA GERAL.xlsx`,
`Regras julho.xlsx`, `MODELO MAPA.xlsm`) e uma base mensal (`DS julho.xlsx`, ~166k
linhas). O fluxo funciona, mas é frágil: cadastro de cliente, regras de segmentação,
de/para de verbas e credenciais de portal (hoje em **texto puro**) ficam espalhados em
abas de Excel, sem histórico, sem validação e sem trilha de quem alterou o quê. Ajustes
pontuais (upload "cliente + regra" depois do "closed" inicial) não têm rastreabilidade
de antes/depois além de uma tabela solta na planilha final.

O objetivo é migrar isso para uma aplicação web com banco de dados, cobrindo o fluxo
de ponta a ponta: cadastro → ingestão da base mensal → aplicação de regras/de-para →
geração do mapa por cliente → revisão → controle de envio — mantendo o mapa final em
Excel (sem macro), com envio ainda disparado manualmente pelo faturista após revisão.

Decisões já confirmadas com o usuário:
- Hospedagem em nuvem (Azure ou AWS).
- Sem preferência de stack — a definir por mim.
- Mapa final continua em `.xlsx`, mas **sem macro** (VBA).
- Envio de e-mail: sistema gera o mapa, faturista revisa e dispara manualmente
  (não há disparo automático no MVP).
- Credenciais de portal do cliente: armazenadas **criptografadas** no banco (não em
  texto puro).

## Como os 4 arquivos de hoje se mapeiam para o sistema

| Arquivo/aba atual | Vira no sistema |
|---|---|
| `DS julho.xlsx` → `DS_Aberto_Fechado` | Upload mensal → tabela `lancamentos_verbas` |
| `DE PARA GERAL.xlsx` → `VERBAS` | `de_para_modelos` (padrão, sem cliente) + `de_para_verbas` |
| `DE PARA GERAL.xlsx` → `CADASTRAIS` | `campos_cadastrais_mapa` (ordem dos campos do colaborador no mapa) |
| `Regras julho.xlsx` → `MAPAS` + `Pendentes` | tabela única `clientes` (com `status`: ativo/pendente) |
| `Regras julho.xlsx` → `REGRAS` | `regras_segmentacao` (valor → destinatário) |
| `Regras julho.xlsx` → `LISTAS` | `atributos_segmentacao` (enum/lookup) |
| `MODELO MAPA.xlsm` → `BASE` | dados internos já cruzados (não persiste como aba, é uma view/consulta) |
| `MODELO MAPA.xlsm` → `MENSAL` | aba gerada no `.xlsx` de saída (detalhe por colaborador) |
| `MODELO MAPA.xlsm` → `MAPA` | aba gerada no `.xlsx` de saída (resumo por grupo, com Inicial/Final/Diferença) |

## Modelo de dados (PostgreSQL)

**Cadastro**
- `usuarios` (analistas/admins, RBAC: admin vê tudo, analista vê só seus clientes)
- `clientes`: negocio, nome, status (ativo/pendente/inativo), `segmentacao_email`,
  `segmentacao_mapa` (podem ser diferentes), `de_para_modelo_id` (nullable = usa GERAL),
  `modelo_mapa_id`, `analista_responsavel_id`, `folha` (aberta/fechada), `aguardo_po`,
  `portal_site`, `portal_login`, `portal_senha_cifrada`, `observacao`
- `cliente_identificadores`: liga linhas da DS a um `cliente_id` por
  `negocio + (cod_grupo | cnpj)` — **ponto a validar com dados reais**, ver "Riscos" abaixo
- `de_para_modelos` (padrão + um por cliente que tiver De/Para próprio)
- `de_para_verbas`: modelo_id, verba_codigo, evento_exibicao, grupo, ordem_grupo, ordem_item
- `campos_cadastrais_mapa`: campo, ordem (equivalente à aba CADASTRAIS)
- `atributos_segmentacao`: lookup (CNPJ, CARGO, CR, UF, COLABORADOR, GERAL, etc. — da aba LISTAS)
- `regras_segmentacao`: cliente_id, valor_segmentacao, nome_exibicao, email_responsavel,
  dia_envio, envio_automatico, analista_id, `aplica_email` / `aplica_mapa` (bool — cobre
  o caso em que a segmentação de e-mail e de mapa divergem)

**Operacional (mensal)**
- `importacoes`: competencia, tipo (`CLOSED_INICIAL` / `AJUSTE`), cliente_id (nullable),
  regra_id (nullable, quando o ajuste é escopado), arquivo original, status
- `lancamentos_verbas`: linha normalizada da DS (competencia, cnpj, cc, matricula,
  colaborador, cargo, negocio, verba_codigo, descri, valor, situacao_folha, origem,
  importacao_id) — tabela de fato, maior volume
- `mapas_gerados`: cliente_id, regra_segmentacao_id (nullable), competencia, status
  (rascunho/pronto/revisado/enviado), arquivo_path, valores_iniciais/finais/diferenca (jsonb)
- `envios`: mapa_gerado_id, email_destino, data_prevista, data_enviado, status,
  dentro_do_prazo, enviado_por — alimenta os indicadores "E-mails Enviados" e "SLA de Envio"
  que já existem no Power BI
- `auditoria_alteracoes`: changelog simples para edições em `clientes`, `regras_segmentacao`
  e `de_para_verbas` (rastreabilidade que hoje não existe)

## Arquitetura recomendada

- **Backend**: Python + FastAPI. Justificativa: o núcleo do sistema é processamento de
  planilhas em lote (pandas/openpyxl) e geração de Excel — ecossistema Python é o mais
  maduro para isso, e evita reescrever parsing que já validamos nesta conversa.
- **ORM/migrations**: SQLAlchemy + Alembic.
- **Banco**: PostgreSQL gerenciado (Azure Database for PostgreSQL ou AWS RDS).
- **Frontend**: React + TypeScript (Vite), biblioteca de componentes (Mantine ou MUI)
  para telas de cadastro (clientes/regras/de-para) e um dashboard operacional que
  reproduz os indicadores do Power BI atual (relação de clientes, SLA, e-mails
  enviados/pendentes).
- **Armazenamento de arquivo**: Blob Storage (Azure) ou S3 (AWS) para os uploads de DS
  e os `.xlsx` gerados.
- **Geração do Excel**: openpyxl, replicando as abas MENSAL (detalhe por colaborador) e
  MAPA (resumo por grupo com Inicial/Final/Diferença) do `MODELO MAPA.xlsm`, sem VBA.
- **Segredos**: chave de criptografia das credenciais de portal fica em um secrets
  manager (Azure Key Vault / AWS Secrets Manager), não hardcoded na aplicação.
- **Autenticação**: como o domínio já é Microsoft 365 (`@gpssa.com.br`), recomendo login
  corporativo via Microsoft Entra ID (OAuth2) em vez de senha própria — menos atrito e
  mais seguro para dado de folha de pagamento. Fallback: usuário/senha com bcrypt + RBAC
  se Entra ID não for viável.
- **Processamento em lote**: para o MVP, tarefas em background simples (FastAPI
  `BackgroundTasks` ou APScheduler) bastam para ~166k linhas/mês; migrar para
  Celery+Redis apenas se o volume/tempo de processamento exigir (fase futura).

## Pipeline de processamento (núcleo do sistema)

1. Upload da base "closed" do mês → parse → grava em `lancamentos_verbas`
   (`tipo=CLOSED_INICIAL`), resolvendo `cliente_id` via `cliente_identificadores`.
2. Para cada cliente com lançamentos na competência:
   a. aplica o De/Para (do cliente ou GERAL) → resolve `grupo`/`evento`/ordem por linha
   b. agrupa pelas colunas de segmentação (email e mapa, conforme cadastro do cliente)
   c. casa cada valor de segmentação com `regras_segmentacao` → destinatário e nome de
      exibição; valores sem regra correspondente ficam marcados como "fora das regras"
      (mesmo alerta que já existe no painel atual)
   d. monta o detalhe por colaborador (equivalente à aba MENSAL) e o resumo por grupo
      (equivalente à aba MAPA), grava em `mapas_gerados` com status `rascunho` e
      `valores_iniciais`
3. Upload de ajuste pontual (cliente + regra específica) depois do closed:
   a. grava como `lancamentos_verbas` (`tipo=AJUSTE`), escopado ao cliente/regra
   b. recalcula os `mapas_gerados` afetados: `valores_finais`, `diferenca` = final − inicial
   c. mapa volta para status `rascunho` (precisa nova revisão)
4. Faturista revisa na tela (valores, alertas de "fora do de-para" / "fora das regras" /
   "colaborador fora do de-para auxiliar"), baixa o `.xlsx` gerado e, após enviar
   manualmente, marca o envio como concluído (grava em `envios` com data/hora).

## Fases de entrega

1. **Cadastros e fundação**: schema do banco, RBAC, CRUD de clientes/de-para/regras/
   atributos de segmentação, criptografia de credenciais, script de migração única dos
   dados hoje em `MAPAS`/`REGRAS`/`DE PARA GERAL.xlsx` para o banco.
2. **Ingestão e motor de regras**: upload de DS (closed e ajuste), resolução de cliente,
   aplicação de de/para, casamento com regras de segmentação, cálculo de
   iniciais/finais/diferença.
3. **Geração do mapa e revisão**: geração do `.xlsx` (abas MENSAL + MAPA, sem macro),
   tela de revisão com os alertas existentes hoje, download.
4. **Controle e dashboard**: tela "relação de clientes" com status/SLA/prazo (reproduzindo
   o painel atual), registro manual de envio, indicadores de e-mails enviados/pendentes.
5. **Futuro (fora do MVP)**: rascunho de e-mail no Outlook via Microsoft Graph
   (para o faturista só clicar "Enviar"), fila assíncrona (Celery) se o volume exigir,
   envio automático total para clientes com `envio_automatico=SIM`.

## Riscos / pontos a validar com dados reais antes da Fase 2

- **Chave de ligação DS → Cliente**: a DS não tem um `cliente_id` direto — a hipótese é
  `NEGOCIO + COD GRUPO` (ou `CNPJ`), mas isso precisa ser confirmado linha a linha com
  o faturista antes de implementar `cliente_identificadores`, para não gerar mapa errado.
- **Segmentação de e-mail vs. de mapa divergentes**: nos exemplos vistos elas coincidem
  (ex: 3M usa COLABORADOR nas duas). O modelo suporta divergência (`aplica_email`/
  `aplica_mapa`), mas vale confirmar se existe caso real assim para não superdimensionar.
- **Conteúdo exato do `.xlsx` final sem macro**: confirmar se o cliente deve receber só
  a aba equivalente a MENSAL, ou MENSAL + MAPA juntas no mesmo arquivo.

## Verificação

- Migração de dados: script que importa `MAPAS`+`Pendentes`+`REGRAS`+`DE PARA GERAL.xlsx`
  para o banco e um relatório de contagem (nº de clientes, regras, verbas) comparado ao
  Excel original.
- Pipeline: rodar a base `DS julho.xlsx` real contra um cliente conhecido (ex: 3M/TALENTOS)
  e comparar o mapa gerado pelo sistema com o `MODELO MAPA.xlsm` real desse cliente,
  valor a valor.
- Alertas: confirmar que verbas fora do De-Para e valores fora das regras aparecem como
  aviso na tela de revisão, igual ao painel atual.
