# Progresso — bi-case-pbi

Nota solta de sessão, não é artefato formal do pipeline (esses estão em `docs/` e
`powerbi/`). Serve pra retomar o trabalho amanhã sem perder o fio.

## Onde paramos

Pipeline multiagente (EDA → Analytics → Design + DAX → Reviewer) já rodou por completo e
está publicado em https://github.com/VictorOS1997/sales-dashboard-case (branch `main`,
último commit `bb142b6`). Hoje a sessão foi **montar o modelo de verdade no Power BI
Desktop**, seguindo `powerbi/model/semantic_model.md`.

### Modelo no Power BI — já montado e validado

6 tabelas, todas confirmadas certas por teste de sanidade:

| Tabela | Transformação aplicada | Resultado | Status |
|---|---|---|---|
| `fact_orders` | Remove Duplicates nas 5 colunas (órder_id, order_date, user_id, product_id, revenue) | 1.651 linhas | ✅ |
| `order_revenue` | Referência de `fact_orders`, remove `product_id`, Remove Duplicados nas 4 colunas restantes | 356 linhas | ✅ `SUM(revenue)` bateu **R$ 606.144,09** |
| `dim_product` | **Group By `item_id`, agregação `Max(category)`** (não Remove Duplicates simples — ver achado corrigido abaixo) | 314 linhas | ✅ |
| `dim_customer` | Coluna `city_display` (De-Para SP→São Paulo, RJ→Rio de Janeiro, nulo→"Não informado") | 8 linhas | ✅ |
| `targets` | Coluna `city_display` (mesmo De-Para, sem caso de nulo) | 8 linhas | ✅ |
| `dim_date` | Criada via Power Query (código M, `CALENDAR` 2024-01-01 a 2024-11-30) + coluna `IsPartialMonth` | marcada como Tabela de Datas | ✅ |

Relações criadas (view Modelo):
1. `dim_product[item_id]` → `fact_orders[product_id]` — 1:N
2. `dim_customer[user_id]` → `order_revenue[user_id]` — 1:N
3. `dim_customer[user_id]` → `targets[user_id]` — 1:1
4. `dim_date[Date]` → `order_revenue[order_date]` — 1:N
5. Sem relação física `order_revenue` ↔ `fact_orders` (intencional, evita ambiguidade de filtro — cada uma serve um propósito: receita vs. contagem de item)

### Achado novo descoberto durante a montagem (já corrigido e commitado)

O achado #5 original do EDA ("5 item_id sem categoria preenchida": 9001, 19045, 13105,
14684, 51849) estava **impreciso**. Esses 5 produtos aparecem duplicados (mesmo padrão do
achado #4) e, em cada par, uma linha tem categoria preenchida e a outra tem nula — a
categoria real existe, só estava "escondida" na linha duplicada irmã. Um
`Remove Duplicates` simples no Power Query corria risco de manter a linha errada (ex:
`item_id` 9001 teria ficado sem categoria por acidente). Resolvido com `Table.Group` +
`Max(category)` em vez de Remove Duplicates — por isso `dim_product` deu exatamente 314
linhas, todas com categoria real.

Documentação corrigida e commitada: `docs/discovery/data_quality_report.md` (achado #5
reescrito + changelog), `data_dictionary.md`, `eda_summary.json`. Commit `bb142b6`.

## O que falta (próximos passos, nesta ordem)

1. **Colar as medidas DAX de verdade no modelo.** Os 3 arquivos já existem e estão
   corretos (`powerbi/dax/01_base_measures.dax`, `02_business_kpis.dax`,
   `03_time_intelligence.dax`) — falta criar cada `Nova Medida` no Power BI e colar a
   fórmula. `Total Revenue` já foi validada manualmente (bateu R$606.144,09 testando
   `SUM` direto em `order_revenue` antes mesmo de criar a medida formal) — as outras
   ainda não foram criadas/testadas dentro do PBI.
2. **Montar os visuais** das 5 páginas conforme `design/layout_coordinates.json` e o
   background `design/pptx/ABInBev_dashboard_background.pptx` (exportar como imagem de
   fundo da página — usar a resolução 1920x1080 que já funcionou, não "Ajustar", tamanho
   de página do relatório tem que ser 16:9).
3. **Aplicar o tema de cores** `powerbi/model/abinbev_theme.json` (View → Temas →
   Procurar temas) nos visuais nativos.
4. **Pendência conhecida, deixada em aberto de propósito**: o card "Top 5 Products" no
   pptx ainda tem subtítulo e corpo com texto antigo ("PENDENTE Analytics Architect...",
   "[RANKING DE PRODUTOS — critério em definição]") e fundo cinza de placeholder — só o
   título já foi corrigido. Texto certo e fundo branco/dourado ficaram pendentes por
   decisão sua, não é bug esquecido.
5. Validar cada medida DAX num contexto de filtro (1 cliente, 1 mês) e comparar com os
   números do `dax_validation.md` antes de considerar o modelo fechado.
6. Quando o `.pbix` estiver pronto, não existe ainda nenhum `.pbix` versionado no
   repositório — decidir se quer commitar ele (binário grande, considerar `.gitignore`
   como fez com o pptx) ou só publicar via Power BI Service.
7. Depois de tudo isso: reler `docs/review/final_audit.md` e `docs/review/
   project_documentation.pdf` pra ver se algum achado MINOR (R3, R5, R6, R7) ainda faz
   sentido resolver, e dar o fechamento final do projeto.

## Referências rápidas

- Arquitetura do sistema multiagente: `CLAUDE.md`
- Modelo de dados completo: `powerbi/model/semantic_model.md`
- Documento consolidado (visão PDM): `docs/review/project_documentation.pdf`
- README atualizado com contexto completo do projeto: `README.md`
- Repositório: https://github.com/VictorOS1997/sales-dashboard-case
