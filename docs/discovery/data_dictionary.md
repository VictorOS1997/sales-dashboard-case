# Data Dictionary — bi-case-pbi

Fonte: `data/raw/PBI_items.xlsx`, `PBI_orders.xlsx`, `PBI_targets.xlsx`, `PBI_users.xlsx`.
Método de leitura: Python 3.12 (`py`) + pandas 3.0.6 + openpyxl 3.1.5 (instalados nesta sessão
via `py -m pip install`, pois não havia `python3`/pandas/openpyxl previamente disponíveis — ver
limitações no `data_quality_report.md`). Leitura completa de todas as linhas de todas as sheets,
sem amostragem — cada workbook tem uma única sheet de dados (`items` em `PBI_items.xlsx`;
`Sheet1` nos demais).

Contexto de negócio (`docs/Power_BI_–_Activities_Data.pdf`): case de BI para a ABI
(Anheuser-Busch InBev — inferido do nome "ABI" no PDF, não confirmado explicitamente no
documento). Pede-se um modelo estrela com medidas de Total Revenue, Average Ticket,
MoM growth, YTD revenue, Top 5 produtos, e dashboard executivo com análise temporal, de
produto e de cliente. O PDF não descreve o schema dos dados — apenas o objetivo do case —
então toda interpretação de negócio abaixo vem exclusivamente da inspeção dos 4 arquivos.

---

## 1. PBI_items.xlsx (sheet `items`)

Grão aparente: um produto por linha (dimensão de produto/item).

| Coluna | Tipo | % nulos | Cardinalidade | Observações |
|---|---|---|---|---|
| item_id | int64 | 0% | 314 valores únicos em 413 linhas | **Chave candidata, mas NÃO é única na tabela** — 99 item_id aparecem em mais de uma linha (198 linhas envolvidas). Em todos os casos verificados a categoria é idêntica entre as linhas duplicadas (0 conflitos de categoria) — ver `data_quality_report.md`. |
| category | string | 1.21% (5 linhas) | 4 valores: `beer`, `nab`, `liquor`, `soda` | Categoria de produto (tipo de bebida). `nab` provavelmente = "non-alcoholic beverage". 5 linhas nulas, mas todas pertencem a `item_id` duplicados (ver Achado #4) cuja categoria está preenchida na linha duplicada irmã — nenhum `item_id` está de fato sem categoria conhecida (ver Achado #5 revisado em `data_quality_report.md`); ao deduplicar, preferir o valor não nulo em vez de `Remove Duplicates` ingênuo. **Status: Resolvido no ETL** (Group By `item_id` + Max(`category`) → `dim_product` 314 linhas, todas com categoria). |

Interpretação de negócio: tabela de produtos (bebidas) com categoria de tipo de bebida —
candidata a dimensão `dim_product` no modelo estrela, após deduplicação de `item_id`.

---

## 2. PBI_orders.xlsx (sheet `orders`)

Grão real (verificado, não assumido): **uma linha por item de pedido (order line)**, não uma
linha por pedido. `order_id` se repete de 1 a 30 vezes (356 order_id distintos em 1660 linhas).

| Coluna | Tipo | % nulos | Cardinalidade | Observações |
|---|---|---|---|---|
| order_id | int64 | 0% | 356 únicos / 1660 linhas | Identifica o pedido, não a linha. Repetição = número de produtos distintos no pedido (média 4.64 produtos/pedido, máx 29). |
| order_date | datetime64 | 0% | 181 datas distintas | Range observado: 2024-01-02 a 2024-11-10. Granularidade diária, sem hora. |
| user_id | int64 | 0% | 8 únicos | FK para `PBI_users.xlsx` / `PBI_targets.xlsx` — os 8 valores batem exatamente com os 8 user_id de ambas as tabelas (sem órfãos em nenhuma direção). |
| product_id | int64 | 0% | 176 únicos | FK para `PBI_items.xlsx.item_id`. Todos os 176 valores de `product_id` existem em `items.item_id` (0 órfãos). 138 dos 314 item_id de `items` nunca aparecem em `orders` (produtos sem venda registrada no período). |
| revenue | float64 | 0% | 304 valores distintos | **ACHADO CRÍTICO DE GRÃO**: `revenue` é constante dentro de cada `order_id` (verificado: 0 de 356 pedidos têm mais de um valor distinto de revenue entre suas linhas). Ou seja, `revenue` está no grão do **pedido**, repetido em cada linha de item desse pedido — não é a receita daquele item específico. Ver `data_quality_report.md` para o impacto quantificado (SUM ingênuo infla a receita em ~8.9x). |

Interpretação de negócio: tabela de fatos de pedidos/vendas. É a tabela fato central do modelo
estrela, mas **a receita não pode ser somada diretamente por linha** — é necessário agregar por
`order_id` primeiro (ex.: `revenue` por `order_id` único) antes de somar, ou tratar `order_id`
como grão da métrica de receita e `product_id` apenas como dimensão de "quais produtos
compuseram o pedido" sem alocação de receita por produto (os dados brutos não trazem receita
por item — ver limitação no quality report, isso impede uma análise de produto baseada em
receita por item sem suposição adicional).

---

## 3. PBI_targets.xlsx (sheet `Sheet1`)

Grão: uma meta mensal de receita por `user_id` (8 linhas = 8 usuários, 1 meta cada —
não há dimensão de mês nesta tabela, apenas um valor único "monthly revenue target" por
usuário).

| Coluna | Tipo | % nulos | Cardinalidade | Observações |
|---|---|---|---|---|
| user_id | int64 | 0% | 8 únicos (= nº de linhas) | FK/PK — bate 1:1 com `users.user_id`, sem órfãos em nenhuma direção. |
| category | string | 0% | 3: `bar`, `restaurant`, `shop` | Idêntica a `users.category` para o mesmo user_id em 100% dos casos (0 mismatches). |
| city | string | 0% | 3: `Rio de Janeiro`, `São Paulo`, `Campinas` | **Diverge de `users.city` em 3 de 8 linhas** — ver quality report (inconsistência de grafia, não de dado: "SP" vs "São Paulo", "RJ" vs "Rio de Janeiro"). |
| monthly revenue target | int64 | 0% | 8 valores únicos | Min 50, max 150000 — dispersão grande entre os 8 usuários (desvio padrão 54663 vs média 30194). Unidade monetária não especificada no PDF nem nos dados (assumir mesma moeda de `orders.revenue`, não confirmado). |

Interpretação de negócio: tabela de metas por cliente/estabelecimento (`user_id` representa um
ponto de venda — bar, restaurante ou loja — não um "usuário final"). Candidata a dimensão
auxiliar ou tabela de metas ligada a `dim_customer`.

---

## 4. PBI_users.xlsx (sheet `Sheet1`)

Grão: um cliente/estabelecimento por linha (dimensão de cliente).

| Coluna | Tipo | % nulos | Cardinalidade | Observações |
|---|---|---|---|---|
| user_id | int64 | 0% | 8 únicos | PK. Os mesmos 8 valores aparecem em `orders.user_id` e `targets.user_id` — cobertura completa nos dois sentidos. |
| category | string | 0% | 3: `bar`, `restaurant`, `shop` | Tipo de estabelecimento do cliente (não é a mesma dimensão que `items.category`, que é tipo de bebida — cuidado para não confundir as duas colunas "category" no modelo). |
| city | string | 12.5% (1 linha, user_id 83095742) | 5 valores brutos: `Campinas`, `São Paulo`, `Rio de Janeiro`, `SP`, `RJ` — **na prática apenas 3 cidades distintas** (São Paulo e Rio de Janeiro grafados de duas formas cada). 1 nulo. | Precisa de padronização antes de uso em dashboard/filtro (ver quality report). |

Interpretação de negócio: dimensão de cliente (`dim_customer`), com apenas 8 clientes no
dataset inteiro — volume muito baixo, relevante para qualquer leitura estatística (ver
limitações).

---

## Relação entre as 4 tabelas (chaves de join observadas)

```
dim_product (PBI_items: item_id, category)
      |
      | item_id = product_id
      v
fact_orders (PBI_orders: order_id, order_date, user_id, product_id, revenue)
      ^
      | user_id = user_id
      |
dim_customer (PBI_users: user_id, category, city) ---- user_id = user_id ---- targets (PBI_targets: user_id, category, city, monthly revenue target)
```

- `orders.product_id` → `items.item_id`: 100% dos product_id de orders existem em items (0 órfãos).
- `orders.user_id` → `users.user_id`: 100% de cobertura nos dois sentidos (os 8 user_id de orders = os 8 de users = os 8 de targets).
- `targets.user_id` → `users.user_id`: 1:1 completo, sem órfãos.
- Não há uma tabela de datas (`dim_date`) nos arquivos brutos — precisará ser criada no Power Query a partir de `order_date`.
