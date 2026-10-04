# bi-case-pbi — Case de BI: dashboard de vendas de bebidas (Power BI)

Case técnico de Data Analyst / BI resolvido por um sistema multiagente. Este repositório contém o
**dashboard Power BI entregue** (`pbi_case.pbix`, 5 páginas, a 5ª oculta) e toda a documentação que o
sustenta: EDA completo, catálogo de KPIs com evidência, modelo semântico, medidas DAX validadas no
Power BI Desktop, backgrounds visuais, tema e auditoria independente com addendum de fechamento.

Documento consolidado do projeto (8 páginas, visão de Product Data Management):
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
├── PROGRESS.md                      # marco de conclusão do projeto (2026-10-03)
├── pbi_case.pbix                    # dashboard Power BI entregue (5 páginas, 5ª oculta)
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
│       ├── final_audit.md           # auditoria independente (0 BLOCKER, 1 MAJOR, 4 MINOR) + addendum de fechamento 2026-10-03
│       └── project_documentation.pdf# documento consolidado do projeto (PDM)
├── design/
│   ├── design_system.md             # canvas, paleta real, hierarquia, pendências
│   ├── layout_coordinates.json      # posição em polegadas de cada visual, por página
│   ├── pptx/ABInBev_dashboard_background.pptx  # fonte visual original (edição manual do usuário)
│   ├── pptx/ABInBev_dashboard_background_EN.pptx # versão EN do background
│   ├── pptx/background/             # 5 PNGs de background (EN) usados nas páginas
│   ├── exports/{overview,detail}.png           # aproximações renderizadas via Pillow
│   ├── build_dashboard_backgrounds.py          # histórico — NÃO reexecutar
│   └── render_png_exports.py                   # gera os PNGs a partir das coordenadas
├── powerbi/
│   ├── model/semantic_model.md      # tabelas, transformações, relacionamentos, limitações
│   ├── model/abinbev_theme.json     # tema Power BI derivado da paleta real do pptx
│   ├── dax/01_base_measures.dax     # Total Revenue, Distinct Order Count, Order Lines Count
│   ├── dax/02_business_kpis.dax     # Average Ticket, MoM, Revenue vs Target, Top 5, categoria
│   ├── dax/03_time_intelligence.dax # dim_date, Revenue PM, YTD Revenue
│   ├── dax/04_dashboard_helpers.dax # Partial Month Note, YTD Title, MoM Color, Revenue % of Total, Target in Period, Unsold Products
│   └── validation/
│       ├── dax_validation.md        # reconciliação lógica + validação real no Power BI Desktop (2026-10-03)
│       └── validation.png, validation matrix.png  # evidências da validação no Desktop
└── reports/figures/                 # 5 figuras exploratórias (grão corrigido)
```

Nota: o achado R6 da auditoria (estrutura planejada vs. real) consta como fechado no addendum de
`docs/review/final_audit.md`: o `CLAUDE.md` descreve a estrutura real e não restam pastas vazias.

## 5. Como reproduzir / continuar

### 5.1 Construir o dashboard no Power BI Desktop

1. Importar os 4 `.xlsx` de `data/raw/`.
2. Aplicar as transformações de `powerbi/model/semantic_model.md`: Remove Duplicates nas 5 colunas de
   orders (→ 1.651 linhas); `dim_product` via **Group By `item_id` + Max(`category`)** (→ 314 linhas,
   todas com categoria; resolve o achado #5 — não existe coluna `category_display`); criar
   `order_revenue` como `DISTINCT(order_id, order_date, user_id, revenue)` (→ 356 linhas); De-Para de
   cidade (SP→São Paulo, RJ→Rio de Janeiro, nulo→"Não informado").
3. Criar `dim_date` (`03_time_intelligence.dax`), **marcá-la como Date Table** e criar os
   relacionamentos: `dim_date[Date] → order_revenue[order_date]`, `order_revenue → dim_customer`,
   `dim_customer → targets`, `fact_orders[product_id] → dim_product[item_id]`, mais os dois
   relacionamentos extras do modelo final, necessários para os slicers filtrarem os visuais de
   produto: `dim_date[Date] → fact_orders[order_date]` e `dim_customer[user_id] → fact_orders[user_id]`.
   `order_revenue` e `fact_orders` **não** se relacionam entre si — isso é intencional.
4. Colar todas as medidas dos 4 arquivos de `powerbi/dax/` (`01` a `04`; o `04_dashboard_helpers.dax`
   traz as medidas de apoio aos visuais).
5. **Teste de aceitação:** `[Total Revenue]` sem filtro deve retornar exatamente **R$ 606.144,09**.
   Se divergir, o erro está no Power Query (dedupe) ou nos relacionamentos, não na fórmula DAX.
6. Aplicar `powerbi/model/abinbev_theme.json` e usar os backgrounds de `design/pptx/background/`
   (PNGs exportados do design) nas páginas, posicionando os visuais pelas coordenadas de
   `design/layout_coordinates.json`. O resultado montado é o `pbi_case.pbix` na raiz.
7. Respeitar os rótulos e disclaimers obrigatórios de `docs/analytics/visual_specification.md` — eles
   são regra de integridade de leitura, não decoração.
8. Registrar o resultado da validação em `powerbi/validation/dax_validation.md` (já feito em 2026-10-03; fechou o achado R3).

### 5.2 Ambiente Python usado nos artefatos (achado R7)

Ambiente Windows **sem `python3` nativo**; o executável disponível é `py` (Python 3.12.10). Nenhuma
biblioteca estava pré-instalada. Comando exato usado nesta sessão (requer acesso a PyPI):

```powershell
py -m pip install pandas openpyxl matplotlib python-pptx Pillow reportlab
```

Para onde cada uma serviu: `pandas` + `openpyxl` para a leitura completa dos `.xlsx` (EDA e teste de
rateio); `matplotlib` para `reports/figures/`; `python-pptx` para inspecionar o `.pptx` do usuário
(coordenadas, paleta e auditoria do slide 3); `Pillow` para `design/render_png_exports.py`;
`reportlab` para gerar `docs/review/project_documentation.pdf`. Os scripts de perfilagem do EDA em si
não foram versionados — R7 foi aceito como limitação (addendum de `final_audit.md`).

### 5.3 Ordem de leitura recomendada

`docs/review/project_documentation.pdf` (visão completa) → `docs/discovery/data_quality_report.md`
(por que o grão importa) → `docs/discovery/revenue_allocation_test.md` (a decisão mais consequente)
→ `docs/analytics/kpi_catalog.md` (o contrato dos KPIs) → `powerbi/model/semantic_model.md` +
`powerbi/dax/` (a implementação) → `docs/review/final_audit.md` (o que um auditor independente
encontrou).

---

Publicado em https://github.com/VictorOS1997/sales-dashboard-case (branch `main`).
`data/raw/` é somente leitura; nenhum dado sensível ou credencial é versionado.
