"""Renderiza PNGs de alta resolucao (overview.png = Executive Overview, detail.png =
Product Analysis) a partir de design/layout_coordinates.json, usando Pillow.

Motivo: sem LibreOffice/PowerPoint disponivel no ambiente para exportar o PPTX
diretamente, este script redesenha o mesmo grid/paleta em PNG para entregar os
exports solicitados. O PPTX real e a fonte editavel e a fonte da verdade visual:
design/pptx/ABInBev_dashboard_background.pptx (editado manualmente pelo usuario,
substitui o antigo dashboard_background.pptx gerado por build_dashboard_backgrounds.py).
Este PNG e so para conferencia visual rapida / aproximacao, nao um render exato do
PowerPoint.

Atualizado em 2026-10-02 para refletir canvas 20x11.25in e a paleta real extraida do
pptx do usuario (preto/dourado, nao mais azul-marinho/azul).
"""
import json
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SCALE = 96  # px per inch -> 1920x1080 @ 20x11.25in

COLOR_BG = (0xF5, 0xF6, 0xF8)
COLOR_CARD_BG = (0xFF, 0xFF, 0xFF)
COLOR_BORDER = (0xE2, 0xDF, 0xD8)
COLOR_TEXT_DARK = (0x14, 0x14, 0x14)
COLOR_TEXT_MUTED = (0x6B, 0x67, 0x60)
COLOR_ACCENT_REAL = (0xE5, 0xB6, 0x11)
COLOR_HEADER_BAND = (0x00, 0x00, 0x00)
COLOR_HEADER_TEXT = (0xFF, 0xFF, 0xFF)
COLOR_HEADER_SUBTEXT = (0xE9, 0xC9, 0x5A)
COLOR_WARNING_BG = (0xFF, 0xF7, 0xD9)
COLOR_WARNING_BORDER = (0xE5, 0xB6, 0x11)
COLOR_WARNING_TEXT = (0x5C, 0x4A, 0x12)
COLOR_PENDING_BG = (0xEE, 0xED, 0xEA)
COLOR_PENDING_BORDER = (0x9A, 0x9A, 0x9A)
COLOR_PENDING_TEXT = (0x55, 0x52, 0x4C)
COLOR_PLACEHOLDER_TAG = (0xA8, 0xA3, 0x98)


def font(size, bold=False):
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def in2px(v):
    return int(round(v * SCALE))


def draw_page(page_rec, canvas, out_path):
    W = in2px(canvas["width"])
    H = in2px(canvas["height"])
    img = Image.new("RGB", (W, H), COLOR_BG)
    d = ImageDraw.Draw(img)

    margin = 0.5
    header_h = 1.25
    # header band (preto) + linha de acento dourado
    d.rectangle([0, 0, W, in2px(header_h)], fill=COLOR_HEADER_BAND)
    d.rectangle([0, in2px(1.208), W, in2px(1.25)], fill=COLOR_ACCENT_REAL)
    title = f"P{page_rec['page']}. {page_rec['name']}"
    d.text((in2px(margin), in2px(0.235)), title, font=font(30, bold=True), fill=COLOR_HEADER_TEXT)

    for v in page_rec["visuals"]:
        pos = v.get("position_in")
        if not pos:
            continue
        l, t, w, h = in2px(pos["left"]), in2px(pos["top"]), in2px(pos["width"]), in2px(pos["height"])
        kind = v["kind"]
        pending = v.get("pending_decision", False)
        title_txt = v.get("title") or v.get("title_in_pptx", "")

        if kind in ("header", "divider", "image"):
            continue  # ja desenhado / fora de escopo deste approx.

        if kind == "filter":
            d.rectangle([l, t, l + w, t + h], fill=COLOR_CARD_BG, outline=COLOR_BORDER, width=1)
            d.text((l + 16, t + h // 2 - 10), title_txt, font=font(14, bold=True), fill=COLOR_TEXT_DARK)
            continue

        if kind == "banner":
            fill = tuple(int(v.get("fill", "#FFF7D9")[i:i+2], 16) for i in (1, 3, 5)) if v.get("fill") else COLOR_WARNING_BG
            d.rectangle([l, t, l + w, t + h], fill=fill, outline=COLOR_WARNING_BORDER, width=2)
            d.text((l + 16, t + 16), title_txt[:220], font=font(16), fill=COLOR_WARNING_TEXT)
            continue
        if kind == "fixed_disclaimer":
            d.rectangle([l, t, l + w, t + h], fill=COLOR_WARNING_BG, outline=COLOR_WARNING_BORDER, width=2)
            d.text((l + 10, t + h // 2 - 9), title_txt[:200], font=font(12), fill=COLOR_WARNING_TEXT)
            continue

        if pending:
            fill, border, textc = COLOR_PENDING_BG, COLOR_PENDING_BORDER, COLOR_PENDING_TEXT
            width_line = 3
        else:
            fill, border, textc = COLOR_CARD_BG, COLOR_BORDER, COLOR_TEXT_DARK
            width_line = 1

        d.rectangle([l, t, l + w, t + h], fill=fill, outline=border, width=width_line)
        # acento dourado no topo do cartao (igual aos cartoes KPI do pptx real), exceto pendente
        if not pending and kind == "kpi":
            d.rectangle([l, t, l + w, t + in2px(0.042)], fill=COLOR_ACCENT_REAL)
        d.text((l + 18, t + 16), title_txt, font=font(17, bold=True), fill=textc)

        subtitle = v.get("subtitle")
        y_sub = t + 44
        if subtitle:
            d.text((l + 18, y_sub), subtitle[:160], font=font(12), fill=COLOR_TEXT_MUTED)
            y_sub += 22

        tag = {"kpi": "[ valor - KPI do DAX ]", "chart": "[ area de grafico ]",
               "text": "[ bloco de texto ]"}.get(kind, "[ placeholder ]")
        if pending:
            tag = "[ RANKING DE PRODUTOS - criterio em definicao ]"
        tw = d.textlength(tag, font=font(13))
        d.text((l + w / 2 - tw / 2, t + h / 2), tag, font=font(13), fill=(COLOR_PENDING_TEXT if pending else COLOR_PLACEHOLDER_TAG))

    footer = page_rec.get("footer_note")
    if footer:
        d.text((in2px(margin), in2px(10.583)), footer, font=font(13, bold=False), fill=(0x8A, 0x86, 0x7E))

    img.save(out_path, "PNG")
    print(f"PNG salvo: {out_path} ({W}x{H})")


def main():
    with open(os.path.join(BASE, "layout_coordinates.json"), "r", encoding="utf-8") as f:
        data = json.load(f)

    pages = {p["page"]: p for p in data["pages"]}
    exports_dir = os.path.join(BASE, "exports")
    os.makedirs(exports_dir, exist_ok=True)

    draw_page(pages[1], data["canvas"], os.path.join(exports_dir, "overview.png"))
    draw_page(pages[3], data["canvas"], os.path.join(exports_dir, "detail.png"))


if __name__ == "__main__":
    main()
