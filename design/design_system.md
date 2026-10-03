# Design System — Dashboard Backgrounds (bi-case-pbi)

**Atualizado em 2026-10-02.** Esta versão descreve fielmente
`design/pptx/ABInBev_dashboard_background.pptx` — o arquivo que o usuário editou
manualmente (ajuste de *placement* e colorimetria) e que agora é a fonte da verdade
visual do projeto. O arquivo gerado anteriormente pelo script do Design
(`design/pptx/dashboard_background.pptx`) foi descontinuado — ver seção "O que mudou"
no final deste documento.

Não contém nenhum KPI/número real — apenas organiza espaço visual para o que o DAX
Engineer vai alimentar depois no Power BI.

## Canvas

- **20.0in x 11.25in** (16:9 widescreen) — maior que o rascunho anterior (13.333x7.5in),
  mesma proporção, ~1.5x de escala linear.
- Margem externa observada: **0.5in** nas laterais.
- Faixa de cabeçalho fixa: **0–1.25in** de altura, mais uma linha de acento dourado em
  1.208–1.25in.
- Logotipo (ABInBev) no canto superior direito de cada página: `left=17.052in,
  top=0.375in, width=2.448in, height=0.458in` (imagem PNG embutida, 3814x714px).
- Nota/rodapé textual por página a partir de **top ≈ 10.583in**.
- Não há mais grid uniforme de 12 colunas explícito; os cartões usam larguras
  customizadas por página (ex.: 4 KPIs de 4.562in cada na página 1; dois blocos de
  9.375in na página 3). Ver `design/layout_coordinates.json` para a posição exata de
  cada visual, por página.

## Paleta real (extraída do pptx do usuário)

| Token | Hex | Uso observado |
|---|---|---|
| `header_band` | `#000000` | faixa de cabeçalho de cada página (preto, não mais azul-marinho `#1F2A44`) |
| `accent_gold` | `#E5B611` | linha de acento sob o cabeçalho; topo dos cartões KPI |
| `accent_gold_text` | `#E9C95A` | subtítulo/pergunta de negócio no cabeçalho (texto dourado claro sobre preto) |
| `card_bg` | `#FFFFFF` | fundo de cartões normais (KPI, gráfico) |
| `divider` | `#E2DFD8` | bordas/divisórias neutras entre cartões (substituiu `#D8DBE0`) |
| `text_dark` | `#141414` | texto principal (títulos de cartão, labels de filtro) — mais escuro que o `#1F2430` anterior |
| `text_muted` | `#6B6760` | subtítulos/notas secundárias |
| `text_footer` | `#8A867E` | texto de rodapé de página |
| `placeholder_tag` | `#A8A398` | texto dos placeholders `[ área de gráfico ]` / `[ valor — KPI do DAX ]` |
| `warning_bg` | `#FFF7D9` | fundo de banners de aviso fixo e do disclaimer do Top 5 (substituiu `#EFE7D3`, tom mais claro/amarelo-creme) |
| `warning_text` | `#5C4A12` | texto sobre `warning_bg` (mantido) |
| `pending_bg` | `#EEEDEA` | fundo do placeholder "Ranking de Produtos (critério em definição)" (substituiu `#ECECEC`, tom bem próximo) |
| `pending_text` | `#55524C` | texto sobre `pending_bg` |

Fonte: **Segoe UI** em todos os elementos de texto (mantida do rascunho anterior).

Regra herdada de `visual_specification.md` permanece válida: nenhuma cor
vermelha/verde de "bom/ruim" sobre dados ainda não validados contra meta real. O pptx
do usuário segue essa regra — não há vermelho/verde em nenhum slide, só preto, dourado,
branco, cinza-quente e o amarelo-creme de aviso.

## Hierarquia visual por página (mantida)

1. Faixa de cabeçalho preta (nome da página + pergunta de negócio em dourado claro) +
   logotipo no canto superior direito.
2. Barra de filtros globais (Período, Cliente, Cidade, Categoria de estabelecimento) —
   ausente apenas na página Conclusion (oculta).
3. Linha de cartões KPI / blocos principais.
4. Área de gráficos principais.
5. Banners/avisos fixos (fundo `#FFF7D9`), não removíveis por filtro.
6. Rodapé com nota metodológica textual.

## Páginas (5), posições reais em polegadas — ver `layout_coordinates.json` para detalhe completo

| # | Página | Observações de layout (ABInBev_dashboard_background.pptx) |
|---|---|---|
| 1 | Executive Overview | 4 cartões KPI de 4.562x2.083in cada (top=2.333) + 1 card de tendência mensal full-width 19x5.75in (top=4.667) |
| 2 | Time Analysis | Card alternável linha/coluna 12.5x4.958in + YTD 6.25x4.958in lado a lado (top=2.333); MoM Growth full-width 19x2.875in embaixo (top=7.542) |
| 3 | Product Analysis | Ranking de Produtos — título preenchido ("Top 5 Produtos por Frequência de Pedidos"); **estilo visual do card ainda pendente** (9.375x4.458in, fundo `#EEEDEA`, top=2.333) + disclaimer fixo preenchido (texto final do Analytics Architect) abaixo (9.375x0.583in, fundo `#FFF7D9`, top=6.958) + Linhas de Pedido por Categoria (9.375x5.208in) à direita + KPI de produtos sem venda (6.25x2.625in) + banner de limitação de receita por produto (12.5x2.625in) embaixo |
| 4 | Customer Analysis | Banner n=8 (19x0.583in, fundo `#FFF7D9`) **abaixo** da barra de filtros (ver nota de divergência abaixo) + Receita por Cliente toggle (11.25x4.375in) + Receita vs Meta (7.5x4.375in) + Receita por Tipo de Estabelecimento (9.375x2.625in) + Receita por Cidade (9.375x2.625in) |
| 5 | Conclusion (hidden) | 3 blocos de texto empilhados, 19x2.806in cada: achados, metodologia, limitações |

### Nota de divergência menor (página 4)

No rascunho anterior do Design, o banner de amostra pequena (n=8) ficava **antes** da
barra de filtros, conforme leitura literal de `visual_specification.md` ("posicionado
no topo da página, não no rodapé"). No pptx do usuário, o banner está posicionado
**depois** da barra de filtros (filtros em `top=1.5`, banner em `top=2.333`) — ainda é
o primeiro bloco de conteúdo da página e não está no rodapé, então a regra de negócio
("sempre visível, fixo, não no rodapé") continua atendida; é apenas uma inversão de
ordem com a barra de filtros. Registrado aqui para o Orchestrator/Analytics Architect
avaliar se importa corrigir — Design não alterou o arquivo do usuário para isso.

## PENDÊNCIA EM ABERTO — Top 5 Products (critério fechado, mas pptx ainda não atualizado)

**O que já foi decidido (fonte: `docs/analytics/visual_specification.md` e
`docs/analytics/analytics_handoff.json` → `kpis[4].footer_disclaimer`):**
- Critério oficial do Top 5 Products: **frequência em pedidos** (COUNT DISTINCT
  order_id por produto) — não é mais "em definição".
- Texto final do disclaimer fixo já está escrito e aprovado (ver citação completa
  abaixo).

**O que o pptx do usuário (`ABInBev_dashboard_background.pptx`) ainda contém, slide 3,
inspecionado em 2026-10-02:**
- O cartão (`left=0.5in, top=2.333in, width=9.375in, height=4.458in`, fundo
  `#EEEDEA`, estilo "pendente") ainda tem o título **"Ranking de Produtos (critério em
  definição)"** e subtítulo **"PENDENTE Analytics Architect: frequência em pedidos vs
  receita via rateio — não assumir eixo final"** — texto antigo, não atualizado.
- A área de disclaimer fixo abaixo (`left=0.5in, top=6.958in, width=9.375in,
  height=0.583in`, fundo `#FFF7D9`) **existe e está no lugar certo**, mas ainda contém
  o texto reservado provisório do Design: *"[reservado p/ Analytics] Receita não é
  rastreável por produto individual nos dados brutos — ranking é por frequência em
  pedidos, não por valor."* — não o texto final.

**Isto é registrado como PENDÊNCIA DE PREENCHIMENTO (conteúdo/texto), não como
pendência de layout.** O Design não editou o pptx do usuário para isso, porque: (a) é
arquivo do usuário, editado manualmente por ele por razão explícita de
placement/colorimetria — sobrescrever texto sem pedido explícito poderia conflitar com
o próximo ajuste manual dele; (b) a tarefa pede para registrar como pendência quando o
pptx ainda não reflete a decisão, não para corrigi-lo silenciosamente.

Texto final oficial a ser copiado literalmente para o disclaimer quando o usuário (ou
quem for editar o pptx) atualizar o slide 3:

> "Este ranking mostra os produtos que aparecem no maior número de pedidos — não os que
> geram mais receita. Os dados de origem registram apenas o valor total de cada
> pedido, não o preço de cada item, então não é possível calcular receita por produto
> individual. Testamos dividir a receita igualmente entre os itens do pedido como
> alternativa, mas o resultado foi inconsistente (preços implícitos variando até 350x
> para o mesmo produto) e foi descartado. Por isso, o critério oficial do Top 5 é
> frequência em pedidos."

Ações pendentes de preenchimento, quando autorizado a editar o pptx do usuário:
1. Atualizar o título do card de "Ranking de Produtos (critério em definição)" para o
   rótulo aprovado — `visual_specification.md` sugere **"Top 5 Produtos por Nº de
   Pedidos"**, com subtítulo obrigatório **"frequência em pedidos — não representa
   receita"**.
2. Remover o estilo pendente (fundo `#EEEDEA`) e aplicar o estilo normal de card de
   gráfico (fundo `#FFFFFF` + acento dourado `#E5B611`, igual aos demais cartões de
   gráfico da página).
3. Substituir o texto provisório do disclaimer fixo pelo texto final citado acima
   (área/posição já está correta, não precisa re-layoutar).

## Interatividade mapeada no layout (mantida)

- **Requisito #1** (dois gráficos que alternam por tipo selecionado): página 2, card
  "Receita Mensal / Pedidos por Mês (alternável)", 12.5in de largura.
- **Requisito #2** (toggle absoluto/percentual): página 4, card "Receita por Cliente
  (R$ <-> %)", 11.25in de largura.

## Arquivos

- `design/pptx/ABInBev_dashboard_background.pptx` — **fonte da verdade visual atual**
  (editado manualmente pelo usuário). 5 slides, 20x11.25in.
- `design/exports/overview.png` — aproximação renderizada da página 1 (Executive
  Overview) a partir das coordenadas/paleta reais acima.
- `design/exports/detail.png` — aproximação renderizada da página 3 (Product
  Analysis), mostrando o placeholder ainda pendente + disclaimer ainda não preenchido.
- `design/layout_coordinates.json` — posições reais (em polegadas) de cada visual, por
  página, extraídas por inspeção direta do pptx do usuário; inclui notas de pendência
  inline (`_status_2026_10_02`) nos itens do Top 5 Products.
- `design/build_dashboard_backgrounds.py` — script original (python-pptx) que gerava o
  antigo `dashboard_background.pptx`. **Mantido apenas como histórico/referência de
  como o layout inicial foi derivado do blueprint** — não gera mais o pptx vigente, já
  que o usuário assumiu edição manual do background. Comentário de cabeçalho do script
  não foi alterado; ver seção abaixo.
- `design/render_png_exports.py` — script Pillow que lia `layout_coordinates.json` e
  gerava os PNGs. Reaproveitado/atualizado para a nova paleta e canvas 20x11.25in (ver
  "O que mudou").

## O que mudou nesta atualização (2026-10-02)

1. **Arquivo-fonte do pptx**: `design/pptx/dashboard_background.pptx` (gerado pelo
   script do Design) não existe mais no repositório — foi substituído por
   `design/pptx/ABInBev_dashboard_background.pptx` (edição manual do usuário). Esta é
   agora a única fonte da verdade visual; `build_dashboard_backgrounds.py` não deve ser
   reexecutado para sobrescrever o pptx do usuário.
2. **Canvas**: 13.333x7.5in → **20.0x11.25in** (mesma proporção 16:9, escala ~1.5x).
3. **Paleta**: faixa de cabeçalho azul-marinho `#1F2A44` → **preto `#000000`**; acento
   azul `#2E5EAA` → **dourado `#E5B611`/`#E9C95A`**; texto principal `#1F2430` →
   **`#141414`**; bordas/divisórias `#D8DBE0` → **`#E2DFD8`**; aviso `#EFE7D3` →
   **`#FFF7D9`** (mais claro); pendente `#ECECEC` → **`#EEEDEA`** (quase igual).
4. **Logotipo**: adicionado um logo (ABInBev) no canto superior direito de cada
   página — elemento novo que não existia no rascunho do Design.
5. **Conteúdo/placeholders**: posições e hierarquia de todos os cartões foram
   preservadas 1:1 em proporção; nenhum texto de KPI foi preenchido com número real.
   O placeholder do Top 5 Products e o disclaimer fixo da página 3 **não foram
   atualizados** pelo usuário — permanecem com o texto antigo "critério em definição" /
   "[reservado p/ Analytics]" mesmo com a decisão de negócio já fechada (ver seção de
   pendência acima).
6. **PNGs**: `overview.png` e `detail.png` foram regerados a partir das coordenadas e
   paleta reais acima, via Pillow (sem LibreOffice/PowerPoint disponível no ambiente
   para exportação nativa do pptx) — são aproximações visuais, não um render exato do
   PowerPoint.

## Limitações deste esboço

- PNGs são aproximações via Pillow a partir das coordenadas lidas do pptx — podem
  apresentar pequenas diferenças tipográficas/de antialiasing em relação ao pptx aberto
  no PowerPoint, mas grid/posições/paleta são fiéis ao arquivo real.
- Nenhum número, KPI ou conclusão foi inventado; qualquer mudança de narrativa
  (inclusive o rótulo final do ranking de produtos) deve voltar para o Analytics
  Architect — já aconteceu (critério fechado), falta apenas o preenchimento no pptx.
