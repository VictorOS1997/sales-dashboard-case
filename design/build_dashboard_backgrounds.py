"""
DEPRECATED (2026-10-02): o pptx gerado por este script (dashboard_background.pptx) foi
substituído como fonte da verdade visual por design/pptx/ABInBev_dashboard_background.pptx,
editado manualmente pelo usuário (ajuste de placement/colorimetria). Mantido apenas como
histórico de como o layout inicial foi derivado do blueprint — NÃO reexecutar para
sobrescrever o pptx do usuário. Ver design/design_system.md, seção "O que mudou".

Dashboard Designer — gera backgrounds (PPTX) e exports (PNG) para o case bi-case-pbi.

Fonte: docs/analytics/dashboard_blueprint.md, docs/analytics/visual_specification.md,
       docs/analytics/analytics_handoff.json (Analytics Architect).

Regra: este script NUNCA escreve KPIs/números reais — apenas organiza espaço visual
(grid, hierarquia, placeholders rotulados) para os visuais que o DAX Engineer vai
alimentar depois no Power BI.

PENDENCIA EM ABERTO (Product Analysis / Top 5): o rótulo exato do eixo "Top 5
Products" (frequencia em pedidos vs receita via rateio) esta em decisao. Por isso
o placeholder deste visual usa o rotulo generico "Ranking de Produtos (criterio em
definicao)" e NAO assume frequencia nem receita.
"""

import json
import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------------------------------------------------------------------------
# Design system (paleta funcional, nao final de marca — ver design_system.md)
# ---------------------------------------------------------------------------
PAGE_W_IN = 13.333
PAGE_H_IN = 7.5

COLOR_BG            = RGBColor(0xF5, 0xF6, 0xF8)  # fundo geral da pagina
COLOR_CARD_BG       = RGBColor(0xFF, 0xFF, 0xFF)  # fundo dos cartoes/placeholders
COLOR_BORDER        = RGBColor(0xD8, 0xDB, 0xE0)  # bordas neutras
COLOR_TEXT_DARK     = RGBColor(0x1F, 0x24, 0x30)  # texto principal
COLOR_TEXT_MUTED    = RGBColor(0x6B, 0x72, 0x80)  # texto secundario / notas
COLOR_ACCENT_REAL   = RGBColor(0x2E, 0x5E, 0xAA)  # dado real/fechado (azul)
COLOR_PARTIAL_TONE  = RGBColor(0xC9, 0xA2, 0x27)  # dado parcial/incompleto (ambar, NUNCA vermelho)
COLOR_HEADER_BAND   = RGBColor(0x1F, 0x2A, 0x44)  # faixa de cabecalho das paginas
COLOR_HEADER_TEXT   = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_WARNING_BG    = RGBColor(0xEF, 0xE7, 0xD3)  # banner de aviso (neutro, nao vermelho)
COLOR_WARNING_TEXT  = RGBColor(0x5C, 0x4A, 0x12)
COLOR_PENDING_BG    = RGBColor(0xEC, 0xEC, 0xEC)  # placeholder pendente de decisao (hachura visual)
COLOR_PENDING_BORDER= RGBColor(0x9A, 0x9A, 0x9A)
COLOR_PENDING_TEXT  = RGBColor(0x55, 0x55, 0x55)
COLOR_FOOTER_TEXT   = RGBColor(0x8A, 0x8F, 0x99)

FONT_NAME = "Segoe UI"

# Grid: margens + 12 colunas
MARGIN = 0.4
GUTTER = 0.14
HEADER_H = 0.62
FOOTER_H = 0.34
CONTENT_TOP = MARGIN + HEADER_H + 0.12
CONTENT_BOTTOM = PAGE_H_IN - MARGIN - FOOTER_H - 0.1
CONTENT_H = CONTENT_BOTTOM - CONTENT_TOP
CONTENT_LEFT = MARGIN
CONTENT_W = PAGE_W_IN - 2 * MARGIN
N_COLS = 12
COL_W = (CONTENT_W - (N_COLS - 1) * GUTTER) / N_COLS


def col_span(start_col, n_cols):
    """Retorna (left, width) em polegadas para colunas 0-indexed do grid de 12."""
    left = CONTENT_LEFT + start_col * (COL_W + GUTTER)
    width = n_cols * COL_W + (n_cols - 1) * GUTTER
    return left, width


layout_coordinates = {"unit": "inches", "canvas": {"width": PAGE_W_IN, "height": PAGE_H_IN}, "grid": {
    "columns": N_COLS, "margin": MARGIN, "gutter": GUTTER, "column_width": round(COL_W, 4),
    "content_top": round(CONTENT_TOP, 4), "content_bottom": round(CONTENT_BOTTOM, 4)
}, "pages": []}


def set_no_line(shape):
    shape.line.fill.background()


def add_rect(slide, left, top, width, height, fill_color, line_color=None, line_dash=None, shadow=False):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    shp.adjustments[0] = 0.045
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill_color
    if line_color is None:
        set_no_line(shp)
    else:
        shp.line.color.rgb = line_color
        shp.line.width = Pt(1)
        if line_dash:
            shp.line.dash_style = line_dash
    shp.shadow.inherit = False
    return shp


def add_text(slide, left, top, width, height, text, size, color, bold=False, italic=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=FONT_NAME, wrap=True):
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font
    return tb


def add_page_header(slide, page_no, title, subtitle):
    add_rect(slide, 0, 0, PAGE_W_IN, MARGIN + HEADER_H, COLOR_HEADER_BAND)
    add_text(slide, MARGIN, MARGIN - 0.05, 8.5, 0.4, f"P{page_no}. {title}", 20, COLOR_HEADER_TEXT, bold=True,
             anchor=MSO_ANCHOR.MIDDLE)
    add_text(slide, MARGIN, MARGIN + 0.32, 10.5, 0.3, subtitle, 11.5, RGBColor(0xC9, 0xD2, 0xE8), italic=True,
             anchor=MSO_ANCHOR.MIDDLE)


def add_page_footer(slide, note):
    top = PAGE_H_IN - MARGIN - FOOTER_H
    add_text(slide, MARGIN, top, CONTENT_W, FOOTER_H, note, 8.5, COLOR_FOOTER_TEXT, italic=True,
             anchor=MSO_ANCHOR.MIDDLE)


def add_card(slide, left, top, width, height, kind, title, subtitle=None, body_hint=None, pending=False,
             accent=False, page_record=None, visual_id=None):
    """Cartao/placeholder generico. kind: 'kpi' | 'chart' | 'banner' | 'filter' | 'text'."""
    if pending:
        fill, border, text_color = COLOR_PENDING_BG, COLOR_PENDING_BORDER, COLOR_PENDING_TEXT
    else:
        fill, border, text_color = COLOR_CARD_BG, COLOR_BORDER, COLOR_TEXT_DARK

    shp = add_rect(slide, left, top, width, height, fill, line_color=border)
    if pending:
        shp.line.width = Pt(1.75)  # borda mais espessa sinaliza "pendente de decisao"

    pad = 0.12
    title_color = COLOR_PENDING_TEXT if pending else COLOR_TEXT_DARK
    add_text(slide, left + pad, top + pad, width - 2 * pad, 0.3, title, 11.5, title_color, bold=True)

    y = top + pad + 0.32
    if subtitle:
        add_text(slide, left + pad, y, width - 2 * pad, 0.26, subtitle, 8.5, COLOR_TEXT_MUTED, italic=True)
        y += 0.28

    # area de conteudo (placeholder visual do grafico/kpi)
    inner_h = height - (y - top) - pad
    if inner_h > 0.15:
        tag = {"kpi": "[ valor — KPI do DAX ]", "chart": "[ area de grafico ]",
               "banner": "[ banner fixo ]", "filter": "[ slicer ]", "text": "[ bloco de texto ]"}.get(kind, "[ placeholder ]")
        if pending:
            tag = "[ RANKING DE PRODUTOS — criterio em definicao ]"
        inner_color = COLOR_PENDING_TEXT if pending else (COLOR_ACCENT_REAL if accent else COLOR_TEXT_MUTED)
        add_text(slide, left + pad, y, width - 2 * pad, inner_h, tag, 9, inner_color,
                  align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        if body_hint:
            add_text(slide, left + pad, top + height - pad - 0.22, width - 2 * pad, 0.22, body_hint, 7.5,
                      COLOR_TEXT_MUTED, italic=True)

    if page_record is not None:
        page_record["visuals"].append({
            "id": visual_id or title,
            "kind": kind,
            "title": title,
            "pending_decision": bool(pending),
            "position_in": {"left": round(left, 3), "top": round(top, 3), "width": round(width, 3), "height": round(height, 3)}
        })
    return shp


def add_warning_banner(slide, left, top, width, height, text, prominent=False, page_record=None):
    bg = COLOR_WARNING_BG
    shp = add_rect(slide, left, top, width, height, bg, line_color=RGBColor(0xC9, 0xA2, 0x27))
    add_text(slide, left + 0.15, top, width - 0.3, height, text,
              12 if prominent else 9, COLOR_WARNING_TEXT, bold=prominent, italic=not prominent,
              anchor=MSO_ANCHOR.MIDDLE)
    if page_record is not None:
        page_record["visuals"].append({"id": "warning_banner", "kind": "banner", "title": text,
                                        "pending_decision": False,
                                        "position_in": {"left": round(left, 3), "top": round(top, 3),
                                                         "width": round(width, 3), "height": round(height, 3)}})
    return shp


def add_fixed_disclaimer(slide, left, top, width, height, text, page_record=None, visual_id="fixed_disclaimer"):
    """Nota/disclaimer fixa e NAO removivel por filtro, ancorada a um visual especifico
    (ex.: ranking de produtos). Estilo distinto do footer de pagina generico — borda solida,
    sempre visivel, nao depende de slicer."""
    shp = add_rect(slide, left, top, width, height, COLOR_WARNING_BG, line_color=RGBColor(0xC9, 0xA2, 0x27))
    add_text(slide, left + 0.15, top, width - 0.3, height, text, 8.5, COLOR_WARNING_TEXT, italic=True,
              anchor=MSO_ANCHOR.MIDDLE)
    if page_record is not None:
        page_record["visuals"].append({
            "id": visual_id, "kind": "fixed_disclaimer", "title": text, "pending_decision": False,
            "removable_by_filter": False,
            "position_in": {"left": round(left, 3), "top": round(top, 3), "width": round(width, 3), "height": round(height, 3)}
        })
    return shp


def add_filter_bar(slide, labels, page_record=None):
    top = CONTENT_TOP
    h = 0.34
    n = len(labels)
    gap = 0.12
    w = (CONTENT_W - (n - 1) * gap) / n
    for i, lab in enumerate(labels):
        left = CONTENT_LEFT + i * (w + gap)
        add_card(slide, left, top, w, h, "filter", lab, page_record=page_record, visual_id=f"filter_{i}")
    return top + h + 0.16


# ---------------------------------------------------------------------------
# Construcao do deck
# ---------------------------------------------------------------------------

def new_presentation():
    prs = Presentation()
    prs.slide_width = Inches(PAGE_W_IN)
    prs.slide_height = Inches(PAGE_H_IN)
    return prs


def blank_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, PAGE_W_IN, PAGE_H_IN, COLOR_BG)
    return slide


def build_page1_executive(prs):
    slide = blank_slide(prs)
    rec = {"page": 1, "name": "Executive Overview", "visuals": []}
    add_page_header(slide, 1, "Executive Overview", "Como estamos indo, no geral, contra a meta?")
    filt_bottom = add_filter_bar(slide, ["Periodo (mes-ano)", "Cliente", "Cidade", "Categoria de estabelecimento"], rec)

    top = filt_bottom
    kpi_h = 1.25
    kpi_w_cols = 3
    kpi_titles = [
        ("Total Revenue", "Receita Total (Jan-Nov/2024)", "grao: 1 valor por pedido"),
        ("Average Ticket", "Ticket Medio", None),
        ("Orders Count", "Pedidos no Periodo", None),
        ("Revenue vs Target", "Receita vs Meta (agregado)", "meta mensal constante"),
    ]
    for i, (vid, title, sub) in enumerate(kpi_titles):
        left, w = col_span(i * kpi_w_cols, kpi_w_cols)
        add_card(slide, left, top, w, kpi_h, "kpi", title, subtitle=sub, accent=True, page_record=rec, visual_id=vid)

    top2 = top + kpi_h + 0.18
    remaining_h = CONTENT_BOTTOM - top2 - 0.3
    left, w = col_span(0, 12)
    add_card(slide, left, top2, w, remaining_h, "chart", "Tendencia de Receita (mensal)",
             subtitle="ultimo ponto (novembro) com marcador de mes parcial", accent=True,
             page_record=rec, visual_id="monthly_revenue_trend")

    add_page_footer(slide, "Receita calculada por pedido unico (order_id); periodo jan-nov/2024, novembro parcial até dia 10.")
    layout_coordinates["pages"].append(rec)
    return slide


def build_page2_time(prs):
    slide = blank_slide(prs)
    rec = {"page": 2, "name": "Time Analysis", "visuals": []}
    add_page_header(slide, 2, "Time Analysis", "A receita esta crescendo, caindo ou estavel mes a mes?")
    filt_bottom = add_filter_bar(slide, ["Periodo (mes-ano)", "Cliente", "Cidade", "Categoria de estabelecimento"], rec)

    top = filt_bottom
    left, w = col_span(0, 8)
    h1 = 3.3
    add_card(slide, left, top, w, h1, "chart", "Receita Mensal / Pedidos por Mes (alternavel)",
             subtitle="Requisito de interatividade #1 — seletor de tipo de grafico (linha <-> coluna)",
             accent=True, page_record=rec, visual_id="toggle_revenue_orders_monthly")

    left2, w2 = col_span(8, 4)
    add_card(slide, left2, top, w2, h1, "chart", "YTD Revenue",
             subtitle="rotulo dinamico: 'YTD até [ultima data], mes corrente parcial'",
             accent=True, page_record=rec, visual_id="ytd_revenue")

    top2 = top + h1 + 0.18
    h2 = CONTENT_BOTTOM - top2
    left3, w3 = col_span(0, 12)
    add_card(slide, left3, top2, w3, h2, "chart", "Crescimento Mes a Mes (%)",
             subtitle="janeiro sem barra/N.A.; novembro com rotulo 'parcial' sobreposto",
             accent=True, page_record=rec, visual_id="mom_growth")

    add_page_footer(slide, "Novembro/2024 sinalizado como mes parcial (dados apenas até dia 10) em toda serie temporal.")
    layout_coordinates["pages"].append(rec)
    return slide


def build_page3_product(prs):
    slide = blank_slide(prs)
    rec = {"page": 3, "name": "Product Analysis", "visuals": []}
    add_page_header(slide, 3, "Product Analysis", "O que estamos vendendo mais (em volume de pedidos)?")
    filt_bottom = add_filter_bar(slide, ["Periodo (mes-ano)", "Cliente", "Cidade", "Categoria de estabelecimento"], rec)

    top = filt_bottom
    left, w = col_span(0, 6)
    h1 = 3.5
    disclaimer_h = 0.3
    ranking_h = h1 - disclaimer_h - 0.08
    # PENDENTE: placeholder generico, sem assumir frequencia vs receita
    add_card(slide, left, top, w, ranking_h, "chart", "Ranking de Produtos (criterio em definicao)",
             subtitle="PENDENTE Analytics Architect: frequencia em pedidos vs receita via rateio — nao assumir eixo final",
             pending=True, page_record=rec, visual_id="top5_products_PENDING")
    # Disclaimer fixo e NAO removivel, reservado especificamente para o visual de ranking de
    # produtos — texto final cabe ao Analytics Architect; aqui so reserva-se a area.
    add_fixed_disclaimer(slide, left, top + ranking_h + 0.08, w, disclaimer_h,
        "[reservado p/ Analytics] Receita nao e rastreavel por produto individual nos dados brutos — "
        "ranking e por frequencia em pedidos, nao por valor.",
        page_record=rec, visual_id="top5_products_disclaimer")

    left2, w2 = col_span(6, 6)
    add_card(slide, left2, top, w2, h1, "chart", "Linhas de Pedido por Categoria de Bebida",
             subtitle="bucket 'Categoria nao informada' sempre visivel quando > 0; nunca moeda",
             accent=True, page_record=rec, visual_id="order_lines_by_category")

    top2 = top + h1 + 0.18
    h2 = CONTENT_BOTTOM - top2
    left3, w3 = col_span(0, 5)
    add_card(slide, left3, top2, w3, h2, "kpi", "Produtos no Catalogo sem Venda no Periodo",
             subtitle="contexto de catalogo, nao alarme (138/314)", page_record=rec, visual_id="unsold_products")

    left4, w4 = col_span(5, 7)
    add_warning_banner(slide, left4, top2, w4, h2,
        "Nao ha receita por produto nos dados de origem — metricas desta pagina medem "
        "frequencia/presenca em pedidos, nao valor monetario.", prominent=False, page_record=rec)

    add_page_footer(slide, "Nenhum visual de frequencia em pedidos usa formatacao de moeda (R$) ou o termo 'receita' no titulo.")
    layout_coordinates["pages"].append(rec)
    return slide


def build_page4_customer(prs):
    slide = blank_slide(prs)
    rec = {"page": 4, "name": "Customer Analysis", "visuals": []}
    add_page_header(slide, 4, "Customer Analysis", "Quem sao nossos clientes e como performam vs meta?")

    # Banner proeminente no topo (antes dos filtros, conforme spec "nao no rodape")
    banner_h = 0.42
    add_warning_banner(slide, CONTENT_LEFT, CONTENT_TOP, CONTENT_W, banner_h,
        "Base de apenas 8 clientes — resultados nao sao estatisticamente representativos de um universo maior de clientes.",
        prominent=True, page_record=rec)

    filt_top = CONTENT_TOP + banner_h + 0.14
    old_top = CONTENT_TOP
    # reaproveita add_filter_bar fixando novo top temporariamente
    globals()["CONTENT_TOP"]  # no-op guard
    h = 0.34
    labels = ["Periodo (mes-ano)", "Cliente", "Cidade", "Categoria de estabelecimento"]
    n = len(labels)
    gap = 0.12
    wcol = (CONTENT_W - (n - 1) * gap) / n
    for i, lab in enumerate(labels):
        left = CONTENT_LEFT + i * (wcol + gap)
        add_card(slide, left, filt_top, wcol, h, "filter", lab, page_record=rec, visual_id=f"filter_{i}")

    top = filt_top + h + 0.16
    left, w = col_span(0, 7)
    h1 = 2.9
    add_card(slide, left, top, w, h1, "chart", "Receita por Cliente (R$ <-> %)",
             subtitle="Requisito de interatividade #2 — toggle 'Valores absolutos' / '% do total'",
             accent=True, page_record=rec, visual_id="revenue_by_customer_toggle")

    left2, w2 = col_span(7, 5)
    add_card(slide, left2, top, w2, h1, "chart", "Receita Realizada vs Meta",
             subtitle="barra agrupada ou bullet chart, por cliente", accent=True, page_record=rec,
             visual_id="revenue_vs_target_customer")

    top2 = top + h1 + 0.18
    h2 = CONTENT_BOTTOM - top2
    left3, w3 = col_span(0, 6)
    add_card(slide, left3, top2, w3, h2, "chart", "Receita por Tipo de Estabelecimento",
             accent=True, page_record=rec, visual_id="revenue_by_establishment_category")
    left4, w4 = col_span(6, 6)
    add_card(slide, left4, top2, w4, h2, "chart", "Receita por Cidade",
             subtitle="3 valores canonicos (De-Para); sem cidade -> 'Nao informado'",
             accent=True, page_record=rec, visual_id="revenue_by_city")

    add_page_footer(slide, "n=8 clientes — leitura nao generalizavel. Aviso fixo, nao removivel por filtro.")
    layout_coordinates["pages"].append(rec)
    return slide


def build_page5_conclusion(prs):
    slide = blank_slide(prs)
    rec = {"page": 5, "name": "Conclusion (hidden tab)", "visuals": [], "hidden": True}
    add_page_header(slide, 5, "Conclusion (aba oculta)", "Sintese textual — acessivel via botao discreto 'Ver notas metodologicas'")

    top = CONTENT_TOP
    h = (CONTENT_BOTTOM - top - 0.3) / 1
    left, w = col_span(0, 12)
    third = h / 3 - 0.1
    headings = [
        ("findings", "O que os numeros mostram", "principais achados — linka para paginas 1-4, sem numero novo"),
        ("methodology", "Como a receita foi calculada", "nota metodologica do grao de pedido (DISTINCT order_id)"),
        ("limitations", "Limitacoes dos dados", "8 ressalvas do EDA em linguagem executiva (n=8 clientes, nov. parcial, etc.)"),
    ]
    y = top
    for vid, title, sub in headings:
        add_card(slide, left, y, w, third, "text", title, subtitle=sub, page_record=rec, visual_id=vid)
        y += third + 0.15

    add_page_footer(slide, "Pagina oculta na navegacao padrao; nenhum numero aqui pode ser novo em relacao as paginas anteriores.")
    layout_coordinates["pages"].append(rec)
    return slide


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    prs = new_presentation()

    build_page1_executive(prs)
    build_page2_time(prs)
    build_page3_product(prs)
    build_page4_customer(prs)
    build_page5_conclusion(prs)

    pptx_path = os.path.join(base, "pptx", "dashboard_background.pptx")
    prs.save(pptx_path)
    print(f"PPTX salvo: {pptx_path}")

    coords_path = os.path.join(base, "layout_coordinates.json")
    with open(coords_path, "w", encoding="utf-8") as f:
        json.dump(layout_coordinates, f, ensure_ascii=False, indent=2)
    print(f"Coordenadas salvas: {coords_path}")

    return pptx_path


if __name__ == "__main__":
    main()
