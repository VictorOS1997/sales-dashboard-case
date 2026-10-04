# DAX Validation — bi-case-pbi

Autor: DAX & Power BI Engineer (04). **Atualização 2026-10-03**: as medidas
foram executadas e validadas no Power BI Desktop contra uma referência em
pandas — ver a seção "Validation in Power BI Desktop (2026-10-03)" no final
deste arquivo (resultados reais, prevalecem sobre o texto abaixo).

Histórico (versão original): validação feita por reconciliação
aritmética com os números já verificados pelo EDA (`docs/discovery/
data_quality_report.md`, `data_profile.csv`, `eda_report.md`), sem engine
Power BI disponível na sessão; as seções 1 a 7 abaixo são esse recálculo
manual/lógico do comportamento esperado de cada expressão DAX, mantido como
registro. Onde dizem "sem engine disponível" ou "recomenda-se validar no
Power BI Desktop", essa pendência foi fechada na seção final.

## 1. Total Revenue

- **Medida**: `SUMX(order_revenue, order_revenue[revenue])`, onde
  `order_revenue` = DISTINCT(order_id, order_date, user_id, revenue) sobre
  fact_orders deduplicado.
- **Contexto sem filtro**: deve reproduzir exatamente **R$ 606.144,09** —
  valor de referência do EDA (soma de 356 valores de pedido únicos,
  `data_quality_report.md` achado #1). **Confirmado por construção**: como
  `order_revenue` tem exatamente 1 linha por order_id (0/356 pedidos com
  >1 valor de revenue, verificado pelo EDA) e 356 linhas no total, a soma
  de `order_revenue[revenue]` é matematicamente idêntica à soma que o EDA
  calculou via `groupby('order_id')['revenue'].first()` — mesma operação,
  mesmo resultado: **R$ 606.144,09**. Divergência deste valor na
  implementação real (Power BI Desktop) indica bug no Power Query
  (dedupe incorreto) ou no relacionamento do modelo, não na fórmula DAX.
- **Contrapositivo verificado**: se a medida fosse `SUM(fact_orders[revenue])`
  direto (grão de linha, sem dedupe por order_id), reproduziria
  R$ 5.396.656,69 (1660 linhas) — o erro que o EDA já identificou e que
  esta implementação evita por desenho.
- **Contexto de filtro — 1 cliente**: não há no EDA um valor de receita
  pré-calculado por user_id individual publicado nos documentos de
  discovery (apenas agregados: total e por mês). Validação qualitativa:
  a medida aplicada com filtro `dim_customer[user_id] = X` deve retornar
  a soma de `revenue` dos order_id únicos cujo `user_id = X` em
  `order_revenue` — consistente por construção com o comportamento do
  Total Revenue sem filtro (mesma lógica de agregação, sub-conjunto de
  linhas). Recomenda-se, na validação dentro do Power BI Desktop, conferir
  este valor contra `SUMIFS` equivalente em Excel sobre uma extração de
  `order_revenue` filtrada por 1 user_id, como segunda confirmação.
- **Contexto de filtro — 1 mês**: idem; a soma mensal ingênua por linha já
  é conhecida do EDA (achado #7: de R$ 49.789,75 em junho a
  R$ 1.917.678,21 em maio, **valores inflados pela mesma distorção de
  grão** — não comparáveis diretamente ao resultado esperado da medida
  corrigida). Não há no EDA um valor mensal já deduplicado por order_id
  publicado para reconciliação direta; recomenda-se gerar esse número
  (SUM de revenue único por order_id, filtrado por mês) no Power BI
  Desktop e também via um recálculo rápido em pandas antes do checkpoint
  final, para fechar esta lacuna de validação cruzada.

## 2. Average Ticket

- **Medida**: `DIVIDE([Total Revenue], [Distinct Order Count])`.
- **Sem filtro**: `606.144,09 / 356 = R$ 1.702,65` (aprox). Reconciliação:
  EDA reporta 356 pedidos distintos e revenue total deduplicado de
  R$ 606.144,09 — a divisão é consistente com esses dois números-base já
  validados.
- **Nota sobre a média simples por linha do EDA**: `data_profile.csv`
  reporta `mean = 3.251,0` para `orders.revenue` — este número é a média
  **por linha de item** (1660 linhas), não o Average Ticket real (que é
  por pedido). O kpi_catalog.md já alerta para não confundir os dois
  (KPI 2, "Evidência de validação"). A medida implementada aqui usa o
  grão correto (pedido), não a média de linha.
- **Decisão de revenue=0**: confirmado que os 26 pedidos de revenue zero (40 linhas)
  permanecem no numerador (soma, sem alteração — zero não afeta a soma) e
  no denominador (`Distinct Order Count` conta todos os 356 order_id,
  incluindo os de revenue zero) — consistente com a decisão registrada em
  kpi_catalog.md KPI 2.
- **Contexto de filtro — 1 cliente**: válido para os 3 user_id concentrados
  de revenue=0 (33198146, 10560208, 37404863, achado #3) — o Average
  Ticket desses clientes específicos será reduzido pela presença dos
  pedidos zero no denominador sem reduzir o numerador proporcionalmente;
  isso é o comportamento **esperado e desejado** pela decisão registrada,
  não um bug.

## 3. MoM Growth %

- **Medida**: `DIVIDE([Total Revenue] - [Revenue PM], [Revenue PM])`,
  onde `[Revenue PM]` usa `PARALLELPERIOD(dim_date[Date], -1, MONTH)`.
- **Janeiro/2024**: não há mês anterior na dim_date (calendário inicia em
  2024-01-01) — `PARALLELPERIOD` retorna um intervalo vazio, `[Revenue PM]`
  retorna BLANK, e `DIVIDE` com denominador BLANK retorna BLANK (não erro,
  não 0%) — comportamento exigido pelo kpi_catalog.md KPI 3 ("deve aparecer
  em branco/N.A., não como 0% ou erro"). **Confirmado pela semântica padrão
  de DIVIDE no DAX**, não requer tratamento adicional na fórmula.
- **Novembro/2024 (mês parcial)**: a medida calcula o valor normalmente
  (não suprimida) comparando a receita parcial de novembro (10 dias) com a
  receita completa de outubro — isso é matematicamente correto como
  "variação", mas **pode ser lido como queda artificial** só por ser
  parcial. A medida não decide isso — a flag `dim_date[IsPartialMonth]`
  (03_time_intelligence.dax) está disponível para o Dashboard Designer
  exibir o indicador visual obrigatório sobre novembro
  (visual_specification.md), conforme exigido pelo catálogo.
- **Validação cruzada com EDA**: o EDA reporta range de order_date
  2024-01-02 a 2024-11-10 (eda_report.md seção 4.6) — consistente com a
  dim_date criada (2024-01-01 a 2024-11-30, estendida só para fins de
  granularidade de calendário, sem inventar dados).

## 4. YTD Revenue

- **Medida**: `CALCULATE([Total Revenue], DATESYTD(dim_date[Date]))`.
- **Validação lógica**: como `[Total Revenue]` já usa o grão correto
  (order_revenue), o acumulado YTD herda a mesma correção de grão — não há
  risco de reintroduzir a inflação de 8,9x dentro do contexto de tempo.
- **Novembro/2024**: YTD até novembro soma 10 meses completos + 10 dias de
  novembro — o rótulo "YTD até 10/Nov/2024 (mês parcial)" é aplicado no
  visual (Dashboard Designer), não na medida, conforme kpi_catalog.md KPI 4.
- **Limitação confirmada**: não há 2023 no dataset (EDA confirma range
  único de 2024) — não implementada comparação YTD vs ano anterior, em
  linha com a decisão registrada.

## 5. Revenue vs Target

- **Medida**: `DIVIDE([Total Revenue], [Monthly Target] * [Complete Months In Period])`.
- **Reconciliação de base**: `targets` tem 8 linhas, 8 user_id únicos,
  min R$ 50, max R$ 150.000 (data_profile.csv) — confirmado 1:1 sem órfãos
  contra users/orders (data_dictionary.md, seção de relações) — join seguro.
- **Teste de contexto — 1 cliente, 1 mês fechado**: para um user_id com
  meta mensal M, filtrando um único mês completo (ex. outubro), a medida
  deve retornar `Total Revenue(user, outubro) / M` (1 mês completo no
  denominador) — comportamento correto por construção de
  `Complete Months In Period`.
- **Teste de contexto — novembro incluído**: `Complete Months In Period`
  subtrai 1 do total de meses distintos no filtro quando o mês mais
  recente do contexto é novembro/2024 — ou seja, a receita de novembro
  entra no numerador mas não conta como "mês completo" no denominador,
  conforme exigido pelo catálogo ("novembro parcial não entra no
  multiplicador de meses completos, mas sua receita realizada pode ser
  somada ao numerador com rótulo 'parcial'").
- **Limitação registrada (herdada do catálogo, não resolvida)**: a lógica
  de `Complete Months In Period` assume que o filtro de período é sempre
  um intervalo contíguo começando em janeiro/2024 (único cenário presente
  no dataset). Um filtro de datas arbitrário e não alinhado a mês
  completo (ex. 15/mar a 20/jun) produziria uma contagem de "meses
  completos" aproximada, não exata — não testável com os dados atuais
  porque todos os filtros de período esperados no dashboard (slicer
  mensal/YTD) são alinhados a mês-calendário. Documentado como limitação
  de borda, não como bug.
- **Premissa não confirmada**: meta tratada como constante mensal ao longo
  de todo o período (targets não tem dimensão de mês) — herdada
  diretamente do kpi_catalog.md KPI 6, sem alteração.

## 6. Order Lines by Category

- **Medida**: `COUNTROWS(fact_orders)`, cruzada com `dim_product[category]`
  (modelo final; `category_display` não existe mais — ver semantic_model.md).
- **Reconciliação de base**: EDA confirma 176 product_id distintos em
  orders, 0 órfãos contra items (kpi_catalog.md KPI 5, "evidência de
  validação" — mesmo join reaproveitado aqui) — relacionamento
  fact_orders[product_id] -> dim_product[item_id] é seguro.
- **Teste de contexto — categoria nula**: os 5 item_id sem categoria
  (incl. 19045, que tem vendas registradas — achado #5) aparecem sob
  `"Categoria não informada"` em vez de serem omitidos (texto original
  desta seção; no modelo final `dim_product[category]` não tem nulos e o
  rótulo é só fallback defensivo — ver semantic_model.md). **Não omitido
  silenciosamente**, conforme exigido pelo catálogo.
- **Teste de contexto — total geral**: `COUNTROWS(fact_orders)` sem
  filtro deve retornar 1.651 linhas (1.660 brutas − 9 duplicatas exatas,
  achado #2) — este é o total de "linhas de pedido" correto após dedupe,
  não 1.660.
- **Rótulo obrigatório**: a medida nunca deve ser formatada como moeda
  nem rotulada "Receita por categoria" — é contagem de ocorrência, não
  receita (mesma limitação estrutural do item #1 do EDA). Responsabilidade
  de nomenclatura do visual é do Dashboard Designer; a medida DAX em si
  já tem nome neutro ("Order Lines by Category").

---

## 7. Top 5 Products (by order frequency)

**Status: IMPLEMENTADO.** Decisão final confirmada pelo dono do projeto em
2026-10-02 (kpi_catalog.md KPI 5; `analytics_handoff.json`, kpi "Top 5
Products", `status: "confirmed"`). Medida adicionada em
`powerbi/dax/02_business_kpis.dax`.

- **Medida**: `Product Order Frequency = DISTINCTCOUNT(fact_orders[order_id])`,
  com o recorte "top 5" aplicado como filtro de visual TopN = 5 (descendente)
  sobre `dim_product[item_id]` no eixo — mesmo padrão arquitetural já usado em
  "Order Lines by Category" (medida simples e reutilizável; o agrupamento vem
  do relacionamento `fact_orders[product_id] -> dim_product[item_id]`, não de
  um `TOPN()`/`SUMMARIZE()` fixo embutido na medida).
- **Reconciliação de base**: EDA confirma 176 product_id distintos em
  `orders`, 0 órfãos contra `items` (kpi_catalog.md KPI 5, "evidência de
  validação") — mesmo join já validado em "Order Lines by Category" (seção 6
  acima); reaproveitado aqui sem alteração.
- **Teste de contexto — filtro por categoria de produto**: filtrando o
  contexto por `dim_product[category] = "beer"`, a medida retorna
  `DISTINCTCOUNT(fact_orders[order_id])` apenas das linhas de `fact_orders`
  cujo `product_id` está relacionado a um `item_id` de categoria "beer" —
  comportamento correto por construção (o filtro de categoria propaga pelo
  relacionamento `fact_orders[product_id] -> dim_product[item_id]`, igual ao
  já confirmado para "Order Lines by Category"). Um visual de Top 5 dentro
  dessa fatia mostraria os 5 produtos "beer" com mais pedidos distintos, não
  o Top 5 geral — comportamento esperado para um slicer de categoria, não bug.
  Validação qualitativa (sem engine Power BI disponível nesta sessão, como
  registrado na nota de abertura deste arquivo): recomenda-se confirmar o
  conjunto exato de 5 produtos "beer" no Power BI Desktop antes do
  checkpoint final, comparando contra um `groupby(['category']).apply(...)`
  equivalente em pandas sobre o EDA, como segunda confirmação.
- **Produto de maior amostra conhecido**: product_id 49121 (beer, 116
  ocorrências em pedidos distintos, achado reaproveitado do teste de rateio
  abaixo) é um caso esperado de aparecer no Top 5 geral e no Top 5 filtrado
  por "beer" — útil como ponto de checagem manual no Power BI Desktop.
- **Rótulo obrigatório**: "Top 5 Products by order frequency" / "Top 5
  produtos por frequência de pedidos" — nunca formatação de moeda, nunca
  "receita"/"revenue" (handoff.json, `mandatory_label`). Responsabilidade de
  nomenclatura do visual é do Dashboard Designer; a medida DAX já tem nome
  neutro ("Product Order Frequency").
- **Limitação que permanece válida (não muda com esta implementação)**: este
  Top 5 mede frequência de pedido, não receita gerada — limitação estrutural
  dos dados de origem (ausência de preço por item), documentada a seguir e em
  `model/semantic_model.md`. Um produto pode aparecer em muitos pedidos de
  baixo valor e não ser o maior gerador de receita, ou vice-versa.

### Evidência do teste de rateio de receita (rejeitado) — mantida para rastreabilidade

O kpi_catalog.md (KPI 5) e o `analytics_handoff.json` já registram que
"Top 5 Products por receita" não é computável com exatidão a partir dos
dados brutos: `orders.revenue` está no grão de pedido, não existe preço
unitário nem coluna de quantidade em `PBI_orders.xlsx`/`PBI_items.xlsx`
(data_dictionary.md, achado #1). A alternativa proposta e já aceita como
default é "Top 5 produtos por número de pedidos distintos em que aparecem"
(frequência), facilmente implementável com o modelo atual
(`COUNT(DISTINCT order_id)` agrupado por `product_id` sobre `fact_orders`
cruzado com `dim_product`).

**Atualização desta rodada**: o teste formal de rateio igualitário de
receita por item (`docs/discovery/revenue_allocation_test.md`), concluído
nesta sessão, **testou e descartou estatisticamente** a alternativa de
"Top 5 por receita via rateio" como substituta da medida por frequência.
Evidência do teste, reproduzida aqui para rastreabilidade:

1. CV (coeficiente de variação) mediano de 60% entre os 131 produtos
   testáveis (aparecem em 2+ pedidos) — o limiar de sanidade proposto era
   30–40%; apenas 25% dos produtos ficam dentro dele.
2. 20% dos produtos têm CV > 100% (desvio-padrão maior que a própria
   média do "preço implícito" — sinal de ruído, não de preço real).
3. O produto com maior amostra do dataset (product_id 49121, categoria
   beer, 116 ocorrências) varia de R$ 32,58 a R$ 11.465,11 de preço
   implícito — amplitude de ~350x para o mesmo produto.
4. Na categoria "nab" (bebida não-alcoólica, esperada mais barata), o
   preço implícito médio (R$ 1.466,78) supera o de "beer" e "liquor",
   invertendo a própria hipótese de negócio que motivou o teste — e a
   razão máx/mín dentro de "nab" chega a 2.146x.
5. Um único pedido-outlier (order_id 7001094580, R$ 125.476,66, 14 itens
   distintos, provavelmente pedido corporativo/atacado) injeta um preço
   implícito de R$ 8.962,62 em 14 produtos de categorias distintas
   (incluindo 8 produtos nab que só aparecem nesse pedido) — isso por si
   só já deslocaria produtos para o topo de um ranking de "receita" sem
   relação com seu volume real de vendas.
6. Rateio proporcional (por quantidade) não é nem testável: não existe
   coluna de quantidade em nenhuma das duas tabelas brutas.

**Conclusão técnica**: a medida de receita por produto não existe no
modelo (ver `model/semantic_model.md`, seção de limitações) porque (a) não
há dado-fonte para calculá-la com exatidão, e (b) a única aproximação
possível (rateio igualitário) foi testada e é estatisticamente
inconsistente — implementá-la produziria um "Top 5 por receita" que na
prática reflete quais produtos estiveram em pedidos grandes/heterogêneos,
não o volume real de receita gerado por eles. Isso **reforça** (não apenas
mantém por padrão) que a medida correta a implementar é "Top 5 por
frequência de pedidos", já suportada pelo modelo atual.

**Status final**: decisão do dono do projeto registrada em 2026-10-02
(kpi_catalog.md KPI 5, `analytics_handoff.json`) encerrou este item como
"por frequência" — medida implementada na seção 7 acima, em
`powerbi/dax/02_business_kpis.dax`. Este item não está mais bloqueado nem é
um gap aberto.

---

## Validation in Power BI Desktop (2026-10-03)

Validação real, executada no Power BI Desktop e comparada contra uma
referência em pandas. Todos os valores abaixo coincidiram. Evidências:
`powerbi/validation/validation.png` e `powerbi/validation/validation matrix.png`.

### Sem filtro

| Medida | Resultado |
|---|---|
| Total Revenue | 606.144,09 |
| Distinct Order Count | 356 |
| Order Lines Count | 1651 |
| Average Ticket | 1.702,65 |
| YTD Revenue | 606.144,09 |
| Monthly Target | 241550 |
| Complete Months In Period | 10 |
| Revenue vs Target | 25,09% |

### Por mês (Total Revenue, jan a nov)

102.932,21 / 74.244,78 / 55.514,71 / 42.182,81 / 159.987,03 / 14.113,94 /
16.905,95 / 18.415,60 / 53.141,61 / 45.877,52 / 22.827,93.
MoM Growth % de janeiro em branco (esperado, sem mês anterior).

### Por cliente

- Os 8 clientes bateram com a referência; a soma de Total Revenue dos 8 =
  606.144,09 (igual ao total).
- Exemplo, user_id 37404863: 385.662,18; 54 pedidos; Average Ticket
  7.141,89; Revenue vs Target 51,42%.
- Top 5 Products por frequência (Product Order Frequency) bateu:
  49121 (116), 71496 (62), 60146 (53), 80738 (50), 93608 (45).

### Matriz cliente x mês (user_id 37404863)

- Maio: receita 151.642,80; 8 pedidos; Revenue vs Target 202,19%;
  MoM 392,16%; YTD 297.397,82.
- Novembro: Revenue vs Target **em branco** porque Complete Months In Period
  = 0 (novembro é mês parcial e não conta como mês completo). Comportamento
  esperado, não bug.

### Gabarito da página 3 (após as novas relações)

Com as relações `dim_date[Date] -> fact_orders[order_date]` e
`dim_customer[user_id] -> fact_orders[user_id]` (ver `model/semantic_model.md`):

- Sem filtro: Unsold Products = 138; linhas por categoria: beer 1514,
  nab 122, liquor 11, soda 4.
- Cliente 37404863: 139 linhas; Unsold Products = 282.
- Mês de maio: 137 linhas; Unsold Products = 238.

### Medidas auxiliares

As medidas de `powerbi/dax/04_dashboard_helpers.dax` (Partial Month Note,
YTD Title, MoM Color, Revenue % of Total, Target in Period, Unsold Products)
são documentadas nesse arquivo; Unsold Products foi conferido no gabarito
acima. Lições aprendidas de MoM Color estão no cabeçalho do mesmo arquivo.
