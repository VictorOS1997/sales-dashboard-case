# Business Context — bi-case-pbi

## 1. Origem e natureza do case

Fonte única de requisito: `docs/Power_BI_–_Activities_Data.pdf` ("Power BI – Activities"),
assinado "ABI" na saudação. O documento é um case técnico de visualização de dados — avalia
modelagem dimensional, Power Query, DAX e construção de dashboard. **Não descreve o schema dos
dados nem confirma a identidade da empresa** — "ABI" não deve ser tratado como confirmado
(Anheuser-Busch InBev é uma inferência plausível, não um fato validado pelo documento).

## 2. Requisitos explícitos do PDF (verbatim, traduzidos)

1. **Modelagem de dados** — Star Schema.
2. **Transformação (Power Query)** — explorar os dados e fazer os ajustes necessários.
3. **Medidas DAX obrigatórias**:
   - Total Revenue
   - Average Ticket
   - Month-over-month growth (%)
   - Year-to-date revenue
   - Top 5 products
   - Outras conforme necessário
4. **Dashboard**:
   - Desenvolvimento: visão executiva com KPIs-chave; análise temporal (mês/ano); análise de
     produto; análise de cliente.
   - Interatividade: (a) dois gráficos diferentes que se sobrepõem e alternam conforme o tipo
     de gráfico selecionado; (b) um único gráfico com toggle entre valores absolutos e
     percentuais.
5. **Conclusão** — análise textual em aba oculta com principais insights.

Os exemplos visuais do PDF (word cloud + gráfico de barras alternando; dashboard de
"task completion/effectiveness" com toggle mês/semana/dia e percentual/total) são de **outro
domínio de negócio** (pesquisa/produtividade) — servem apenas como referência de padrão de
interação exigido, não como modelo de conteúdo a replicar literalmente. Esse ponto é
registrado aqui para o Dashboard Designer não confundir o mock de exemplo com o dataset real
(vendas/clientes/produtos).

## 3. O que os dados realmente são (fonte: EDA, não o PDF)

O PDF não descreve o schema. Toda a leitura de negócio abaixo vem de
`docs/discovery/data_dictionary.md` e `eda_report.md`:

- **Negócio**: operação de vendas de bebidas (cerveja, nab, destilados, refrigerante) para
  estabelecimentos clientes (bar, restaurante, loja), em 3 cidades (São Paulo, Rio de Janeiro,
  Campinas), com meta mensal de receita por cliente.
- **4 tabelas brutas**: `PBI_users` (8 clientes), `PBI_targets` (1 meta por cliente),
  `PBI_items` (314 produtos únicos), `PBI_orders` (356 pedidos únicos, 1660 linhas de item de
  pedido).
- **Período coberto**: 2024-01-02 a 2024-11-10 — um único ano, novembro incompleto (10 dias).

## 4. Problema central do case

Traduzir uma base pequena e com problemas reais de grão/qualidade em um dashboard executivo
que (a) meça receita corretamente, (b) explique vendas por tempo, produto e cliente, e
(c) seja auditável — cada número rastreável à sua fórmula e evidência. O desafio central não é
volume de dado, é **rigor de grão**: a cilada deliberada do dataset é a coluna `revenue` estar
no grão do pedido, não do item, e um analista descuidado que some a coluna direto por linha
reporta um Total Revenue quase 9x maior que o real.

## 5. Público-alvo do dashboard

Inferido do pedido ("visão executiva", "análise de cliente", "aba de conclusão com insights"):
público executivo/comercial que acompanha receita, metas, mix de produto e desempenho por
cliente — não um público técnico. Linguagem e KPIs devem ser diretos, sem jargão estatístico,
mas com as limitações estruturais (8 clientes, 1 ano, revenue não alocável por produto)
expostas de forma honesta na aba de conclusão.

## 6. Decisões de enquadramento tomadas aqui (Analytics Architect)

Ver `kpi_catalog.md` para o detalhe formal; resumo das decisões de maior impacto:

- **Total Revenue / todas as medidas de receita**: SEMPRE agregadas a partir de 1 linha por
  `order_id` (receita do pedido), nunca por soma direta das 1660 linhas de `fact_orders`. Esta
  é a decisão mais importante do handoff e é tratada como regra obrigatória, não como opção.
- **Top 5 produtos**: não computável por receita exata (sem preço unitário/rateio nos dados
  brutos). Redefinido como "Top 5 produtos por número de pedidos distintos em que aparecem"
  (frequência de presença em pedidos), com a limitação declarada em toda visualização que o
  exiba. Rateio proporcional de receita do pedido entre itens foi **descartado** como opção
  default por ser uma suposição de negócio não validada — fica registrado como alternativa
  possível somente mediante validação humana explícita (não implementada neste handoff).
- **orders duplicados (9 linhas) e items duplicados (99 item_id / 94 linhas completas)**:
  removidos via DISTINCT no Power Query antes de qualquer agregação — tratado como correção
  técnica, não como decisão de negócio.
- **revenue = 0 (40 linhas, 3 clientes restaurant)**: mantidos como pedidos válidos (não há
  evidência de erro de carga) mas excluídos do denominador de contagem de pedidos usado no
  Average Ticket é avaliado como opção alternativa — ver `kpi_catalog.md` Average Ticket para a
  definição final e a razão da escolha.
- **Cidade (De-Para)**: padronizada para 3 valores canônicos (São Paulo, Rio de Janeiro,
  Campinas) a partir das 5 grafias brutas; 1 cliente com cidade nula é mantido com rótulo
  explícito "Não informado", não descartado.
- **Novembro/2024 parcial**: qualquer KPI de MoM/YTD que toque novembro deve exibir um
  indicador visual de "mês parcial (até dia 10)" — ver `dashboard_blueprint.md` e
  `visual_specification.md`. Não comparar novembro a outros meses fechados sem esse aviso.
- **Base de 8 clientes**: toda a página "Customer Analysis" carrega um aviso fixo de amostra
  pequena; não se apresentam médias/segmentações como estatisticamente generalizáveis.
