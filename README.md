# bi-case-pbi — Case de BI: dashboard de vendas de bebidas (Power BI)

Case técnico de Data Analyst / BI resolvido por um sistema multiagente. O entregável final é um
dashboard em Power BI; este repositório contém **tudo o que antecede e especifica esse dashboard**:
EDA completo, catálogo de KPIs com evidência, modelo semântico, medidas DAX, background visual,
tema e auditoria independente.

Documento consolidado do projeto (12 páginas, visão de Product Data Management):
**[`docs/review/project_documentation.pdf`](docs/review/project_documentation.pdf)**.

---

## 1. O que é o projeto

O requisito vem de um único documento: `docs/Power_BI_–_Activities_Data.pdf` ("Power BI –
Activities", assinado "ABI"). Ele pede um modelo em star schema, tratamento no Power Query, um
conjunto de medidas DAX (Total Revenue, Average Ticket, MoM growth %, YTD revenue, Top 5 products e
"outras conforme necessário"), um dashboard com visão executiva + análises temporal, de produto e de
cliente, dois requisitos específicos de interatividade e uma conclusão textual em aba oculta. A
transcrição verbatim dos requisitos está em `docs/analytics/business_context.md` seção 2.

O PDF **não descreve o schema dos dados nem confirma a empresa** — "ABI" (Anheuser-Busch InBev) é
inferência plausível, não fato validado, e o projeto trata isso como inferência em todos os
artefatos. Todo o entendimento de negócio foi reconstruído a partir da inspeção dos 4 arquivos
brutos: operação de vendas de bebidas (beer, nab, liquor, soda) para 8 estabelecimentos clientes
(bar, restaurant, shop) em 3 cidades (São Paulo, Rio de Janeiro, Campinas), com meta mensal de
receita por cliente, no período 2024-01-02 a 2024-11-10.

## 2. Como os dados estão organizados

Quatro planilhas em `data/raw/` (somente leitura, nunca modificadas):

| Arquivo | Papel | Grão verificado | Volume |
|---|---|---|---|
| `PBI_orders.xlsx` | Fato de pedidos | uma linha por **item dentro de um pedido** | 1.660 linhas / 356 pedidos / 176 produtos / 8 clientes |
| `PBI_items.xlsx` | Dimensão de produto | um produto por linha, `item_id` **não** único | 413 linhas / 314 `item_id` / 4 categorias |
| `PBI_users.xlsx` | Dimensão de cliente | um estabelecimento por linha | 8 linhas / 3 categorias |
| `PBI_targets.xlsx` | Meta de receita | uma meta por cliente, **sem dimensão de mês** | 8 linhas |

### A limitação principal: o grão de `revenue`

`orders.revenue` está no grão do **pedido**, repetido em cada linha de item do pedido — verificado:
0 de 356 `order_id` têm mais de um valor distinto de revenue entre suas linhas. Consequência:

- `SUM(revenue)` por linha → **R$ 5.396.656,69** (errado, inflado ~8,9x)
- soma de 1 valor por `order_id` → **R$ 606.144,09** (correto)

Esse número é o **valor-âncora do projeto**: toda medida de receita agrega a partir de uma linha por
`order_id`, e qualquer divergência na implementação é tratada como bug, não como variação aceitável
(`docs/discovery/data_quality_report.md` achado #1; `docs/analytics/kpi_catalog.md` KPI 1).

Desdobramento importante: como não há preço unitário nem quantidade por item, **receita por produto
não é computável**. O rateio igualitário da receita do pedido entre seus itens foi testado
formalmente e **rejeitado** (`docs/discovery/revenue_allocation_test.md`): CV mediano de 60% do
preço implícito, um produto com ~350x de amplitude, a categoria `nab` ficando mais "cara" que beer e
liquor (invertendo a hipótese de negócio) e um único pedido de R$ 125.476,66 contaminando 14
produtos. Por decisão do dono do projeto (2026-10-02), **Top 5 Products é por frequência em pedidos**
(`COUNT(DISTINCT order_id)` por produto), rotulado como tal em todo visual e nunca formatado como
moeda.

Outras limitações estruturais, todas documentadas e replicadas na aba de conclusão do dashboard:
apenas 8 clientes (nada generalizável); um único ano com novembro parcial (sem YoY); moeda não
confirmada; meta sem dimensão de mês (tratada como constante mensal); 40 linhas com `revenue = 0`
mantidas como pedidos válidos por decisão conservadora.

## 3. Como foi construído

Arquitetura multiagente — nove papéis especializados que se comunicam por **artefatos persistidos no
repositório**, não por memória de conversa. Especificação operacional em
[`CLAUDE.md`](CLAUDE.md); especificação original em `docs/arquitetura_multiagentes_powerbi.docx`.

| # | Agente | Onde gravou |
|---|---|---|
| — | Orchestrator / Project Lead | sessão principal + `CLAUDE.md` |
| 01 | EDA Specialist | `docs/discovery/`, `reports/figures/` |
| 02 | Analytics & Storytelling Architect | `docs/analytics/` |
| 03 | Dashboard Visual Designer | `design/` |
| 04 | DAX & Power BI Engineer | `powerbi/` |
| 05 | GitHub Operator | versionamento (só com autorização explícita) |
| 06 | Independent BI Reviewer | `docs/review/final_audit.md` |
| 07 | Cleanup Executor | limpeza de estrutura |
| 08 | PDM Documenter | `docs/review/project_documentation.pdf`, este README |

Princípios que se enxergam nos arquivos: artefato como contrato (`docs/analytics/analytics_handoff.json`
é o handoff estruturado literal entre análise, design e DAX); checkpoint humano antes de decisão
relevante (a reformulação do Top 5 só fechou com confirmação do dono do projeto; o `.pptx` editado
manualmente por ele nunca foi sobrescrito por um agente); rastreabilidade requisito → evidência → KPI
→ visual → medida → validação; e auditoria independente lendo os arquivos originais, não a
documentação sobre eles — foi assim que o achado MAJOR R1 apareceu.

## 4. Estrutura do repositório (estado real)

```
bi-case-pbi/
├── CLAUDE.md                        # arquitetura multiagente e regras do projeto
├── README.md
├── .claude/agents/                  # definição dos 8 agentes especialistas
├── data/raw/                        # 4 .xlsx brutos — SOMENTE LEITURA
├── docs/
│   ├── Power_BI_–_Activities_Data.pdf        # case original
│   ├── arquitetura_multiagentes_powerbi.docx # spec original da arquitetura
│   ├── discovery/                   # saída do EDA Specialist
│   │   ├── eda_report.md            # contexto, método, grão, joins, perguntas abertas
│   │   ├── data_dictionary.md       # coluna por coluna, tipos, nulos, cardinalidade
│   │   ├── data_quality_report.md   # 8 achados com números e severidade
│   │   ├── data_profile.csv         # perfil estatístico bruto
│   │   ├── eda_summary.json         # resumo estruturado (handoff EDA → Analytics)
│   │   └── revenue_allocation_test.md  # teste do rateio de receita (rejeitado)
│   ├── analytics/                   # saída do Analytics Architect
│   │   ├── business_context.md      # requisitos verbatim do PDF + leitura de negócio
│   │   ├── analytical_storyline.md  # árvore de perguntas + arco narrativo
│   │   ├── kpi_catalog.md           # 7 KPIs: fórmula, grão, filtros, evidência, limitação
│   │   ├── dashboard_blueprint.md   # 5 páginas e o que entra em cada uma
│   │   ├── visual_specification.md  # visual a visual, rótulos e disclaimers obrigatórios
│   │   └── analytics_handoff.json   # contrato estruturado para Design e DAX
│   └── review/
│       ├── final_audit.md           # auditoria independente (0 BLOCKER, 1 MAJOR, 4 MINOR)
│       └── project_documentation.pdf# documento consolidado do projeto (PDM)
├── design/
│   ├── design_system.md             # canvas, paleta real, hierarquia, pendências
│   ├── layout_coordinates.json      # posição em polegadas de cada visual, por página
│   ├── pptx/ABInBev_dashboard_background.pptx  # FONTE DA VERDADE VISUAL (edição manual)
│   ├── exports/{overview,detail}.png           # aproximações renderizadas via Pillow
│   ├── build_dashboard_backgrounds.py          # histórico — NÃO reexecutar
│   └── render_png_exports.py                   # gera os PNGs a partir das coordenadas
├── powerbi/
│   ├── model/semantic_model.md      # tabelas, transformações, relacionamentos, limitações
│   ├── model/abinbev_theme.json     # tema Power BI derivado da paleta real do pptx
│   ├── dax/01_base_measures.dax     # Total Revenue, Distinct Order Count, Order Lines Count
│   ├── dax/02_business_kpis.dax     # Average Ticket, MoM, Revenue vs Target, Top 5, categoria
│   ├── dax/03_time_intelligence.dax # dim_date, Revenue PM, YTD Revenue
│   └── validation/dax_validation.md # reconciliação medida por medida + lacunas declaradas
└── reports/figures/                 # 5 figuras exploratórias (grão corrigido)
```

Nota: a seção "Estrutura de diretórios" do `CLAUDE.md` ainda descreve a árvore *planejada*
(`docs/design/`, `docs/implementation/`), que não foi a seguida — é o achado R6 da auditoria, com a
metade de sistema de arquivos já resolvida (nenhuma pasta vazia restante) e a metade de documentação
ainda aberta.

## 5. Status atual

**Pronto e versionado:** EDA completo; 7 KPIs com decisão fechada e evidência; modelo semântico
especificado tabela por tabela com as transformações de Power Query nomeadas; 11 expressões DAX
comentadas; background de 5 páginas em `.pptx` com coordenadas documentadas; tema Power BI;
auditoria independente (**0 BLOCKER**); documento consolidado em PDF.

**Depende de passo manual no Power BI Desktop — não feito:** **não existe `.pbix` neste
repositório.** O dashboard existe como especificação executável, não como relatório publicado. Ver
o roteiro em §6.

**Pendências abertas** (detalhe em `docs/review/final_audit.md` e na seção 8 do PDF consolidado):

| ID | Sev. | Pendência |
|---|---|---|
| R1 | MAJOR | Slide 3 do `.pptx`: subtítulo ("PENDENTE Analytics Architect…") e placeholder de corpo ainda obsoletos, contradizendo o título já correto; fundo do card ainda `#EEEDEA` em vez de branco + dourado. Requer autorização do dono do projeto (arquivo de edição manual dele) |
| R3 | MINOR | Nenhuma medida DAX foi executada em motor Power BI real — a corretude afirmada é de fórmula e grão |
| R5 | MINOR | Banner n=8 está depois (não antes) da barra de filtros; aceito como não-bloqueante pelo auditor |
| R6 | MINOR | `CLAUDE.md` descreve estrutura de diretórios que não foi a seguida |
| R7 | MINOR | Scripts de perfilagem do EDA não versionados (números existem em prosa); o setup de ambiente está documentado em §7 |
| — | — | `design/design_system.md` está desatualizado quanto ao estado real do slide 3 (ver contradição C1 no PDF consolidado) |

## 6. Como reproduzir / continuar

### 6.1 Construir o dashboard no Power BI Desktop

1. Importar os 4 `.xlsx` de `data/raw/`.
2. Aplicar as transformações de `powerbi/model/semantic_model.md`: Remove Duplicates nas 5 colunas de
   orders (→ 1.651 linhas); Remove Duplicates em items (→ 314 linhas); criar `order_revenue` como
   `DISTINCT(order_id, order_date, user_id, revenue)` (→ 356 linhas); `category_display` para as 5
   categorias nulas; De-Para de cidade (SP→São Paulo, RJ→Rio de Janeiro, nulo→"Não informado").
3. Criar `dim_date` (`03_time_intelligence.dax`), **marcá-la como Date Table** e criar os
   relacionamentos: `dim_date[Date] → order_revenue[order_date]`, `order_revenue → dim_customer`,
   `dim_customer → targets`, `fact_orders[product_id] → dim_product[item_id]`. `order_revenue` e
   `fact_orders` **não** se relacionam entre si — isso é intencional.
4. Colar as medidas dos três arquivos de `powerbi/dax/`.
5. **Teste de aceitação:** `[Total Revenue]` sem filtro deve retornar exatamente **R$ 606.144,09**.
   Se divergir, o erro está no Power Query (dedupe) ou nos relacionamentos, não na fórmula DAX.
6. Aplicar `powerbi/model/abinbev_theme.json` e usar os 5 slides de
   `design/pptx/ABInBev_dashboard_background.pptx` como background das páginas, posicionando os
   visuais pelas coordenadas de `design/layout_coordinates.json`.
7. Respeitar os rótulos e disclaimers obrigatórios de `docs/analytics/visual_specification.md` — eles
   são regra de integridade de leitura, não decoração.
8. Registrar o resultado da validação em `powerbi/validation/dax_validation.md` (fecha o achado R3).

### 6.2 Ambiente Python usado nos artefatos (achado R7)

Ambiente Windows **sem `python3` nativo**; o executável disponível é `py` (Python 3.12.10). Nenhuma
biblioteca estava pré-instalada. Comando exato usado nesta sessão (requer acesso a PyPI):

```powershell
py -m pip install pandas openpyxl matplotlib python-pptx Pillow reportlab
```

Para onde cada uma serviu: `pandas` + `openpyxl` para a leitura completa dos `.xlsx` (EDA e teste de
rateio); `matplotlib` para `reports/figures/`; `python-pptx` para inspecionar o `.pptx` do usuário
(coordenadas, paleta e auditoria do slide 3); `Pillow` para `design/render_png_exports.py`;
`reportlab` para gerar `docs/review/project_documentation.pdf`. Os scripts de perfilagem do EDA em si
não foram versionados — versioná-los é a parte ainda aberta de R7.

### 6.3 Ordem de leitura recomendada

`docs/review/project_documentation.pdf` (visão completa) → `docs/discovery/data_quality_report.md`
(por que o grão importa) → `docs/discovery/revenue_allocation_test.md` (a decisão mais consequente)
→ `docs/analytics/kpi_catalog.md` (o contrato dos KPIs) → `powerbi/model/semantic_model.md` +
`powerbi/dax/` (a implementação) → `docs/review/final_audit.md` (o que um auditor independente
encontrou).

---

Publicado em https://github.com/VictorOS1997/sales-dashboard-case (branch `main`).
`data/raw/` é somente leitura; nenhum dado sensível ou credencial é versionado.
