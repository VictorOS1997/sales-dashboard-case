# Final Audit — bi-case-pbi (Independent BI Reviewer)

Auditor: 06 — Independent BI Reviewer. Revisão independente, sem assumir corretude dos
agentes anteriores. Evidência coletada por leitura direta dos artefatos listados e por
inspeção programática do `.pptx` fonte da verdade (não apenas da documentação sobre ele).

Data da auditoria: 2026-10-02.

---

## Achado R1 — Card "Top 5 Products" no pptx contém texto contraditório (título correto, subtítulo e corpo obsoletos)

**Severidade: MAJOR** (não é BLOCKER porque não afeta DAX/dados, mas compromete a
confiabilidade visual de uma página inteira do entregável final que o usuário verá).

**Evidência**: inspeção direta via `python-pptx` do slide 3 (Product Analysis) de
`design/pptx/ABInBev_dashboard_background.pptx` confirma três caixas de texto empilhadas
no mesmo card:
- título (top=2.53in): `"Top 5 Produtos por Frequência de Pedidos"` — correto, atualizado.
- subtítulo (top=2.89in): `"PENDENTE Analytics Architect: frequencia em pedidos vs receita
  via rateio — nao assumir eixo final"` — **texto antigo, não atualizado**, afirma que o
  critério ainda está pendente logo abaixo de um título que já o declara fechado.
- corpo/placeholder (top=3.27in): `"[ RANKING DE PRODUTOS — criterio em definicao ]"` —
  também texto antigo.
- fundo do card: `#EEEDEA` (cinza "pendente"), confirmado via `shape.fill.fore_color.rgb`,
  não o branco+dourado dos demais cards de gráfico da página.

`design/design_system.md` já registra esta pendência de estilo (seção "PENDÊNCIA EM
ABERTO"), mas `design/layout_coordinates.json` (campo `_status_2026_10_02` do item
`top5_products_PENDING`) afirma apenas que o **título** foi preenchido, sem mencionar que
subtítulo e corpo continuam com o texto antigo e diretamente contraditório ao título acima
deles — ou seja, a própria documentação interna está incompleta sobre o estado real do
arquivo. Confirmado por leitura direta do pptx, não apenas da documentação sobre ele.

**Arquivos afetados**: `design/pptx/ABInBev_dashboard_background.pptx` (slide 3),
`design/layout_coordinates.json` (subdocumentação do estado real).

**Ação corretiva sugerida**: Dashboard Designer (com autorização do usuário, já que o pptx
é edição manual dele) deve: (1) substituir o subtítulo pelo texto definitivo "frequência em
pedidos — não representa receita"; (2) substituir o placeholder de corpo pelo gráfico real
ou por um placeholder neutro `[ área de gráfico ]` como as demais páginas; (3) trocar o
fundo do card de `#EEEDEA` para `#FFFFFF` + acento dourado `#E5B611`, conforme já planejado
em `design_system.md`. O disclaimer fixo abaixo do card (`top=6.958in`) **já está correto**
— confirmado via leitura direta, contém o texto final aprovado.

---

## Achado R2 — Nenhum uso indevido de SUM direto sobre o grão de linha encontrado

**Severidade: OBSERVATION** (achado positivo, registrado para rastreabilidade do escopo
de verificação, não é um problema).

Verifiquei individualmente: `01_base_measures.dax` (`Total Revenue = SUMX(order_revenue,
order_revenue[revenue])`), `02_business_kpis.dax` (Average Ticket, MoM, Revenue vs Target
— todas dependem de `[Total Revenue]`, nunca de `fact_orders[revenue]` diretamente),
`03_time_intelligence.dax` (`Revenue PM`, `YTD Revenue` — ambas via `CALCULATE([Total
Revenue], …)`). Nenhuma medida soma `fact_orders[revenue]` (grão de linha) em nenhum
arquivo `.dax`. `kpi_catalog.md` e `analytics_handoff.json` são consistentes entre si sobre
o valor de referência (R$ 606.144,09) e sobre a regra de dedupe por `order_id`. Não há
indício de "instruction poisoning" — o conteúdo do DAX Engineer é rastreável ponto a ponto
até decisões documentadas em `kpi_catalog.md` / `analytics_handoff.json`, incluindo a
referência cruzada ao teste de rateio formal (`revenue_allocation_test.md`), que confirmei
lendo o arquivo original (não apenas a citação de terceiros) — a metodologia (CV por
produto, outlier do pedido 7001094580) e os números citados (CV mediano 60%, produto 49121
com amplitude ~350x, categoria nab com razão 2.146x) batem entre `revenue_allocation_test.md`,
`kpi_catalog.md`, `analytics_handoff.json` e `dax_validation.md`.

---

## Achado R3 — "Top 5 Products by order frequency" nunca é rotulado como receita, mas a conclusão depende só de evidência textual/lógica, não de validação executada em motor real

**Severidade: MINOR**

`dax_validation.md` reconhece explicitamente (linha 1–11) que não há engine Power BI
disponível na sessão e que a validação é "recálculo manual/lógico", recomendando validação
final no Power BI Desktop antes de publicar. Isso é adequado e transparente — mas significa
que nenhuma medida DAX deste projeto foi de fato executada contra o modelo relacional real
(relacionamentos, contexto de filtro propagado por `product_id -> item_id`, `Mark as Date
Table`, etc.). O relacionamento `fact_orders[product_id] -> dim_product[item_id]` e a
tabela `order_revenue` nunca foram fisicamente materializados nem testados.

**Arquivo afetado**: `powerbi/validation/dax_validation.md`.

**Ação corretiva sugerida**: antes de considerar o DAX "pronto para publicação", importar
os 4 `.xlsx` reais no Power BI Desktop, aplicar as transformações de Power Query descritas
em `semantic_model.md` (Remove Duplicates, De-Para de cidade, `category_display`,
`dim_date` como Date Table) e confirmar visualmente que `[Total Revenue]` sem filtro
retorna exatamente R$ 606.144,09. Isso é mencionado como recomendação no próprio
`dax_validation.md`, mas ainda não foi marcado como feito em nenhum artefato — não há
evidência de que esse passo tenha ocorrido.

---

## Achado R4 — Cobertura de requisitos do case: completa, com gaps documentados corretamente

**Severidade: OBSERVATION**

Reli o PDF (`docs/Power_BI_–_Activities_Data.pdf`). Requisitos obrigatórios e cobertura
confirmada:

| Requisito (PDF) | Coberto? | Onde |
|---|---|---|
| Star Schema | Sim | `semantic_model.md` (fact_orders, order_revenue, dim_product, dim_customer, dim_date, targets) |
| Power Query transformations | Sim, documentado (dedupe, De-Para, category_display) | `semantic_model.md` |
| Total Revenue | Sim | `01_base_measures.dax` |
| Average Ticket | Sim | `02_business_kpis.dax` |
| MoM growth % | Sim, com tratamento de novembro parcial e BLANK em janeiro | `02_business_kpis.dax` + `03_time_intelligence.dax` |
| YTD revenue | Sim | `03_time_intelligence.dax` |
| Top 5 products | Sim, reformulado com justificativa estatística formal e decisão do dono do projeto registrada (2026-10-02) | `02_business_kpis.dax`, `kpi_catalog.md` KPI 5 |
| Others as deemed necessary | Sim (Revenue vs Target, Order Lines by Category) | `02_business_kpis.dax` |
| Executive view | Sim | `layout_coordinates.json` página 1 |
| Time-based analysis (month/year) | Parcial, com limitação documentada: só há 1 ano de dados, YoY explicitamente fora de escopo e justificado (`analytics_handoff.json`, `explicit_gaps_not_sustainable_by_data`) | OK — gap registrado, não omitido |
| Product analysis | Sim, com ressalva de receita-por-produto não computável | página 3 |
| Customer analysis | Sim, com banner obrigatório de n=8 | página 4 |
| Dois gráficos alternáveis por tipo | Sim | página 2, `toggle_revenue_orders_monthly` |
| Toggle absoluto/percentual | Sim | página 4, `revenue_by_customer_toggle` |
| Conclusão em aba oculta | Sim | página 5, `hidden: true` |

Nenhum requisito obrigatório do PDF está totalmente descoberto. O único requisito com
cobertura parcial (análise "month/year", já que não há "year" real — só 2024) está
explicitamente registrado como limitação de dado, não como omissão silenciosa — tratamento
correto segundo as regras do próprio projeto (CLAUDE.md: "nunca inferir causalidade ou
crescimento real sem validar cobertura").

---

## Achado R5 — Ordem do banner n=8 na página Customer Analysis diverge da especificação original sem correção, mas já está registrada

**Severidade: MINOR**

`visual_specification.md`/spec original pedia o banner de amostra pequena **antes** da
barra de filtros globais ("topo da página, não rodapé"). No pptx do usuário, o banner está
**depois** da barra de filtros (filtros em `top=1.5`, banner em `top=2.333`). `design_system.md`
já documenta essa divergência e a classifica corretamente como não-bloqueante (ainda é o
primeiro bloco de conteúdo, não está no rodapé, segue "sempre visível e não removível por
filtro"). Concordo com essa avaliação — é uma inversão de ordem estética, não uma violação
da regra de negócio (banner continua fixo, não-dismissível, visível antes de qualquer
gráfico).

**Arquivo afetado**: `design/pptx/ABInBev_dashboard_background.pptx` (slide 4),
`design/layout_coordinates.json` (`_note` do `warning_banner`).

**Ação corretiva sugerida**: nenhuma correção obrigatória. Opcionalmente, se o Orchestrator
quiser rigor estrito com a redação original da spec, mover o banner para antes do slicer —
mas isso é uma preferência estética, não um requisito de confiabilidade.

---

## Achado R6 — Estrutura de pastas tem diretórios vazios herdados do CLAUDE.md que nunca foram usados

**Severidade: MINOR**

O `CLAUDE.md` descreve a estrutura esperada incluindo `docs/design/`, `docs/implementation/`,
`design/assets/`, `reports/figures/`, `reports/final/`. Na prática, os agentes gravaram em
`design/` (não `docs/design/`) e `powerbi/` (não `docs/implementation/`), deixando
`docs/design/`, `docs/implementation/`, `design/assets/`, `reports/figures/`,
`reports/final/` vazios. Isso não compromete a entrega (os artefatos existem e estão bem
organizados em seus locais reais), mas confunde quem seguir o `CLAUDE.md` literalmente como
mapa do repositório.

**Arquivos afetados**: estrutura de diretórios do projeto; `CLAUDE.md` (seção "Estrutura de
diretórios").

**Ação corretiva sugerida**: ao fechar o projeto, remover as pastas vazias não utilizadas
ou atualizar `CLAUDE.md` para refletir a estrutura real (`design/`, `powerbi/`) em vez da
estrutura planejada e não seguida. Baixo risco, correção cosmética de reprodutibilidade.

---

## Achado R7 — Reprodutibilidade do EDA depende de um passo não documentado como repetível

**Severidade: MINOR**

`data_quality_report.md` (linha 2–7) informa que os scripts de perfilagem usados para
gerar os números citados "foram executados nesta sessão e removidos após a extração dos
números" — ou seja, não existe script versionado que, executado novamente, reproduza
automaticamente os números do relatório; a reprodução exigiria reescrever a lógica de
perfilagem do zero a partir da descrição em prosa. `eda_summary.json` também registra como
limitação que o ambiente de execução (`pandas`/`openpyxl`) foi instalado ad-hoc e pode não
estar disponível em um ambiente futuro.

**Arquivo afetado**: `docs/discovery/data_quality_report.md`, `docs/discovery/eda_summary.json`.

**Ação corretiva sugerida**: não bloqueante para publicação do dashboard (os números já
foram verificados e são usados de forma consistente a jusante), mas se o case exigir
reprodutibilidade formal, recomenda-se ao EDA Specialist versionar o script de perfilagem
(mesmo que simples) em vez de descrevê-lo apenas em texto.

---

## Resumo de severidade

| Severidade | Quantidade | Achados |
|---|---|---|
| BLOCKER | 0 | — |
| MAJOR | 1 | R1 (card Top 5 Products com texto contraditório/obsoleto no pptx) |
| MINOR | 4 | R3, R5, R6, R7 |
| OBSERVATION | 2 | R2, R4 |

## Conclusão

**Nenhum BLOCKER real foi encontrado.** A correção do grão de receita (achado crítico ~8.9x
do EDA) está tratada corretamente e de forma consistente em todos os artefatos downstream
verificados (kpi_catalog.md, analytics_handoff.json, as três medidas .dax, semantic_model.md,
dax_validation.md) — não há nenhum lugar onde `SUM`/`SUMX` seja aplicado diretamente sobre o
grão de linha de `fact_orders`. A decisão de Top 5 Products por frequência está rastreável a
um teste estatístico formal e documentado (`revenue_allocation_test.md`), não a uma mera
afirmação. A cobertura de requisitos obrigatórios do PDF é completa, com gaps (YoY,
receita-por-produto) explicitamente registrados como limitação de dado em vez de omitidos.

O projeto **não está 100% pronto para publicação** por causa do achado MAJOR R1: o slide de
Product Analysis do arquivo `.pptx` — que é a fonte da verdade visual e será o que o
avaliador do case efetivamente vê — contém um subtítulo e um placeholder de corpo que
contradizem diretamente o título já corrigido acima deles ("Top 5 Produtos por Frequência
de Pedidos" seguido de "PENDENTE... não assumir eixo final"), além do estilo de card ainda
cinza/pendente em vez do padrão visual branco+dourado dos demais cards. Isso é uma correção
pontual de conteúdo/estilo no pptx (não envolve dados, DAX ou decisão de negócio — essa
parte já está fechada), mas precisa ser resolvida antes de publicar, pois é visualmente
confuso para quem abrir o dashboard. Recomenda-se ao Orchestrator encaminhar R1 ao Dashboard
Designer para correção, com autorização do usuário por se tratar de edição manual dele.
