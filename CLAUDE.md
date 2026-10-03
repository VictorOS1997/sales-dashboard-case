# bi-case-pbi — Arquitetura Multiagentes

Projeto de case de Data Analyst / BI. Entregável final: dashboard em Power BI.
Esta arquitetura é multiagente: cada agente é especialista em uma etapa, comunica
descobertas por artefatos persistidos (não só por chat) e respeita checkpoints humanos.

Especificação completa: `docs/arquitetura_multiagentes_powerbi.docx`.
Case/dados de apoio: `docs/Power_BI_–_Activities_Data.pdf`.

## Princípios

- Separar descoberta dos dados, interpretação analítica e implementação.
- Artefatos no repositório são o contrato de comunicação entre agentes (não assumir que
  outro agente "lembra" de algo que não está escrito em arquivo).
- Autonomia para explorar/codificar/testar; checkpoint humano antes de decisões relevantes
  e antes de publicar/commitar.
- Rastreabilidade: requisito → evidência → KPI → visualização → medida → validação.
- `data/raw/` é somente leitura. Nunca versionar dados sensíveis ou credenciais.

## Agentes

| Agente | Arquivo | Modelo sugerido | Autonomia |
|---|---|---|---|
| Orchestrator / Project Lead | (este CLAUDE.md + sessão principal) | Opus | Coordena e delega |
| 01 EDA Specialist | `.claude/agents/eda-specialist.md` | Opus | Exploração autônoma |
| 02 Analytics & Storytelling Architect | `.claude/agents/analytics-architect.md` | Opus | Narrativa, validação humana |
| 03 Dashboard Visual Designer | `.claude/agents/dashboard-designer.md` | Opus | Produção de layout |
| 04 DAX & Power BI Engineer | `.claude/agents/dax-engineer.md` | Opus | Implementação e testes |
| 05 GitHub Operator | `.claude/agents/github-operator.md` | Haiku | Só com autorização |
| 06 Independent BI Reviewer | `.claude/agents/bi-reviewer.md` | Opus | Auditoria independente |
| 07 Cleanup Executor | `.claude/agents/cleanup-executor.md` | Sonnet | Execução mecânica, sem decisão de conteúdo |
| 08 PDM Documenter | `.claude/agents/pdm-documenter.md` | Opus | Consolida projeto em PDF + reescreve README |

## Fluxo de execução

1. Orchestrator lê o case e define escopo.
2. EDA Specialist faz profiling → `docs/discovery/`.
3. Analytics Architect define storyline/KPIs a partir do EDA → `docs/analytics/`.
4. **Checkpoint humano** — aprovar direção analítica antes de implementar.
5. Design e DAX trabalham em paralelo a partir do blueprint aprovado.
6. BI Reviewer audita tudo de forma independente → `docs/review/final_audit.md`.
7. Orchestrator encaminha correções aos especialistas responsáveis.
8. GitHub Operator versiona, só após aprovação explícita.

Não é obrigatório acionar todos os agentes em toda solicitação — delegar só o necessário.

## Estrutura de diretórios

```
bi-case-pbi/
├── CLAUDE.md
├── .claude/agents/          # definição dos 8 agentes
├── docs/
│   ├── discovery/           # saída do EDA Specialist
│   ├── analytics/           # saída do Analytics Architect
│   └── review/              # saída do BI Reviewer e do PDM Documenter
├── data/raw/
├── design/{pptx,exports}/   # saída do Dashboard Designer (pptx = fonte da verdade editada pelo usuário)
├── powerbi/{dax,model,validation}/  # saída do DAX Engineer
└── reports/figures/         # saída do EDA Specialist
```

## Contratos de comunicação

Handoffs entre agentes devem ser arquivos estruturados (JSON/Markdown), não só mensagens.
Exemplo (EDA → Analytics), formato ilustrativo:

```json
{
  "dataset": "activities",
  "grain": "one row per activity",
  "validated_fields": ["activity_id", "activity_date", "activity_type"],
  "quality_issues": [{
    "field": "activity_date",
    "issue": "missing_values",
    "severity": "major",
    "business_impact": "May affect temporal analysis"
  }],
  "validated_metrics": [],
  "limitations": ["Temporal coverage requires confirmation"],
  "recommended_next_step": "Validate period completeness before defining growth KPIs"
}
```

## Definition of Done

- Data discovery: dicionário, qualidade e limitações documentados.
- Integridade: métricas reconciliadas com referências do EDA.
- Storytelling: cada página do dashboard responde a uma pergunta de negócio.
- KPIs: fórmula, campos, granularidade, filtros e limitações rastreáveis.
- Design: backgrounds aderentes à especificação aprovada.
- DAX: medidas testadas em contextos de filtro relevantes.
- Case: requisitos obrigatórios cobertos.
- Revisão: nenhum BLOCKER ou MAJOR pendente.
- GitHub: commit limpo, sem dados brutos/credenciais.

## Regras gerais

- Nunca inferir causalidade ou crescimento real sem validar cobertura, definição e comparabilidade.
- Nenhum agente deve alterar definição de KPI sem comunicar o Analytics Architect.
- Design não inventa números/conclusões — qualquer mudança de narrativa volta para Analytics.
- GitHub Operator nunca força push, sobrescreve histórico ou commita sem autorização.
