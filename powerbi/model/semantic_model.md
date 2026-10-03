# Semantic Model — bi-case-pbi

Autor: DAX & Power BI Engineer (04). Base: `docs/analytics/kpi_catalog.md`,
`docs/analytics/analytics_handoff.json`, `docs/discovery/data_dictionary.md`,
`docs/discovery/data_quality_report.md`. Decisão final de modelagem física
é deste agente, dentro do contrato definido pelo Analytics Architect
(kpi_catalog.md, cabeçalho).

## Problema central de grão

`PBI_orders.xlsx` tem grão de **linha de item de pedido** (order_id × product_id),
mas `revenue` está no grão de **pedido**, repetido em cada linha (achado #1 /
EDA). Qualquer `SUM(revenue)` direto sobre a tabela no grão de linha infla o
total em ~8,9x (R$ 5.396.656,69 vs R$ 606.144,09 correto). Isso exige uma
tabela adicional no grão de pedido para toda medida de receita, mantendo a
tabela no grão de linha apenas para contagens de item/categoria.

## Tabelas do modelo

### fact_orders (grão de linha de pedido)
- Fonte: `PBI_orders.xlsx`.
- Transformação no Power Query: `Remove Duplicates` sobre as 5 colunas
  (order_id, order_date, user_id, product_id, revenue) — remove as 9 linhas
  100% duplicadas (achado #2). 1.651 linhas resultantes (1.660 − 9).
- Uso: apenas contagem/presença de item em pedido (`Order Lines Count`,
  `Order Lines by Category`). **Nunca usada para SUM(revenue)**.
- Colunas: order_id, order_date, user_id, product_id, revenue.

### order_revenue (grão de pedido — tabela nova, criada no Power Query)
- Derivada de fact_orders: `DISTINCT (order_id, order_date, user_id, revenue)`
  — como revenue é constante por order_id (0/356 violações verificadas no
  EDA), isso produz exatamente 1 linha por order_id, 356 linhas.
- É a única tabela usada para somar `revenue` (Total Revenue, Average Ticket,
  MoM, YTD, Revenue vs Target).
- Relaciona-se com dim_date (order_date -> Date, N:1) e dim_customer
  (user_id -> user_id, N:1).
- Alternativa de implementação equivalente, caso o time prefira evitar uma
  tabela extra: medida `SUMX(VALUES(fact_orders[order_id]), CALCULATE(MAX(fact_orders[revenue])))`.
  Optou-se por materializar `order_revenue` como tabela separada por ser
  mais legível, mais performático (evita reavaliar MAX por contexto de
  linha a cada chamada) e deixar o contrato de grão explícito no modelo —
  reduz risco de um futuro mantenedor somar `fact_orders[revenue]` por
  engano.

### dim_product
- Fonte: `PBI_items.xlsx`.
- Transformação: `Remove Duplicates` sobre (item_id, category) — remove as
  99 duplicatas de item_id / 94 linhas 100% duplicadas (achado #4; 0
  conflitos de categoria confirmados pelo EDA, dedupe seguro). 314 linhas
  resultantes.
- Tratamento de categoria nula (achado #5, 5 item_id incl. 19045 com
  vendas): coluna calculada/Power Query `category_display` =
  `IF(ISBLANK(category), "Categoria não informada", category)`, usada em
  todo visual de categoria em vez da coluna bruta `category`.
- Relaciona-se com fact_orders (item_id -> product_id, 1:N).

### dim_customer
- Fonte: `PBI_users.xlsx`, 8 linhas, 1 por user_id.
- Tratamento de cidade (achado #6): coluna `city_display` via De-Para
  (Power Query): SP -> São Paulo, RJ -> Rio de Janeiro, Campinas inalterado,
  nulo (user_id 83095742) -> "Não informado" (nunca descartado).
- Relaciona-se com order_revenue (user_id -> user_id, 1:N) e com targets
  (user_id -> user_id, 1:1).
- **Limitação estrutural**: apenas 8 clientes no dataset inteiro — qualquer
  segmentação por cliente/categoria/cidade opera sobre n=8. Deve carregar
  banner de limitação estatística em qualquer página de Customer Analysis
  (responsabilidade do Dashboard Designer, registrada aqui para
  rastreabilidade).

### dim_date (tabela calculada, ver 03_time_intelligence.dax)
- Não existe nos dados brutos — criada via `CALENDAR` de 2024-01-01 a
  2024-11-30 (cobertura real do dataset é até 2024-11-10; estende-se até
  fim do mês apenas para o calendário ter granularidade mensal completa,
  sem inventar dias de dados).
- Marcada como **Date Table** no modelo (propriedade do Power BI), com
  coluna `[Date]` como chave de marcação.
- Coluna `IsPartialMonth` sinaliza novembro/2024 (dados reais só até dia
  10) para consumo pelo Dashboard Designer nos visuais de MoM/YTD.
- Relaciona-se com order_revenue (Date -> order_date, 1:N, filtro de
  dim_date para order_revenue).

### targets
- Fonte: `PBI_targets.xlsx`, 8 linhas, 1 por user_id, sem dimensão de mês.
- Tratamento de cidade: mesmo De-Para de dim_customer (já é consistente
  internamente, mas divergia de users antes do De-Para — achado #6).
- Relacionamento 1:1 com dim_customer por user_id. Usada apenas pela
  medida `Revenue vs Target`.

## Diagrama de relacionamentos

```
dim_date (calendário, Date Table)
      |  1:N  (Date -> order_date)
      v
order_revenue (grão de pedido, 356 linhas)  ---- N:1 (user_id) ----  dim_customer ---- 1:1 (user_id) ---- targets
      ^
      | (mesmo order_id, relação lógica — NÃO modelada como relacionamento
      |  físico ativo no Power BI; order_revenue e fact_orders compartilham
      |  order_id mas servem propósitos de agregação diferentes e não
      |  precisam de JOIN explícito entre si no modelo estrela)

fact_orders (grão de linha, 1.651 linhas)  ---- N:1 (product_id -> item_id) ----  dim_product
      |
      | N:1 (user_id -> user_id) — opcional, só necessário se algum visual
      |  cruzar linha de item com cliente sem passar por revenue
      v
dim_customer
```

**Nota de modelagem**: `order_revenue` e `fact_orders` não têm relacionamento
físico direto entre si no Power BI (ambas se relacionam independentemente com
dim_date/dim_customer/dim_product pelos seus próprios campos). Isso é
intencional: evita ambiguidade de filtro cruzado e mantém cada tabela no seu
papel — `order_revenue` para receita, `fact_orders` para contagem de
item/categoria. Qualquer visual que precise cruzar "receita" E "categoria de
produto" ao mesmo tempo com exatidão **não é suportado pelos dados brutos**
(achado #1 — não há receita por item), e não deve ser forçado.

## Por que não um esquema estrela "tradicional" único

O catálogo de KPI (cabeçalho) já previa duas alternativas equivalentes:
(a) fact_orders deduplicado ao grão de pedido + tabela ponte N:N
order_id↔product_id, ou (b) tabela auxiliar `order_revenue` (grão de
pedido) + fact_orders original (grão de linha) mantida separada para
contagens. Optou-se pela alternativa (b) por ser mais simples de
implementar em DAX (evita medidas com SUMMARIZE/TREATAS para simular a
ponte N:N) e por deixar o contrato de "receita é por pedido, não por item"
explícito na própria estrutura do modelo, reduzindo risco de erro futuro —
alinhado à regra do agente de preferir medidas simples e não duplicar
lógica.

## Limitações carregadas do EDA (não resolvidas pela modelagem, apenas contornadas)

- Não é possível calcular receita por produto/item com exatidão — nenhuma
  tabela/relacionamento neste modelo tenta resolver isso (ver KPI 5 — Top 5
  Products, implementado por frequência, em `validation/dax_validation.md`).
  Isso não é apenas
  ausência de dado-fonte (sem preço unitário/quantidade): um teste
  estatístico formal de rateio igualitário de `revenue` entre os itens de
  cada pedido (`docs/discovery/revenue_allocation_test.md`) **confirmou que
  a alternativa é estatisticamente inconsistente**, não apenas indisponível
  — CV mediano de 60% entre produtos (limiar de sanidade proposto era
  30–40%), um produto com 350x de amplitude de preço implícito entre
  pedidos (product_id 49121, 116 ocorrências), a categoria "nab" resultando
  em preço médio maior que "beer"/"liquor" (invertendo a própria hipótese de
  negócio que motivou o teste), e um único pedido-outlier de R$ 125.476,66
  contaminando o preço implícito de 14 produtos de categorias distintas.
  Por isso este modelo **não inclui** nenhuma tabela/coluna de "receita por
  produto" nem via rateio: a decisão de modelagem é que essa métrica não
  deve existir no modelo até/menos que o negócio valide explicitamente uma
  regra de alocação diferente (ex.: fornecendo preço unitário real). A
  medida "Top 5 Products" foi fechada pelo dono do projeto em 2026-10-02 como
  "por frequência" (`Product Order Frequency` em
  `powerbi/dax/02_business_kpis.dax`, suportada pelo modelo atual via
  `fact_orders`) — não é mais um item pendente/bloqueado; a limitação de
  receita-por-produto acima, porém, continua válida e não muda com essa
  implementação.
- Moeda/unidade de `revenue` e `monthly revenue target` não confirmada por
  fonte externa — assumida consistente entre as duas, não validada.
- `targets` não tem dimensão de mês — tratado como constante mensal ao
  longo de todo o período em `Revenue vs Target` (premissa registrada em
  02_business_kpis.dax).
- Apenas 1 ano de dados — sem YoY, sem comparação YTD-ano-anterior.
