# bi-case-pbi

Case de Data Analyst / BI — entregável final em Power BI, construído por um sistema
multiagente. Ver `CLAUDE.md` para a arquitetura completa e
`docs/arquitetura_multiagentes_powerbi.docx` para a especificação original.

## Estado atual

- Dados brutos em `data/raw/` (PBI_items, PBI_orders, PBI_targets, PBI_users).
- Case descrito em `docs/Power_BI_–_Activities_Data.pdf`.
- Agentes definidos em `.claude/agents/`. Nenhuma etapa de análise rodou ainda.

## Próximo passo

Orchestrator aciona `eda-specialist` para data discovery antes de qualquer definição de
KPI ou storytelling.
