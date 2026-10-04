# Analytical Storyline — bi-case-pbi

## Árvore de perguntas de negócio

```
Como está a performance de vendas da operação e o que explica o resultado?
│
├── 1. VISÃO EXECUTIVA — "Como estamos indo, no geral, contra a meta?"
│   ├── 1.1 Qual a receita total do período (grão correto)?
│   ├── 1.2 Qual o ticket médio por pedido?
│   ├── 1.3 Quantos pedidos foram feitos?
│   └── 1.4 Estamos batendo a meta mensal agregada dos clientes?
│
├── 2. ANÁLISE TEMPORAL — "A receita está crescendo, caindo, ou estável mês a mês?"
│   ├── 2.1 Como a receita evolui mês a mês (Jan–Nov/2024)?
│   ├── 2.2 Qual o crescimento percentual mês sobre mês (MoM)?
│   ├── 2.3 Qual a receita acumulada no ano (YTD)?
│   └── 2.4 Novembro é uma queda real ou um artefato de mês incompleto? [resposta: artefato —
│       novembro só tem 10 dias de dados; deve ser sinalizado, não interpretado como tendência]
│
├── 3. ANÁLISE DE PRODUTO — "O que estamos vendendo mais?"
│   ├── 3.1 Quais produtos aparecem com mais frequência nos pedidos (proxy de popularidade)?
│   │   [NÃO é "quais produtos geram mais receita" — essa pergunta não é respondível com
│   │   exatidão nos dados brutos; ver limitação formal]
│   ├── 3.2 Qual a participação de cada categoria de bebida (beer/nab/liquor/soda) no volume
│   │   de linhas de pedido?
│   └── 3.3 Há produtos cadastrados que nunca venderam no período? (138 de 314 — relevante para
│       gestão de catálogo, não para receita)
│
└── 4. ANÁLISE DE CLIENTE — "Quem são nossos clientes e como cada um performa vs meta?"
    ├── 4.1 Qual a receita por cliente (grão correto) e como se compara à meta individual?
    ├── 4.2 Como a receita se distribui por categoria de estabelecimento (bar/restaurant/shop)?
    ├── 4.3 Como a receita se distribui por cidade (São Paulo/Rio de Janeiro/Campinas)?
    └── 4.4 [limitação permanente] Qualquer leitura acima opera sobre apenas 8 clientes —
        não deve ser lida como representativa de um universo maior.
```

## Storyline (arco narrativo do dashboard)

### Abertura — "Onde estamos?"
Página Executiva. Resposta imediata, sem necessidade de interação: receita total do período
(grão correto), ticket médio, nº de pedidos, e meta agregada vs realizado. Define o
vocabulário numérico que o resto do dashboard vai detalhar. Esta página é a âncora de
confiança — se o número aqui estiver certo (R$606.144,09, não R$5,4M), o resto do dashboard
herda credibilidade.

### Desenvolvimento — "Por que esse número, decomposto em três eixos"
1. **Tempo** (página Time Analysis): a receita não é uniforme — varia por mês, com novembro
   claramente sinalizado como incompleto. Mostra tendência real sem o ruído do mês parcial.
2. **Produto** (página Product Analysis): o que compõe o volume de pedidos — por categoria e
   por frequência de produto — com a ressalva explícita de que isso é proxy de popularidade,
   não de receita gerada por item.
3. **Cliente** (página Customer Analysis): quem compra, quanto, e como isso se compara à meta
   individual — por cliente, categoria de estabelecimento e cidade, com o aviso de amostra
   pequena (n=8) sempre visível.

### Interatividade exigida pelo case, encaixada na narrativa
- **Dois gráficos sobrepostos que alternam por tipo** (requisito 4-Interactivity, item 1): na
  página Time Analysis, alternando entre "Receita mensal" (linha) e "Nº de pedidos mensal"
  (coluna) — dois ângulos da mesma pergunta temporal, não dois assuntos distintos.
- **Toggle absoluto/percentual** (requisito 4-Interactivity, item 2): na página Customer
  Analysis, alternando "Receita por cliente (R$)" e "Participação % de cada cliente na receita
  total" — mesma pergunta (quem contribui mais), duas lentes.

### Fechamento — "O que isso significa e o que não podemos afirmar"
Aba oculta de Conclusão (requisito 5): síntese textual dos achados + bloco de limitações
explícitas (grão de revenue corrigido, Top 5 por frequência não por receita, novembro parcial,
base de 8 clientes, 40 linhas de revenue=0; o achado #5 de categoria nula foi resolvido no ETL e não é mais limitação — ver `data_quality_report.md`, changelog 2026-10-02, commit bb142b6). Fecha o arco respondendo
"o que aprendemos" e sendo transparente sobre "o que os dados não permitem concluir" — coerente
com o princípio do projeto de não forçar conclusão sem sustentação.

## Associação vs correlação vs causalidade

- Qualquer leitura de "categoria X vende mais que categoria Y" é **associação observacional**
  dentro do período e amostra disponíveis — não se infere causa (ex.: não dizer "clientes do
  Rio compram mais porque são do Rio"; a cidade pode estar confundida com o tipo de
  estabelecimento ou com o próprio cliente individual, dado n=8).
- Variação mês a mês não deve ser lida como tendência causal (sazonalidade, campanhas, etc.)
  sem dado adicional — o dataset cobre só 11 meses de 1 ano, sem comparação YoY possível.
- "Produto mais frequente em pedidos" é associação de co-ocorrência (presença em pedidos), não
  evidência de que aquele produto é o maior gerador de receita — a pergunta de receita por
  produto permanece em aberto por falta de dado, não é respondida por proxy disfarçado de fato.
