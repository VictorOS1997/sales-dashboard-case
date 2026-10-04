# EDA Report — bi-case-pbi

## 1. Contexto do case

Fonte: `docs/Power_BI_–_Activities_Data.pdf` (2 páginas). O documento define o case "Power BI –
Activities": construir um modelo estrela, tratar os dados no Power Query, criar medidas DAX
(Total Revenue, Average Ticket, MoM growth %, YTD revenue, Top 5 produtos + outras conforme
necessário), montar um dashboard com visão executiva, análise temporal, de produto e de
cliente, dois gráficos interativos que se alternam por tipo de visual, um gráfico com toggle
absoluto/percentual, e uma conclusão textual em aba oculta. O PDF **não descreve o schema dos
dados** nem o nome da empresa de forma explícita (assinado "ABI" na saudação) — todo o
entendimento de negócio abaixo vem exclusivamente da inspeção dos 4 arquivos brutos.

## 2. Método

Ambiente Windows sem Python funcional por padrão (`python3` não encontrado; `python` apontava
para o alias da Microsoft Store). `py` (Python 3.12.10) estava disponível mas sem pandas/
openpyxl/matplotlib instalados. Resolvido instalando as 3 libs via `py -m pip install` nesta
sessão (pandas 3.0.6, openpyxl 3.1.5, matplotlib 3.11.2). Com isso, todos os 4 arquivos `.xlsx`
foram lidos **por completo** (todas as linhas, todas as sheets — cada arquivo tem uma única
sheet de dados), sem nenhuma amostragem ou truncamento. Não houve necessidade de recorrer a
parsing manual do XML/zip interno do xlsx.

**Limitação de ferramenta a registrar**: a instalação de pacotes Python dependeu de acesso à
internet/PyPI dentro do ambiente de execução. Se o ambiente de outro agente não tiver esse
acesso, a mesma rota pode falhar — nesse caso, a alternativa seria parsing manual do XML do
xlsx (como feito anteriormente nesta sessão com um `.docx`), não testada aqui pois não foi
necessária.

## 3. O que os dados representam (grão e papel de cada tabela)

- **`PBI_users.xlsx`** — dimensão de cliente/estabelecimento. 8 linhas = 8 pontos de venda,
  cada um com uma categoria de negócio (`bar`, `restaurant`, `shop`) e uma cidade.
- **`PBI_targets.xlsx`** — meta de receita mensal por cliente (1 meta por `user_id`, sem
  dimensão de mês própria — é um valor único, não uma série temporal de metas).
- **`PBI_items.xlsx`** — dimensão de produto (bebidas), com categoria de tipo de bebida
  (`beer`, `nab`, `liquor`, `soda`).
- **`PBI_orders.xlsx`** — fato de pedidos. Grão real verificado: **uma linha por item dentro de
  um pedido** (não uma linha por pedido). `revenue` é um atributo do **pedido** (`order_id`),
  repetido em todas as suas linhas de item — este é o achado mais importante desta rodada de
  EDA (ver quality report, Achado #1).

## 4. Principais achados de qualidade (resumo — detalhe completo em `data_quality_report.md`)

1. **BLOCKER** — `revenue` está no grão do pedido, não do item. Somar a coluna direto por linha
   infla a receita total em ~8,9x (R$5.396.656,69 somando por linha vs R$606.144,09 somando
   corretamente 1 valor por `order_id`). Nenhuma medida de "receita por produto" pode ser
   calculada com exatidão a partir dos dados brutos — não há preço unitário nem rateio.
2. 9 linhas totalmente duplicadas em `orders`; 94 linhas totalmente duplicadas + 99 `item_id`
   redundantes (sem conflito de categoria) em `items`.
3. 40 linhas de `orders` com `revenue = 0` (2,4%), concentradas em 3 clientes, todos
   `category = restaurant`.
4. 5 linhas de `items` (de 413 linhas / 314 item_id) com `category` nula — `item_id` 9001,
   19045, 13105, 14684 e 51849 — mas todas pertencem a `item_id` duplicados cuja linha irmã
   tem `category` preenchida; nenhum produto está de fato sem categoria (ver Achado #5
   revisado em `data_quality_report.md`). `item_id 19045` tem vendas em `orders`.
   **Status: Resolvido no ETL** (Group By `item_id` + Max(`category`) → `dim_product` com 314
   linhas, todas com categoria real; verificado no Power BI).
5. `city` em `users`/`targets` tem grafia inconsistente (`SP` vs `São Paulo`, `RJ` vs
   `Rio de Janeiro`) e diverge entre as duas tabelas em 3 de 8 registros — mesma cidade, grafia
   diferente, não é um dado contraditório, mas precisa de padronização (De-Para) antes de
   servir de filtro/dimensão.
6. Cobertura temporal: 2024-01-02 a 2024-11-10, um único ano, novembro parcial (só 10 dias).
   Não é possível calcular YoY nem validar sazonalidade com segurança; MoM de novembro vai
   aparecer artificialmente baixo se não for sinalizado como mês incompleto.
7. Base de apenas 8 clientes — qualquer "análise de cliente" deve vir com ressalva de amostra
   pequena.

## 5. Relações entre tabelas (joins validados)

- `orders.product_id` → `items.item_id`: 100% dos 176 product_id de orders existem em items.
  138 dos 314 item_id de items nunca foram vendidos no período observado.
- `orders.user_id` ↔ `users.user_id` ↔ `targets.user_id`: cobertura 100% nos três sentidos —
  exatamente os mesmos 8 user_id aparecem nas três tabelas, sem órfãos.
- Não existe uma tabela de datas nos arquivos brutos; `dim_date` precisa ser construída no
  Power Query a partir de `orders.order_date` (range 2024-01-02 a 2024-11-10).

## 6. Figuras exploratórias

Geradas com matplotlib em `reports/figures/` (grão de receita já corrigido onde aplicável):

- `01_monthly_revenue_corrected_grain.png` — receita mensal somando 1 valor por `order_id`
  (grão correto); novembro/2024 destacado em vermelho por ser mês parcial.
- `02_orders_count_per_month.png` — número de pedidos distintos por mês.
- `03_revenue_by_customer_category.png` — receita total (grão correto) por categoria de
  cliente (bar/restaurant/shop).
- `04_order_lines_by_product_category.png` — contagem de linhas de pedido por categoria de
  produto (bebida). **Não é receita** — é apenas contagem de aparições, dado que não há receita
  por item (ver achado #1). Rotulado explicitamente no gráfico para evitar leitura incorreta.
- `05_order_revenue_distribution.png` — histograma da receita por pedido (n=356, grão
  correto), evidenciando a cauda de outliers de alto valor.

## 7. Perguntas em aberto para o Analytics Architect

- Como tratar "Top 5 produtos" dado que não há receita por item? Opções possíveis: contagem de
  aparições em pedidos, ou solicitar/assumir explicitamente uma regra de rateio igualitário de
  `revenue` do pedido entre seus itens (decisão de negócio, não de dado — precisa de validação
  humana antes de virar medida DAX).
- `revenue = 0`: tratar como pedido válido (desconto total/cortesia) ou excluir do denominador
  de Average Ticket? Não inferível dos dados.
- Moeda/unidade de `revenue` e `monthly revenue target` não especificada — assumir mesma
  unidade para as duas colunas (plausível, pois ambas em `targets`/`orders` referem-se aos
  mesmos `user_id` e ordens de grandeza são compatíveis) mas não confirmado por nenhuma fonte.
- Novembro/2024 parcial: como o dashboard deve sinalizar isso visualmente para não sugerir
  queda de receita?
