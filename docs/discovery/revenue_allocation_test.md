# Teste de Rateio de Receita por Item — PBI_orders.xlsx

**Objetivo:** verificar se é possível substituir o KPI "Top 5 produtos por frequência" (reformulação do
Analytics Architect, documentada em `data_dictionary.md` e `data_quality_report.md`) por um
"Top 5 produtos por receita", rateando a receita do pedido entre os itens do pedido.

**Método:** leitura de `data/raw/PBI_orders.xlsx` via `py` (pandas), somente leitura — nenhum arquivo em
`data/raw/` foi alterado.

## 0. Estrutura confirmada dos dados

- `PBI_orders.xlsx`: 1.660 linhas, colunas `order_id, order_date, user_id, product_id, revenue`.
- **Confirmado**: `revenue` é idêntico em todas as linhas de um mesmo `order_id` (0 de 356 pedidos têm
  mais de um valor distinto de `revenue` entre suas linhas). Ou seja, `revenue` é o total do pedido,
  repetido por linha/item — **não existe preço por item nos dados brutos**.
- **Não existe coluna de quantidade** em `PBI_orders.xlsx` nem em `PBI_items.xlsx` (colunas de
  `PBI_items.xlsx`: `item_id, category`). Portanto **só é possível testar o rateio igualitário**
  (revenue_pedido / N itens do pedido). O rateio proporcional por quantidade não é testável — não há
  dado de base para isso.
- `PBI_items.xlsx`: 413 linhas, mas com 99 linhas duplicadas exatas (mesmo `item_id` + `category`
  repetidos). Após `drop_duplicates()`: 314 itens únicos, 0 conflitos de categoria por `item_id`.

## 1. Cálculo do rateio igualitário

Para cada pedido, `implied_price = revenue_pedido / n_itens_do_pedido`. Agregado por `product_id`
(considerando todas as ocorrências do produto em pedidos diferentes):

- 176 produtos distintos aparecem em `PBI_orders.xlsx`.
- 61 produtos aparecem em **apenas 1 pedido** (CV indefinido — nenhuma validação estatística possível).
- 131 produtos aparecem em 2+ pedidos (base válida para o teste de coerência).

### Distribuição do coeficiente de variação (CV = desvio / média) entre os 131 produtos testáveis

| Métrica | Valor |
|---|---|
| Média do CV | 0,67 |
| Mediana do CV | 0,60 |
| Desvio padrão do CV | 0,40 |
| Mínimo | 0,00 |
| Máximo | 2,02 |

| Faixa | Contagem | % |
|---|---|---|
| CV < 0,30 (preço estável, razoável) | 20 | 15% |
| CV < 0,40 (limite "aceitável" da hipótese) | 33 | 25% |
| CV > 1,00 (rateio é essencialmente ruído) | 26 | 20% |

**Apenas 1 em cada 4 produtos** fica dentro do limiar de 40% de CV proposto como "razoável". A mediana
de CV (0,60 = 60%) já está bem acima do limite de sanidade. Isso por si só indica que o preço implícito
não é estável produto a produto.

## 2. Teste (a) — estabilidade do preço implícito por produto

Falhou. Mediana de CV = 60%, 20% dos produtos com CV > 100% (ou seja, o desvio padrão do "preço" supera
a própria média — sinal clássico de ruído, não de um preço real e estável).

### Top 5 piores casos (maior CV), valores reais observados

| product_id | categoria | nº pedidos | média (R$) | desvio (R$) | mín (R$) | máx (R$) | CV |
|---|---|---|---|---|---|---|---|
| 83779 | beer | 7 | 1.614,33 | 3.258,54 | 55,06 | 8.962,62 | 2,02 |
| 49121 | beer | 116 | 1.455,57 | 2.296,58 | 32,58 | 11.465,11 | 1,58 |
| 21554 | beer | 4 | 281,34 | 440,54 | 0,00 | 934,14 | 1,57 |
| 88583 | beer | 5 | 2.399,46 | 3.712,47 | 243,59 | 8.962,62 | 1,55 |
| 71960 | nab | 8 | 18,56 | 28,69 | 0,00 | 85,38 | 1,55 |

O produto 49121 (beer), com 116 ocorrências (a maior amostra do dataset), tem preço implícito variando
de **R$ 32,58 a R$ 11.465,11** — uma faixa de quase 350x entre o mínimo e o máximo observado para o
*mesmo produto*. Isso não é compatível com a ideia de que exista um preço unitário real por trás do
rateio.

## 3. Teste (b) — comparação entre produtos da mesma categoria

| categoria | nº produtos | média dos preços médios (R$) | mediana (R$) | mín (R$) | máx (R$) | razão máx/mín |
|---|---|---|---|---|---|---|
| beer | 115 | 302,88 | 155,96 | 7,57 | 2.657,22 | **350,9x** |
| liquor | 6 | 112,58 | 108,65 | 7,89 | 249,12 | 31,6x |
| nab | 51 | 1.466,78 | 66,13 | 4,18 | 8.962,62 | **2.145,9x** |
| soda | 4 | 79,11 | 68,03 | 13,49 | 166,88 | 12,4x |

Há outliers absurdos dentro da mesma categoria: em "beer", produtos variam de R$ 7,57 a R$ 2.657,22
(350x); em "nab" — categoria que deveria ter os preços mais baixos de todo o catálogo (ex.: água,
refrigerante, guaraná) — o intervalo vai de R$ 4,18 a **R$ 8.962,62** (2.146x). A média da categoria nab
(R$ 1.466,78) fica **maior que a média de beer e liquor**, o que contradiz a própria hipótese de negócio
que motivou o teste (bebida alcoólica mais cara que não-alcoólica).

## 4. Teste (c) — valores negativos, zero ou fora de faixa plausível

- **Negativos**: nenhum.
- **Zero**: **20 produtos** têm preço implícito mínimo igual a R$ 0,00 (decorrente de 26 pedidos, de 356,
  com `revenue = 0,00` no pedido inteiro).
- **Fora de faixa plausível para bebida**: sim, e a causa raiz foi identificada:

### Caso concreto da distorção: pedido `7001094580`

Este único pedido tem `revenue = R$ 125.476,66` e **14 itens distintos** (provavelmente um pedido
corporativo/atacado, não uma compra unitária de consumidor). O rateio igualitário atribui
**R$ 8.962,62 por item** a cada um dos 14 produtos do pedido — incluindo 7 itens da categoria **nab**
(ex.: `product_id` 14132, 27665, 27935, 62234, 83261, 87039, 89368, 89964), que deveriam custar na faixa
de R$ 4 a R$ 85 segundo o resto da amostra. Para os 5 produtos nab que aparecem *somente* neste pedido,
o "preço implícito" registrado é exatamente R$ 8.962,62 — um valor ~100x a ~2000x maior que o preço
desses mesmos produtos em outros contextos.

Esse único pedido-outlier, por si só, já é suficiente para invalidar qualquer ranking de "Top 5 por
receita" construído sobre o rateio: qualquer produto que esteve nesse pedido herda um valor de receita
inflado artificialmente, deslocando-o para o topo do ranking sem relação com seu volume real de vendas.

## 5. Rateio proporcional (alternativa)

Não testável. Não existe coluna de quantidade em `PBI_orders.xlsx` nem relação de quantidade/peso em
`PBI_items.xlsx` que permita ponderar o rateio de outra forma além de "igual para todas as linhas do
pedido". O único rateio possível com os dados brutos é o igualitário já testado acima.

## 6. Conclusão objetiva

**O rateio NÃO é confiável.**

Evidência numérica:
1. Mediana do CV entre produtos = 60% (limite de sanidade proposto era 30–40%); somente 25% dos
   produtos ficam abaixo de 40% de CV.
2. 20% dos produtos têm CV > 100% (desvio maior que a própria média — ruído, não sinal).
3. Produto com maior amostra (49121, beer, 116 pedidos) varia de R$ 32,58 a R$ 11.465,11 — 350x de
   amplitude para o "mesmo" produto.
4. Dentro da categoria nab, a razão entre o preço implícito máximo e mínimo é de 2.146x; a categoria nab
   chega a ter média de preço implícito maior que beer e liquor, invertendo a hipótese de negócio que
   motivou o teste.
5. Um único pedido-outlier (`order_id` 7001094580, R$ 125.476,66, 14 itens) injeta um preço implícito de
   R$ 8.962,62 em 14 produtos de categorias distintas (incluindo nab), o que por si só já compromete
   qualquer "Top 5 por receita" calculado sobre esses dados — o ranking passaria a refletir
   quais produtos estiveram presentes nesse pedido grande, não o volume real de receita gerado por eles.
6. 20 produtos (de 176) têm preço implícito igual a R$ 0,00 por causa de pedidos com `revenue = 0`.

**Recomendação (evidência, não decisão):** os dados não suportam um "Top 5 produtos por receita" via
rateio igualitário sem mascarar graves distorções causadas por pedidos de tamanho/valor muito
heterogêneo e pela ausência de preço por item nos dados brutos. A reformulação do Analytics Architect
para "Top 5 por frequência" é consistente com a limitação real identificada aqui. A decisão final sobre
manter, ajustar ou descartar o rateio cabe ao usuário/Orchestrator — este documento apenas reporta a
evidência estatística levantada.

---
*Gerado em 2026-10-02 via `py` (pandas) sobre `data/raw/PBI_orders.xlsx` e `data/raw/PBI_items.xlsx`
(somente leitura). Nenhum arquivo em `data/raw/` foi modificado.*
