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
     base de 8 clientes, 5 produtos sem categoria, revenue=0).
  3. Não incluir nenhum número que não esteja também disponível/rastreável nas páginas
     anteriores — esta aba resume, não introduz dado novo.
- Página deve ficar oculta na navegação padrão, acessível via botão/link discreto (ex. "Ver
  notas metodológicas"), conforme pedido explícito do PDF.

## Filtros globais (todas as páginas, exceto Conclusion)
- Período (date range / slicer de mês-ano), com novembro visualmente identificado como parcial
  em qualquer seletor.
- Cliente (user_id / nome do estabelecimento).
- Cidade (3 valores canônicos pós De-Para).
- Categoria de estabelecimento (bar/restaurant/shop).

## Dependências e ordem de implementação sugerida
1. DAX Engineer implementa o tratamento de grão de `orders` (DISTINCT por order_id) e dedupe de
   `items` antes de qualquer medida — pré-requisito de todas as páginas.
2. De-Para de cidade implementado no Power Query antes da página Customer Analysis.
3. Flag de "mês parcial" (coluna calculada ou medida) implementada antes da página Time
   Analysis e de qualquer cartão de YTD/MoM no Executive Overview.
