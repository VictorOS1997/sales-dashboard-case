# Dashboard Blueprint — bi-case-pbi

Nível de especificação para o Dashboard Designer: estrutura de páginas, propósito, KPIs/visuais
por página e requisitos de interatividade do case mapeados a páginas específicas. Arte-final,
paleta e grid ficam a cargo do Designer (ver `visual_specification.md` para o nível seguinte de
detalhe de cada visual).

## Páginas

### Página 1 — Executive Overview
**Pergunta que responde**: "Como estamos indo, no geral, contra a meta?"
- Cartões de KPI: Total Revenue (KPI 1), Average Ticket (KPI 2), nº de pedidos, Revenue vs
  Target agregado (KPI 6).
- Mini-gráfico de tendência mensal de receita (sparkline ou linha compacta) com novembro
  sinalizado como parcial.
- Aviso fixo discreto no rodapé: "Receita calculada por pedido único (order_id); período
  jan–nov/2024, novembro parcial até dia 10."

### Página 2 — Time Analysis
**Pergunta que responde**: "A receita está crescendo, caindo ou estável mês a mês?"
- Gráfico de receita mensal (KPI 1 por mês) com novembro marcado visualmente (cor/padrão
  diferente ou anotação "parcial").
- Gráfico/cartão de MoM growth % (KPI 3) por mês, janeiro sem valor (N.A., sem mês anterior).
- YTD revenue (KPI 4) como cartão ou linha acumulada.
- **Requisito de interatividade #1 do case** (dois gráficos que se sobrepõem e alternam por
  tipo selecionado): implementado aqui — alternância entre "Receita mensal" (linha) e "Nº de
  pedidos mensal" (coluna), mesmo eixo temporal, controlado por um seletor de tipo de gráfico.

### Página 3 — Product Analysis
**Pergunta que responde**: "O que estamos vendendo mais (em volume de pedidos)?"
- Top 5 Products (KPI 5) — **critério fechado, sem pendência**: ranking por frequência em
  pedidos (`COUNT(DISTINCT order_id)` por produto). Não é por receita, e essa decisão não está
  mais em aberto — ver `kpi_catalog.md` seção 5 para a evidência do teste de rateio que a
  confirma.
- Participação por categoria de bebida (KPI 7) — rotulado "linhas de pedido por categoria", não
  "receita por categoria".
- Indicador secundário: produtos cadastrados nunca vendidos no período (138 de 314) — contexto
  de catálogo, não de receita.
- Aviso fixo (rodapé, não removível por filtro — ver texto literal em
  `visual_specification.md` seção "Disclaimer fixo — Product Analysis"): explica que receita por
  produto não é rastreável nos dados brutos e por isso o ranking usa frequência em pedidos.

### Página 4 — Customer Analysis
**Pergunta que responde**: "Quem são nossos clientes e como performam vs meta?"
- Receita por cliente (KPI 1 por user_id) vs meta individual (KPI 6).
- Receita por categoria de estabelecimento (bar/restaurant/shop).
- Receita por cidade (São Paulo/Rio de Janeiro/Campinas, após De-Para).
- **Requisito de interatividade #2 do case** (toggle absoluto/percentual em um único gráfico):
  implementado aqui — gráfico de receita por cliente alternando entre R$ absoluto e % de
  participação no total.
- Aviso fixo e proeminente (não rodapé pequeno — esta página precisa de destaque maior dado o
  risco de má leitura): "Base de apenas 8 clientes — resultados não são estatisticamente
  representativos de um universo maior de clientes."

### Página 5 — Conclusion (aba oculta)
**Requisito do case**: "Create a textual analysis in a hidden tab with key insights."
- Síntese textual (não visual) com:
  1. Principais achados de negócio (ex.: maior/menor mês de receita, cliente(s) acima/abaixo da
     meta, categoria de produto dominante em volume).
  2. Bloco "Limitações e decisões metodológicas" — replicando de forma executiva os pontos de
     `business_context.md` seção 6 (grão de revenue, Top 5 por frequência, novembro parcial,
     base de 8 clientes, revenue=0). O achado #5 (categoria nula) foi resolvido no ETL e não
     entra mais como limitação (ver `data_quality_report.md`, changelog, commit bb142b6).
  3. Não incluir nenhum número que não esteja também disponível/rastreável nas páginas
     anteriores — esta aba resume, não introduz dado novo.
- Página deve ficar oculta na navegação padrão, acessível via botão/link discreto (ex. "Ver
  notas metodológicas"), conforme pedido explícito do PDF.

## Filtros globais (todas as páginas, exceto Conclusion)
- Período (date range / slicer de mês-ano), com novembro visualmente identificado como parcial
  em qualquer seletor.
- Cliente (user_id / nome do estabelecimento).
- Cidade (3 cidades canônicas pós De-Para + "Não informado").
- Categoria de estabelecimento (bar/restaurant/shop).

## Dependências e ordem de implementação sugerida
1. DAX Engineer implementa o tratamento de grão de `orders` (DISTINCT por order_id) e dedupe de
   `items` antes de qualquer medida — pré-requisito de todas as páginas.
2. De-Para de cidade implementado no Power Query antes da página Customer Analysis.
3. Flag de "mês parcial" (coluna calculada ou medida) implementada antes da página Time
   Analysis e de qualquer cartão de YTD/MoM no Executive Overview.

## Implementation status / as-built

Estado real do dashboard, verificado pelo usuário no Power BI Desktop. Não altera nenhuma
definição de KPI; os blocos acima permanecem como especificação.

- **p1 Executive Overview**: 4 cartões de KPI, 4 slicers, linha de tendência mensal com marcador
  de novembro parcial e medida de tooltip (Partial Month Note).
- **p2 Time Analysis**: alternância Receita/Pedidos linha <-> coluna (4 visuais empilhados +
  botões + bookmarks); YTD com título dinâmico (YTD Title); colunas de MoM com regra de 4 cores
  (parcial `#5C4A12`, acima da média `#6FA66B`, negativo `#8A867E`, demais ouro `#E5B611`).
- **p3 Product Analysis**: Top 5 por frequência de pedidos; linhas de pedido por categoria (beer
  1514, nab 122, liquor 11, soda 4; total 1651); KPI Unsold Products = 138 de 314; disclaimer fixo.
  Valores de referência do Top 5 sem filtro: 49121 (116), 71496 (62), 60146 (53), 80738 (50),
  93608 (45).
- **p4 Customer Analysis**: banner de n=8; receita por cliente com toggle R$ <-> % (bookmarks);
  Revenue vs Target em barras agrupadas (Total Revenue e Target in Period); receita por categoria
  de estabelecimento: restaurant 419.997,40 / bar 181.107,46 / shop 5.039,23; por cidade: Rio de
  Janeiro 413.043,71 / Campinas 152.162,79 / São Paulo 36.259,09 / Não informado 4.678,50.
- **p5 Conclusion**: oculta, 3 caixas de texto, escrita em inglês.
- **Medidas novas** (além do catálogo original): Partial Month Note, YTD Title, MoM Color,
  Revenue % of Total, Target in Period, Unsold Products — ver `kpi_catalog.md` seção 8.
- **Modelo**: dois relacionamentos extras adicionados para os slicers da p3 funcionarem:
  `dim_date[Date]` -> `fact_orders[order_date]` e `dim_customer[user_id]` ->
  `fact_orders[user_id]` (decisão registrada).
- **Achado #5 resolvido no ETL**: `dim_product` via Group By `item_id` + Max(`category`), 314
  linhas, todas com categoria; não há bucket "Categoria não informada" na prática nem limitação
  de "5 produtos sem categoria" (ver `data_quality_report.md`, changelog, commit bb142b6).
- **Idioma (as-built)**: backgrounds das páginas e a página 5 (Conclusion) estão em inglês; os textos dinâmicos gerados por medida (`Partial Month Note`, `YTD Title`) e os nomes de campo do modelo permanecem em português. Registrado como estado final entregue, sem padronização adicional.
