# Data Quality Report — bi-case-pbi

> **Changelog — 2026-10-02**: o Achado #5 foi reformulado. A redação original ("5 item_id sem
> categoria preenchida: 9001, 19045, 13105, 14684, 51849") estava tecnicamente imprecisa: os 5
> `item_id` citados pertencem ao grupo de duplicados já identificado no Achado #4, e em cada um
> deles a categoria **existe** — está preenchida na linha duplicada irmã, nula apenas na outra.
> A imprecisão foi descoberta durante a montagem do modelo no Power BI (pelo usuário), não é um
> erro do EDA original na extração/leitura dos dados (os números de nulos em si estavam
> corretos) — foi uma formulação imprecisa da conclusão de negócio sobre um dado que já estava
> corretamente extraído. Correção também propagada para `data_dictionary.md` (linha `category`)
> e verificada de forma independente antes da correção
> (`groupby('item_id')['category'].apply(lambda s: (s.isna().sum(), s.notna().sum()))` → `(1,1)`
> nos 5 casos).

Método: perfilagem programática com pandas 3.0.6 / openpyxl 3.1.5 sobre os 4 arquivos de
`data/raw/` (leitura completa, sem amostragem). Scripts de perfilagem foram executados nesta
sessão e removidos após a extração dos números abaixo (não fazem parte do entregável; os
números citados são reproduzíveis lendo os arquivos originais, que permanecem intocados em
`data/raw/`).

## Achado crítico #1 — `orders.revenue` está no grão do pedido, não do item (BLOCKER para medidas de produto)

**Evidência**: para os 356 `order_id` distintos de `PBI_orders.xlsx`, 0 (zero) apresentam mais
de um valor distinto de `revenue` entre suas linhas — ou seja, `revenue` é idêntico em todas as
linhas de um mesmo pedido, independentemente de quantos produtos (`product_id`) distintos o
pedido tenha (de 1 a 29 produtos por pedido, média 4.64).

**Método de cálculo**: `orders.groupby('order_id')['revenue'].nunique()` → máximo = 1 em todos
os 356 grupos.

**Impacto quantificado**:
- `SUM(revenue)` somando todas as 1660 linhas: **5.396.656,69**
- `SUM(revenue)` somando uma linha por `order_id` (deduplicado ao grão real do pedido):
  **606.144,09**
- Razão: a soma ingênua por linha **infla a receita total em ~8,9x**.

**Ressalva**: não há nos dados brutos nenhuma informação de preço unitário, quantidade ou
alocação de receita por produto dentro do pedido — portanto **não é possível** calcular
"receita por produto" de forma exata com os dados atuais; qualquer métrica de produto que
dependa de receita (ex. "Top 5 produtos por receita") precisa ser definida com o Analytics
Architect assumindo uma regra explícita (ex. contagem de aparições do produto em pedidos, não
receita atribuída) ou solicitando dado adicional. Não inferir rateio proporcional sem validação
de negócio.

**Severidade**: BLOCKER para qualquer medida de receita por produto. MAJOR para "Total Revenue"
genérico (a medida correta precisa agregar por `order_id` antes de somar, não por linha de
`fact_orders` diretamente).

---

## Achado #2 — `PBI_orders.xlsx` tem 9 linhas totalmente duplicadas

**Evidência**: `orders.duplicated().sum()` (todas as 5 colunas idênticas) = 9 de 1660 linhas.

**Impacto**: se não removidas, inflam contagem de linhas/itens e (indiretamente, via grão do
pedido) não afetam a soma de receita por `order_id` desde que o order_id dedupe primeiro — mas
afetam qualquer contagem de "itens por pedido" ou "produtos vendidos".

**Severidade**: MAJOR. Recomenda-se `DISTINCT`/remove duplicates no Power Query antes de
qualquer agregação.

---

## Achado #3 — `orders.revenue == 0` em 40 linhas (2.4% das linhas, correspondendo a pedidos reais)

**Evidência**: 40 linhas com `revenue == 0`, nenhuma negativa. Concentradas em 3 user_id
(33198146: 23 linhas; 10560208: 7; 37404863: 7) — todos de `category = restaurant`.
Distribuídas ao longo de 9 dos 11 meses observados, sem padrão sazonal óbvio.

**Ressalva**: não é possível afirmar se revenue=0 representa um pedido cancelado, cortesia,
erro de carga ou produto de brinde sem validação de negócio — registrar como limitação, não
assumir.

**Severidade**: MINOR/MAJOR dependendo da definição de negócio — impacta "Average Ticket" se
pedidos de receita zero forem contados no denominador de número de pedidos.

---

## Achado #4 — `PBI_items.xlsx`: `item_id` duplicado em 99 produtos (198 linhas), mas sem conflito de categoria

**Evidência**: 413 linhas, apenas 314 `item_id` únicos. Para os 99 `item_id` que se repetem,
0 apresentam categoria divergente entre as linhas duplicadas (checado via
`groupby('item_id')['category'].nunique() > 1` → 0 ocorrências). Além disso, 94 das 413 linhas
são duplicatas **completas** (todas as colunas idênticas).

**Impacto**: tabela de produtos precisa de deduplicação (`DISTINCT item_id, category`) antes de
virar dimensão — caso contrário, qualquer join/contagem de produtos infla artificialmente.

**Severidade**: MAJOR (estrutural, mas de correção simples e sem ambiguidade de negócio já que
não há conflito de valores).

---

## Achado #5 — `PBI_items.xlsx`: 5 `item_id` (do grupo de duplicados do Achado #4) têm `category` nula em UMA das duas linhas duplicadas, mas preenchida na outra

**Evidência**: dos 5 `item_id` com alguma linha de `category` nula (9001, 19045, 13105, 14684,
51849), nenhum é "sem categoria" de fato — todos pertencem ao grupo de 99 `item_id` duplicados do
Achado #4 e, em cada um, exatamente uma das duas linhas tem `category` nula e a outra tem a
categoria preenchida (confirmado via
`df[df.item_id.isin(ids)].groupby('item_id')['category'].apply(lambda s: (s.isna().sum(), s.notna().sum()))`
→ `(1, 1)` nos 5 casos):

| item_id | linha com categoria nula (index) | linha com categoria preenchida (index) | categoria disponível |
|---|---|---|---|
| 9001   | 51  | 365 | nab   |
| 19045  | 372 | 58  | beer  |
| 13105  | 385 | 71  | beer  |
| 14684  | 398 | 84  | beer  |
| 51849  | 411 | 97  | nab   |

**Ressalva de implementação (crítica)**: como a categoria *existe* na linha duplicada irmã, um
`Remove Duplicates` simples no Power Query (que mantém a primeira linha encontrada, de forma
arbitrária) pode reter justamente a linha com `category` nula — por exemplo, para `item_id 9001`
a primeira ocorrência (index 51) é a que está nula. O resultado seria um bucket "(em branco)"
evitável em qualquer análise por categoria, mesmo havendo dado correto disponível na própria
tabela. **Ação recomendada**: ao deduplicar `dim_product`, usar uma agregação que prefira
explicitamente o valor não nulo de `category` por `item_id` — ex. `Table.Group` com
`List.RemoveNulls(...){0}` ou `List.Max`/`List.First` sobre a lista sem nulos — em vez de um
`Remove Duplicates` ingênuo sobre a coluna `item_id`.

**Severidade**: MINOR — não há produto realmente sem categoria conhecida nos dados brutos; o risco
é inteiramente de implementação (deduplicação ingênua descartando o valor correto). Se a
deduplicação for feita com a regra acima, este achado não gera impacto algum no modelo final.

---

## Achado #6 — `PBI_users.xlsx`: `city` com grafias inconsistentes e 1 nulo

**Evidência**: valores brutos observados: `São Paulo`, `SP`, `Rio de Janeiro`, `RJ`, `Campinas`
— ou seja, 5 valores textuais distintos representam apenas 3 cidades reais. 1 de 8 linhas
(user_id 83095742) tem `city` nulo.

**Comparação com `PBI_targets.xlsx`**: a mesma inconsistência aparece — e **diverge** da
grafia usada em `users` para 3 dos 8 user_id (`targets` usa consistentemente a forma longa
`São Paulo`/`Rio de Janeiro`, `users` mistura as duas formas). `category` não diverge entre as
duas tabelas (0 mismatches em 8 comparações).

**Severidade**: MAJOR para qualquer segmentação geográfica (precisa de padronização /
De-Para no Power Query antes de usar `city` como dimensão ou filtro) — mas de correção simples
dado o volume baixo (8 clientes).

---

## Achado #7 — Cobertura temporal incompleta e volume mensal muito desigual

**Evidência**: `order_date` cobre 2024-01-02 a 2024-11-10 (sem dezembro/2024, sem nenhum outro
ano). Contagem de linhas por mês varia de 46 (novembro, mês parcial — só 10 dias) a 278
(janeiro); receita mensal (ingênua, por linha — ver Achado #1 para o viés de escala) varia de
R$49.789,75 (junho) a R$1.917.678,21 (maio), uma razão de ~38x entre o mês mais baixo e o mais
alto.

**Ressalva**: novembro está incompleto (só até dia 10) — qualquer comparação MoM ou YTD que
inclua novembro/2024 precisa sinalizar que o mês é parcial, não comparável diretamente a meses
fechados. Não há dado de 2023 para comparação ano a ano nem indício de sazonalidade validável
com apenas 11 meses de 1 ano.

**Severidade**: MAJOR — risco real de o dashboard sugerir "queda" ou "crescimento" em
novembro que na verdade é efeito de mês incompleto, não de tendência real.

---

## Achado #8 — Volume de clientes extremamente baixo (n=8)

**Evidência**: `PBI_users.xlsx` e `PBI_targets.xlsx` têm exatamente 8 `user_id`, e são
exatamente os mesmos 8 que aparecem em `orders.user_id` (cobertura 100% nos dois sentidos, sem
órfãos).

**Ressalva**: qualquer "análise de cliente" no dashboard (requisito do PDF) estará operando
sobre uma base de 8 pontos — médias, desvios-padrão e segmentações por `category`/`city` têm
significância estatística limitada. Reportar como limitação explícita na conclusão do
dashboard, não apresentar como amostra representativa de um universo maior sem ressalva.

**Severidade**: informativo/estrutural — não é um "erro" dos dados, mas limita o tipo de
afirmação que pode ser feita (ex.: evitar extrapolações causais).

---

## Resumo de severidade

| Achado | Severidade | Bloqueia |
|---|---|---|
| #1 revenue no grão do pedido | BLOCKER | Medidas de receita por produto |
| #2 orders duplicados (9 linhas) | MAJOR | Contagem de itens/pedidos |
| #3 revenue = 0 (40 linhas) | MAJOR/MINOR | Average Ticket, definição de "pedido válido" |
| #4 item_id duplicado (99 produtos) | MAJOR | Dimensão de produto |
| #5 category nula em items (5 linhas) | MINOR/MAJOR | Análise por categoria de produto |
| #6 city inconsistente em users/targets | MAJOR | Segmentação geográfica |
| #7 cobertura temporal incompleta (nov parcial, 1 ano só) | MAJOR | MoM, YTD, sazonalidade |
| #8 base de 8 clientes | Estrutural | Significância de "análise de cliente" |

Nenhum destes achados foi corrigido nos dados brutos — `data/raw/` permanece intocado, conforme
regra do projeto. Correções (deduplicação, De-Para de cidade, agregação correta de revenue)
devem ser implementadas no Power Query pelo DAX & Power BI Engineer, a partir da direção
definida pelo Analytics Architect.
