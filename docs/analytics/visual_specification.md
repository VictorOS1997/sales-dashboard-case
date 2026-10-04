# Visual Specification — bi-case-pbi

Especificação por visual (nível: o que mostrar, como rotular, hierarquia e cor funcional — não
arte-final). Dashboard Designer converte isto em layout/pixel; DAX Engineer converte os
"campos" em medidas.

Convenção de cor funcional (não paleta final): usar 1 cor de destaque para "dado real/fechado"
e 1 cor de alerta (ex. cinza-hachurado ou tom secundário, nunca vermelho de "erro") para
"dado parcial/incompleto" (novembro) — nunca usar vermelho para novembro, pois não representa
erro ou queda, representa incompletude.

---

## Executive Overview

| Visual | Tipo | Campos | Título | Observação |
|---|---|---|---|---|
| Total Revenue | Cartão KPI | KPI 1 | "Receita Total (Jan–Nov/2024)" | Subtítulo pequeno: "grão: 1 valor por pedido" |
| Average Ticket | Cartão KPI | KPI 2 | "Ticket Médio" | — |
| Nº de Pedidos | Cartão KPI | COUNT DISTINCT order_id | "Pedidos no Período" | — |
| Revenue vs Target | Cartão KPI + barra de progresso | KPI 6 | "Receita vs Meta (agregado)" | Meta tratada como constante mensal, nota de rodapé |
| Tendência mensal | Linha compacta | KPI 1 por mês | "Tendência de Receita" | Último ponto (novembro) com marcador visual distinto + tooltip "mês parcial" |

---

## Time Analysis

| Visual | Tipo | Campos | Título | Observação |
|---|---|---|---|---|
| Receita mensal / Pedidos mensais (alternável) | Linha ↔ Coluna, controlado por seletor de tipo | KPI 1 por mês / COUNT order_id por mês | "Receita Mensal" / "Pedidos por Mês" | **Requisito de interatividade #1**: os dois gráficos ocupam o mesmo espaço e alternam por seleção do usuário; novembro sempre com marcador de parcial em ambos |
| MoM Growth % | Coluna (waterfall opcional) | KPI 3 | "Crescimento Mês a Mês (%)" | Janeiro sem barra/N.A.; novembro com rótulo "parcial" sobreposto |
| YTD Revenue | Linha acumulada ou cartão | KPI 4 | "Receita Acumulada no Ano (YTD)" | Rótulo dinâmico "YTD até [última data], mês corrente parcial" quando aplicável |

---

## Product Analysis

| Visual | Tipo | Campos | Título | Observação |
|---|---|---|---|---|
| Top 5 Produtos | Barra horizontal | KPI 5 | "Top 5 Produtos por Nº de Pedidos" | **Critério fechado (não mais "em definição")**: frequência em pedidos. Subtítulo obrigatório: "frequência em pedidos — não representa receita" |
| Participação por categoria | Pizza/donut ou barra 100% | KPI 7 | "Linhas de Pedido por Categoria de Bebida" | Achado #5 resolvido no ETL (4 categorias reais; "Categoria não informada" apenas fallback defensivo, hoje = 0 e não aparece); nunca formatar como moeda |
| Produtos nunca vendidos | Cartão KPI | COUNT item_id não presentes em orders | "Produtos no Catálogo sem Venda no Período" | 138/314 — contexto, não alarme |
| Disclaimer fixo da página | Banner de texto fixo, não removível por filtro (mesmo padrão do banner de n=8 em Customer Analysis) | — | — | Ver texto literal abaixo, em "Disclaimer fixo — Product Analysis". Posicionado em área fixa (rodapé ou topo da página, a critério do Design), sempre visível independente de filtro aplicado. |

---

### Disclaimer fixo — Product Analysis

**Status: fechado — pronto para implementação literal pelo Design.**

Texto final (copiar literalmente para o banner fixo da página):

> "Este ranking mostra os produtos que aparecem no maior número de pedidos — não os que geram
> mais receita. Os dados de origem registram apenas o valor total de cada pedido, não o preço de
> cada item, então não é possível calcular receita por produto individual. Testamos dividir a
> receita igualmente entre os itens do pedido como alternativa, mas o resultado foi inconsistente
> (preços implícitos variando até 350x para o mesmo produto) e foi descartado. Por isso, o
> critério oficial do Top 5 é frequência em pedidos."

Regras de exibição:
- Área fixa, não removível/ocultável por filtro (mesmo tratamento do banner de amostra pequena
  da página Customer Analysis).
- Nunca abreviar a ponto de remover a frase "não os que geram mais receita" — é o ponto central
  que evita leitura equivocada do ranking por um executivo apressado.
- Não usar tom de pedido de desculpas; é uma nota metodológica, não um erro do dashboard.

---

## Customer Analysis

| Visual | Tipo | Campos | Título | Observação |
|---|---|---|---|---|
| Receita por cliente (R$ ↔ %) | Barra, toggle absoluto/percentual | KPI 1 por user_id | "Receita por Cliente" | **Requisito de interatividade #2**: toggle explícito "Valores absolutos" / "% do total" |
| Receita vs Meta por cliente | Barra agrupada ou bullet chart | KPI 1 + KPI 6 | "Receita Realizada vs Meta" | — |
| Receita por categoria de estabelecimento | Barra | KPI 1 agrupado por users.category | "Receita por Tipo de Estabelecimento" | — |
| Receita por cidade | Mapa ou barra | KPI 1 agrupado por cidade (De-Para) | "Receita por Cidade" | 3 valores canônicos apenas; cliente sem cidade informada em bucket "Não informado" |
| Aviso de amostra pequena | Banner de texto fixo, não removível por filtro | — | "Base de 8 clientes — leitura não generalizável" | Posicionado no topo da página, não no rodapé |

---

## Conclusion (aba oculta)

- Bloco de texto estruturado (não visual gráfico), com headings:
  1. "O que os números mostram" (insights)
  2. "Como a receita foi calculada" (nota metodológica do grão de pedido)
  3. "Limitações dos dados" (lista das 8 ressalvas do EDA, linguagem executiva)
- Sem gráficos novos — qualquer número citado deve linkar/referenciar a página onde aparece.

---

## Regras de rótulo transversais (aplicam a todas as páginas)

1. Nenhum visual de "frequência em pedidos" (Top 5 Products, categoria de produto) pode usar
   formatação de moeda (R$) ou o termo "receita" no título.
2. Todo visual que inclua novembro/2024 em uma série temporal precisa de indicador visual de
   mês parcial — não é opcional, é regra de integridade de leitura.
3. Toda página de Customer Analysis carrega o aviso de n=8 de forma permanente e visível.
4. Cores: evitar vermelho/verde semânticos de "bom/ruim" em cima de dados ainda não validados
   contra meta real (ex. revenue=0) — usar neutro até confirmação de negócio.
