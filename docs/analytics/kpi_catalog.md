# KPI Catalog — bi-case-pbi

Convenção de modelo estrela assumida (para a coluna "campos"): `fact_orders` deduplicado a
`DISTINCT order_id, order_date, user_id, revenue` + tabela ponte `fact_order_lines`
(order_id, product_id) para a relação N:N pedido↔produto, OU uma tabela auxiliar
`order_revenue` (1 linha por order_id com revenue) usada nas medidas de receita, mantendo
`fact_orders` original (grão de linha) só para contagens de produto. A decisão final de
modelagem física é do DAX Engineer; aqui se define o contrato de **o que a medida precisa
calcular**, não a sintaxe DAX.

---

## 1. Total Revenue

- **Definição de negócio**: soma da receita de todos os pedidos únicos no período filtrado.
- **Fórmula**: `SUM(revenue)` calculado sobre **uma linha por `order_id`** (após
  `DISTINCT`/dedupe de `fact_orders` nas 9 linhas totalmente duplicadas, achado #2). Nunca
  somar a tabela `fact_orders` no grão de linha-de-item diretamente.
- **Campos**: `orders.order_id`, `orders.revenue`, `orders.order_date` (para filtro de
  período).
- **Granularidade de exibição**: total, por mês, por cliente, por categoria de cliente, por
  cidade — todas derivadas do mesmo valor de pedido deduplicado.
- **Filtros aplicáveis**: período (date slicer), cliente, cidade, categoria de estabelecimento.
  Não filtra por produto/categoria de produto com exatidão (ver limitação).
- **Evidência de validação**: EDA confirmou 0 de 356 `order_id` com mais de 1 valor distinto de
  `revenue` entre suas linhas (`data_quality_report.md`, achado #1). Valor correto de
  referência: R$ 606.144,09 (soma de 356 valores de pedido únicos) vs R$ 5.396.656,69 se somado
  ingenuamente por linha — razão de inflação ~8,9x. **Este valor de referência (606.144,09)
  deve ser o resultado reproduzido pela medida DAX final; qualquer divergência é bug, não
  variação aceitável.**
- **Limitações**: moeda/unidade não confirmada no PDF nem nos dados (assumida consistente com
  `targets.monthly revenue target`, não validada por fonte externa). Inclui as 40 linhas de
  revenue=0 (pedidos válidos mantidos, ver Average Ticket).

---

## 2. Average Ticket

- **Definição de negócio**: valor médio de receita por pedido.
- **Fórmula**: `SUM(revenue por order_id único) / COUNT(order_id único)`.
- **Campos**: `orders.order_id`, `orders.revenue`.
- **Granularidade**: total, por mês, por cliente.
- **Filtros aplicáveis**: mesmos de Total Revenue.
- **Decisão sobre revenue=0 (achado #3)**: os 40 pedidos com revenue=0 **permanecem no
  numerador E no denominador** — não há evidência nos dados de que sejam erro de carga
  (distribuídos em 9 de 11 meses, concentrados em 3 clientes restaurant, sem padrão de
  sistema). Tratá-los como exclusão seria assumir "erro" sem prova; mantê-los é a opção
  conservadora e documentada. Reportar a métrica alternativa "Average Ticket (excl.
  revenue=0)" apenas se solicitado explicitamente em revisão — não implementar por padrão.
- **Evidência de validação**: 304 valores distintos de revenue em 356 pedidos (eda
  data_profile.csv); min 0,0, max 125.476,66, média simples por linha 3.251,0 (não confundir
  com o Average Ticket real, que deve usar o grão de pedido, não de linha).
- **Limitações**: decisão sobre revenue=0 é uma escolha registrada, não uma certeza de dado —
  se o negócio confirmar que são erro, a medida deve ser revisada pelo Analytics Architect.

---

## 3. Month-over-Month Growth (%)

- **Definição de negócio**: variação percentual da receita (grão correto) entre o mês corrente
  e o mês anterior.
- **Fórmula**: `(Total Revenue mês atual − Total Revenue mês anterior) / Total Revenue mês
  anterior`, calculado sobre a série mensal de Total Revenue (já no grão de pedido).
- **Campos**: `orders.order_date` (mês), Total Revenue (medida acima).
- **Granularidade**: mensal.
- **Filtros aplicáveis**: cliente, cidade, categoria (a variação pode ser recalculada dentro de
  qualquer fatia, mas a leitura de tendência é mais confiável no agregado total dado o n=8 de
  clientes).
- **Tratamento obrigatório de novembro/2024 (achado #7)**: novembro tem apenas 10 dias de
  dados (cobertura até 2024-11-10). A medida de MoM deve ser calculada normalmente (não
  suprimida), mas **todo visual que exiba MoM precisa carregar um indicador visual/textual de
  "mês parcial"** sobre a barra/ponto de novembro — ver `visual_specification.md`. Não há mês
  de dezembro/2024 nos dados; o dashboard não deve simular ou extrapolar dezembro.
- **Evidência de validação**: `eda_report.md` seção 4.6 — range de order_date 2024-01-02 a
  2024-11-10, confirmado via leitura completa sem amostragem.
- **Limitações**: sem dado de 2023, YoY não é computável; MoM de janeiro não tem mês anterior
  dentro do dataset (deve aparecer em branco/N.A., não como 0% ou erro).

---

## 4. Year-to-Date Revenue (YTD)

- **Definição de negócio**: receita acumulada desde o início do ano (2024-01-02) até a data
  (ou mês) selecionada.
- **Fórmula**: soma cumulativa de Total Revenue (grão de pedido) de janeiro até o mês
  filtrado/corrente.
- **Campos**: `orders.order_date`, Total Revenue (medida acima).
- **Granularidade**: mensal (acumulado até o mês).
- **Filtros aplicáveis**: cliente, cidade, categoria de estabelecimento.
- **Tratamento de novembro**: o YTD até novembro/2024 é um acumulado de 10 meses completos +
  10 dias de novembro — rotular explicitamente "YTD até 10/Nov/2024 (mês parcial)" em vez de
  apresentar como "YTD Novembro" sem qualificação, para não sugerir que representa o mês
  inteiro.
- **Evidência de validação**: mesma base de Total Revenue, já validada acima.
- **Limitações**: como só há 1 ano de dados, YTD não tem comparação YTD-ano-anterior possível
  — não implementar essa comparação (não forçar, conforme achado #7).

---

## 5. Top 5 Products

- **Definição de negócio reformulada (gap do case, decisão explícita)**: o case pede "Top 5
  products" — presumivelmente por receita. **Não computável com exatidão**: `orders.revenue`
  é um valor de pedido, não de item; não há preço unitário nem regra de rateio por produto nos
  dados brutos (ver `data_quality_report.md`, achado #1, e `eda_report.md` seção 7).
  **KPI implementado**: "Top 5 produtos por número de pedidos distintos em que aparecem"
  (frequência de presença/popularidade), explicitamente rotulado como tal em todo visual —
  nunca apresentado com formatação de moeda ou rótulo "receita".
- **Fórmula**: `COUNT(DISTINCT order_id)` agrupado por `product_id`, ordenado desc, top 5.
- **Campos**: `orders.product_id`, `orders.order_id`, `items.item_id` (join para nome/categoria
  do produto, se houver nome — revisar se `items` tem coluna de nome do produto; nos campos
  validados pelo EDA só há `item_id` e `category`, portanto o rótulo de exibição pode precisar
  ser "Produto #<item_id>" se não houver nome de produto na base).
- **Granularidade**: por produto, total do período ou por mês.
- **Filtros aplicáveis**: cliente, cidade, categoria de estabelecimento, mês.
- **Evidência de validação**: 176 product_id distintos em orders, 0 órfãos contra items.
- **Decisão final (confirmada pelo dono do projeto em 2026-10-02)**: Top 5 Products é, em
  caráter definitivo, por **frequência em pedidos** — não por receita. Este item está encerrado,
  não é mais um gap aberto.
- **Teste de alternativa (rateio de receita) — EXECUTADO e REJEITADO**: `docs/discovery/
  revenue_allocation_test.md` testou ratear `revenue` do pedido igualmente entre suas linhas de
  item (único rateio testável — não há coluna de quantidade nos dados brutos) e concluiu que o
  rateio **não é estatisticamente confiável**:
  - mediana do CV (coeficiente de variação) do "preço implícito" por produto = 60% (limite de
    sanidade proposto era 30–40%); apenas 25% dos 131 produtos testáveis ficam abaixo de 40% de CV;
  - o produto com maior amostra (49121, beer, 116 pedidos) varia de R$ 32,58 a R$ 11.465,11 —
    ~350x de amplitude para o mesmo produto;
  - na categoria "nab" (bebidas não-alcoólicas, que deveriam ser as mais baratas), a razão
    preço-implícito máximo/mínimo chega a 2.146x, e a média da categoria fica **maior** que a de
    "beer" e "liquor" — invertendo a própria hipótese de negócio que motivou o teste;
  - um único pedido-outlier (`order_id` 7001094580, R$ 125.476,66, 14 itens distintos) injeta um
    preço implícito de R$ 8.962,62 em 14 produtos de categorias diferentes (incluindo 7 da
    categoria "nab"), contaminando qualquer ranking construído sobre o rateio.
  Conclusão: a alternativa de rateio foi testada formalmente e descartada com evidência
  estatística, não por suposição. Frequência em pedidos permanece como único critério válido com
  os dados brutos disponíveis.
- **Limitações (registrar de forma visível no dashboard, não só aqui)**: este Top 5 mede
  frequência de pedido, não receita gerada. Um produto pode aparecer em muitos pedidos de baixo
  valor e não ser o maior gerador de receita, ou vice-versa. Isso é uma limitação estrutural dos
  dados de origem (ausência de preço por item), não uma escolha arbitrária — ver teste de rateio
  acima para a evidência que fecha essa questão.

---

## 6. Revenue vs Target (Meta) — KPI adicional ("outras conforme necessário")

- **Definição de negócio**: aderência da receita realizada (grão correto) à meta mensal de
  receita por cliente.
- **Fórmula**: `Total Revenue (por user_id, no período) / (targets.'monthly revenue target' ×
  nº de meses completos no período filtrado)`. Para período parcial (ex.: YTD até novembro),
  multiplicar a meta mensal pelo nº de meses fechados; novembro parcial não entra no
  multiplicador de meses completos, mas sua receita realizada pode ser somada ao numerador com
  rótulo "parcial".
- **Campos**: `orders.revenue` (grão de pedido), `orders.user_id`, `orders.order_date`,
  `targets.user_id`, `targets.'monthly revenue target'`.
- **Granularidade**: por cliente, agregável por categoria de estabelecimento ou cidade.
- **Filtros aplicáveis**: cliente, cidade, categoria, período.
- **Evidência de validação**: 8 de 8 `user_id` de `targets` batem 1:1 com `users`/`orders`, sem
  órfãos (`data_dictionary.md` seção de relações).
- **Limitações**: `targets` tem apenas 1 valor de meta por cliente, sem dimensão de mês — a
  meta é tratada como constante mensal ao longo de todo o período (premissa necessária, não
  confirmada pelo PDF nem pelos dados — registrar isso na aba de conclusão). Moeda não
  confirmada como igual a `orders.revenue` (plausível, não comprovada).

---

## 7. KPI adicional — Receita por Categoria de Produto (contagem de linha, não receita real)

- **Definição de negócio**: participação de cada categoria de bebida (beer/nab/liquor/soda) no
  volume de pedidos.
- **Fórmula**: `COUNT(linhas de fact_orders, grão de item)` agrupado por `items.category`,
  via join `orders.product_id = items.item_id` (dimensão de produto deduplicada por DISTINCT
  item_id antes do join, achado #4).
- **Campos**: `orders.product_id`, `items.item_id`, `items.category`.
- **Granularidade**: por categoria, por mês, por cliente.
- **Rótulo obrigatório**: "Linhas de pedido por categoria" ou "Presença de categoria em
  pedidos" — **nunca rotular como "Receita por categoria de produto"**, pois não é receita, é
  contagem de ocorrência de item em pedido (mesma limitação do Top 5 Products).
- **Tratamento de category nula (achado #5)**: 5 item_id sem categoria (incluindo ao menos 1
  com vendas registradas, item_id 19045) aparecem em um bucket explícito "Categoria não
  informada" — não omitidos silenciosamente do total.
- **Evidência de validação**: `data_dictionary.md` seção 1; `data_quality_report.md` achado #5.
- **Limitações**: mesma limitação estrutural de ausência de receita por item (achado #1).

---

## Resumo de rastreabilidade (requisito → KPI → evidência)

| Requisito do case (PDF) | KPI | Evidência EDA |
|---|---|---|
| Total Revenue | KPI 1 | data_quality_report.md achado #1 |
| Average Ticket | KPI 2 | data_quality_report.md achado #3 |
| MoM growth (%) | KPI 3 | data_quality_report.md achado #7 |
| YTD revenue | KPI 4 | data_quality_report.md achado #7 |
| Top 5 products | KPI 5 (reformulado, decisão final confirmada) | data_quality_report.md achado #1; eda_report.md seção 7; discovery/revenue_allocation_test.md (teste de rateio rejeitado) |
| Others as deemed necessary | KPI 6 (Revenue vs Target), KPI 7 (categoria) | data_dictionary.md relações; achado #5 |
