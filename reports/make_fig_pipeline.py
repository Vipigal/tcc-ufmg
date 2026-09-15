#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gera a figura da pipeline como infográfico editorial em SVG -> PDF vetorial
(para o LaTeX) e PNG (inspeção).

Conceito: NÃO mostra os 7 passos, e sim a MUDANÇA DA ESTRUTURA DO DADO, em
cinco estados, da tabela bruta ao grafo de comunidades. Os detalhes de
implementação ficam como anotações sobre as setas (operações entre estados).

Estilo "nativo do TCC": cards/medalhões claros, line-art monocromático e um
único acento crimson (#D7263D, da paleta dos grafos) no estado final.

Variantes geradas (para comparação):
  A  boxed     + faixa de título   (linha)        — horizontal
  B  medallion + faixa de título   (ícone cheio)  — horizontal
  C  boxed     SEM faixa de título (linha)        — horizontal, mais compacto
  D  vertical timeline (linha)                    — 1 coluna

Paleta herdada de modules/layout.py e modules/results.py.
"""
import cairosvg
from PIL import Image, ImageFont

SCRATCH = ("/tmp/claude-1000/-home-vinicius-tcc/"
           "58029b9c-baac-472c-99d4-b0c535afae3b/scratchpad")

# ---- paleta (mesma das demais figuras do trabalho) -------------------------
INK   = "#14172A"
MUTED = "#3a4055"
RULE  = "#d4d8e0"
GREY  = "#c7ccd6"
WHITE = "#FFFFFF"
C_PUR, C_TEAL, C_ORA, C_CRI, C_BLU = "#5E4FA2", "#26A69A", "#E8852B", "#D7263D", "#3C6E9E"
ACCENT = C_CRI
MED_FILL, MED_FINAL = "#EEF1F6", "#FBE9EC"      # preenchimento dos medalhões

FONT = "Helvetica, Arial, 'DejaVu Sans', sans-serif"
_FP = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def _w(s, size):
    try:
        return ImageFont.truetype(_FP, max(1, int(round(size)))).getlength(s)
    except Exception:
        return len(s) * size * 0.52


# ---- conteúdo --------------------------------------------------------------
TITLES = ["Arquivos CSV", "Matriz bipartida B", "Grafo de co-retweet",
          "Backbone", "Comunidades"]
SUBS = ["author_id · referenced_tweets", "usuários U × tweets T",
        "denso · peso = Jaccard", "esparso · J ≥ τ", "partição de Leiden"]
ANN = [("carga + filtro", ["type = retweeted", "usuários ≥ N"]),
       ("projeção", ["Jaccard · B·B^T", "em blocos"]),
       ("backbone", ["corte", "τ = 0,1"]),
       ("Leiden", ["maximiza Q", "+ métricas"])]


# ---- helpers de texto ------------------------------------------------------
def text(x, y, s, size, color, weight="normal", anchor="middle", spacing=None):
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{color}" font-weight="{weight}" text-anchor="{anchor}"{sp}>{s}</text>')


def text_sup(x, y, ln, size, color, anchor):
    """linha de detalhe com 'T' sobrescrito ('^T'). cairosvg só posiciona o
    tspan dy sob anchor='start', então centralizo medindo a largura."""
    if "^T" not in ln:
        return text(x, y, ln, size, color, anchor=anchor)
    pre = ln.split("^T")[0]
    if anchor == "middle":
        x = x - (_w(pre, size) + _w("T", size * 0.85)) / 2
    body = f'{pre}<tspan font-size="{size*0.85:.1f}" dy="-5">T</tspan>'
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" '
            f'fill="{color}" text-anchor="start">{body}</text>')


def ann_block(x, kw_y, line_ys, idx, anchor="middle"):
    kw, lines = ANN[idx]
    out = [text(x, kw_y, kw, 11.5, INK, weight="bold", anchor=anchor)]
    for ln, yy in zip(lines, line_ys):
        out.append(text_sup(x, yy, ln, 10, MUTED, anchor))
    return "\n".join(out)


# ---- ícones (line-art, centro em cx,cy) ------------------------------------
def icon_csv(cx, cy):
    s = [f'<rect x="{cx-20:.1f}" y="{cy-24:.1f}" width="36" height="46" rx="4" '
         f'fill="{WHITE}" stroke="{RULE}" stroke-width="1.5"/>']
    fx, fy, fw, fh = cx - 10, cy - 16, 36, 46
    s.append(f'<path d="M{fx:.1f},{fy:.1f} h{fw-9} l9,9 v{fh-9} h-{fw} z" '
             f'fill="{WHITE}" stroke="{INK}" stroke-width="1.7" stroke-linejoin="round"/>')
    s.append(f'<path d="M{fx+fw-9:.1f},{fy:.1f} v9 h9" fill="none" stroke="{INK}" '
             f'stroke-width="1.5" stroke-linejoin="round"/>')
    s.append(f'<rect x="{fx+5:.1f}" y="{fy+8:.1f}" width="{fw-10}" height="7" '
             f'fill="{INK}" opacity="0.12"/>')
    for k in range(3):
        yy = fy + 22 + k * 7
        s.append(f'<line x1="{fx+5:.1f}" y1="{yy:.1f}" x2="{fx+fw-5:.1f}" y2="{yy:.1f}" '
                 f'stroke="{INK}" stroke-width="1.2" opacity="0.55"/>')
    s.append(f'<line x1="{fx+fw*0.5:.1f}" y1="{fy+18:.1f}" x2="{fx+fw*0.5:.1f}" '
             f'y2="{fy+fh-6:.1f}" stroke="{INK}" stroke-width="1.1" opacity="0.45"/>')
    return "\n".join(s)


def icon_bipartite(cx, cy):
    s, lx, rx = [], cx - 20, cx + 20
    ys = [cy - 22, cy, cy + 22]
    for a, b in [(0, 0), (0, 1), (1, 0), (1, 2), (2, 1), (2, 2)]:
        s.append(f'<line x1="{lx:.1f}" y1="{ys[a]:.1f}" x2="{rx:.1f}" y2="{ys[b]:.1f}" '
                 f'stroke="{INK}" stroke-width="1.1" opacity="0.5"/>')
    for y in ys:
        s.append(f'<circle cx="{lx:.1f}" cy="{y:.1f}" r="5" fill="{INK}"/>')
    for y in ys:
        s.append(f'<circle cx="{rx:.1f}" cy="{y:.1f}" r="5" fill="{WHITE}" '
                 f'stroke="{INK}" stroke-width="1.6"/>')
    return "\n".join(s)


def _ring(cx, cy, r, n, start=-90):
    import math
    return [(cx + r * math.cos(math.radians(start + i * 360 / n)),
             cy + r * math.sin(math.radians(start + i * 360 / n))) for i in range(n)]


def icon_hairball(cx, cy):
    s, pts = [], _ring(cx, cy, 26, 6) + [(cx, cy)]
    edges = [(6, i) for i in range(6)] + [(0, 2), (0, 3), (1, 3), (1, 4),
             (2, 4), (2, 5), (3, 5), (0, 4), (1, 5)]
    for a, b in edges:
        s.append(f'<line x1="{pts[a][0]:.1f}" y1="{pts[a][1]:.1f}" '
                 f'x2="{pts[b][0]:.1f}" y2="{pts[b][1]:.1f}" '
                 f'stroke="{INK}" stroke-width="1" opacity="0.32"/>')
    for x, y in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{INK}"/>')
    return "\n".join(s)


def icon_backbone(cx, cy):
    s, pts = [], _ring(cx, cy, 26, 6) + [(cx, cy)]
    removed = [(0, 2), (0, 3), (1, 3), (2, 4), (2, 5), (0, 4), (1, 5), (6, 1), (6, 4)]
    kept = [(6, 0), (6, 2), (6, 3), (6, 5), (1, 4)]
    for a, b in removed:
        s.append(f'<line x1="{pts[a][0]:.1f}" y1="{pts[a][1]:.1f}" '
                 f'x2="{pts[b][0]:.1f}" y2="{pts[b][1]:.1f}" '
                 f'stroke="{RULE}" stroke-width="1" stroke-dasharray="2.5 2.5" opacity="0.9"/>')
    for a, b in kept:
        s.append(f'<line x1="{pts[a][0]:.1f}" y1="{pts[a][1]:.1f}" '
                 f'x2="{pts[b][0]:.1f}" y2="{pts[b][1]:.1f}" '
                 f'stroke="{INK}" stroke-width="2"/>')
    for x, y in pts:
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.6" fill="{INK}"/>')
    return "\n".join(s)


def icon_communities(cx, cy):
    s = []
    clusters = [
        (C_PUR,  [(cx - 24, cy - 18), (cx - 14, cy - 6), (cx - 28, cy - 3)]),
        (C_TEAL, [(cx - 4, cy + 20), (cx + 8, cy + 14), (cx - 8, cy + 8)]),
        (C_CRI,  [(cx + 22, cy - 16), (cx + 26, cy - 3), (cx + 14, cy - 10)]),
    ]
    for col, nodes in clusters:
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                s.append(f'<line x1="{nodes[i][0]:.1f}" y1="{nodes[i][1]:.1f}" '
                         f'x2="{nodes[j][0]:.1f}" y2="{nodes[j][1]:.1f}" '
                         f'stroke="{col}" stroke-width="1.4" opacity="0.55"/>')
    for a, b in [(clusters[0][1][1], clusters[1][1][2]),
                 (clusters[1][1][1], clusters[2][1][2])]:
        s.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                 f'stroke="{GREY}" stroke-width="1" opacity="0.7"/>')
    for col, nodes in clusters:
        for x, y in nodes:
            s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4.6" fill="{col}"/>')
    return "\n".join(s)


ICONS = [icon_csv, icon_bipartite, icon_hairball, icon_backbone, icon_communities]


def icon_scaled(i, cx, cy, s):
    if abs(s - 1.0) < 1e-3:
        return ICONS[i](cx, cy)
    return (f'<g transform="translate({cx:.1f},{cy:.1f}) scale({s}) '
            f'translate({-cx:.1f},{-cy:.1f})">{ICONS[i](cx, cy)}</g>')


def _svg(w, h, body):
    defs = (f'<defs><marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" '
            f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0.5,1 L9,5 L0.5,9" fill="none" stroke="{INK}" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'
            f'</marker></defs>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{WHITE}"/>'
            f'{defs}\n{body}\n</svg>')


# ---- HORIZONTAL ------------------------------------------------------------
def build_h(mode="boxed", title_band=True):
    W = 1200
    MARGIN, CARD_W = 28, 150
    N = 5
    GAP = (W - 2 * MARGIN - N * CARD_W) / (N - 1)
    X = [MARGIN + i * (CARD_W + GAP) for i in range(N)]
    cx = [x + CARD_W / 2 for x in X]
    top = 70 if title_band else 30
    o = []

    if title_band:
        o.append(text(MARGIN, 34, "CONSTRUÇÃO DA REDE DE CO-RETWEET", 11.5, MUTED,
                      weight="bold", anchor="start", spacing="1.6"))
        o.append(text(W - MARGIN, 34, "da tabela ao grafo", 11.5, MUTED, anchor="end"))
        o.append(f'<line x1="{MARGIN}" y1="46" x2="{W-MARGIN}" y2="46" '
                 f'stroke="{RULE}" stroke-width="1.2"/>')

    if mode == "boxed":
        CARD_H = 150
        icy = top + 46
        rule_y, title_y, sub_y = top + 88, top + 112, top + 131
        arrow_y = icy + 26
        kw_y, l1, l2 = top + 16, top + 31, top + 44
        H = top + CARD_H + 30
        arrow_pad = 8
    else:  # medallion (sem caixa)
        MR = 36
        icy = top + 42
        title_y, sub_y = top + 96, top + 114
        arrow_y = icy
        kw_y, l1, l2 = top - 8, top + 5, top + 18
        H = sub_y + 22
        arrow_pad = MR + 6

    # setas + anotações
    for i in range(N - 1):
        x1, x2 = (X[i] + CARD_W + arrow_pad if mode == "boxed" else cx[i] + arrow_pad), \
                 (X[i + 1] - arrow_pad if mode == "boxed" else cx[i + 1] - arrow_pad)
        o.append(f'<line x1="{x1:.1f}" y1="{arrow_y:.1f}" x2="{x2:.1f}" y2="{arrow_y:.1f}" '
                 f'stroke="{INK}" stroke-width="1.5" marker-end="url(#ah)"/>')
        o.append(ann_block((x1 + x2) / 2, kw_y, (l1, l2), i))

    # nós
    for i in range(N):
        final = (i == N - 1)
        if mode == "boxed":
            border = ACCENT if final else RULE
            o.append(f'<rect x="{X[i]:.1f}" y="{top}" width="{CARD_W}" height="{CARD_H}" '
                     f'rx="10" fill="{WHITE}" stroke="{border}" '
                     f'stroke-width="{1.8 if final else 1.3}"/>')
            if final:
                o.append(f'<path d="M{X[i]+10:.1f},{top} h{CARD_W-20} a10,10 0 0 1 10,10 '
                         f'v6 h-{CARD_W} v-6 a10,10 0 0 1 10,-10 z" fill="{ACCENT}" opacity="0.10"/>')
            o.append(icon_scaled(i, cx[i], icy, 1.0))
            o.append(f'<line x1="{X[i]+16:.1f}" y1="{rule_y}" x2="{X[i]+CARD_W-16:.1f}" '
                     f'y2="{rule_y}" stroke="{RULE}" stroke-width="1"/>')
        else:  # medallion
            o.append(f'<circle cx="{cx[i]:.1f}" cy="{icy:.1f}" r="{MR}" '
                     f'fill="{MED_FINAL if final else MED_FILL}" '
                     f'stroke="{ACCENT if final else RULE}" '
                     f'stroke-width="{1.8 if final else 1.2}"/>')
            o.append(icon_scaled(i, cx[i], icy, 0.82))
        o.append(text(cx[i], title_y, TITLES[i], 13.5, ACCENT if final else INK, weight="bold"))
        o.append(text(cx[i], sub_y, SUBS[i], 9.8, MUTED))

    return _svg(W, H, "\n".join(o))


# ---- VERTICAL (timeline, 1 coluna) -----------------------------------------
def build_v():
    W = 470
    spine, tx = 70, 112
    N = 5
    ys = [56 + i * 122 for i in range(N)]
    DR = 26
    H = ys[-1] + DR + 30
    o = [text(spine - DR, 28, "DA TABELA AO GRAFO", 11, MUTED, weight="bold",
              anchor="start", spacing="1.4")]
    o.append(f'<line x1="{spine-DR}" y1="38" x2="{W-24}" y2="38" stroke="{RULE}" stroke-width="1.2"/>')

    # conectores verticais + anotações
    for i in range(N - 1):
        y1, y2 = ys[i] + DR + 2, ys[i + 1] - DR - 2
        o.append(f'<line x1="{spine:.1f}" y1="{y1:.1f}" x2="{spine:.1f}" y2="{y2:.1f}" '
                 f'stroke="{INK}" stroke-width="1.5" marker-end="url(#ah)"/>')
        ymid = (y1 + y2) / 2
        o.append(ann_block(tx, ymid - 9, (ymid + 5, ymid + 18), i, anchor="start"))

    # nós
    for i in range(N):
        final = (i == N - 1)
        o.append(f'<circle cx="{spine:.1f}" cy="{ys[i]:.1f}" r="{DR}" '
                 f'fill="{MED_FINAL if final else MED_FILL}" '
                 f'stroke="{ACCENT if final else RULE}" stroke-width="{1.8 if final else 1.2}"/>')
        o.append(icon_scaled(i, spine, ys[i], 0.6))
        o.append(text(tx, ys[i] - 3, TITLES[i], 13.5, ACCENT if final else INK,
                      weight="bold", anchor="start"))
        o.append(text(tx, ys[i] + 14, SUBS[i], 9.8, MUTED, anchor="start"))
    return _svg(W, H, "\n".join(o))


# ---- render + contact sheet ------------------------------------------------
VARIANTS = {
    "A_boxed_titulo":      lambda: build_h("boxed", True),
    "B_medalhao_titulo":   lambda: build_h("medallion", True),
    "C_boxed_sem_titulo":  lambda: build_h("boxed", False),
    "D_vertical":          lambda: build_v(),
}

if __name__ == "__main__":
    pngs = {}
    for name, fn in VARIANTS.items():
        svg = fn()
        open(f"{SCRATCH}/pipe_{name}.svg", "w").write(svg)
        png = f"{SCRATCH}/pipe_{name}.png"
        cairosvg.svg2png(bytestring=svg.encode(), write_to=png, output_width=1800)
        pngs[name] = png
        print("ok", name)

    # também grava a variante A como o candidato vetorial padrão p/ o LaTeX
    cairosvg.svg2pdf(bytestring=build_h("boxed", True).encode(),
                     write_to="reports/fig_pipeline_v2.pdf")

    # contact sheet: A,B,C empilhadas (col. esq.) + D (col. dir.)
    ims = {k: Image.open(v).convert("RGB") for k, v in pngs.items()}
    pad, label_h, colw = 30, 34, 1180
    def scaled(im, w):
        return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    left = [scaled(ims[k], colw) for k in ["A_boxed_titulo", "B_medalhao_titulo", "C_boxed_sem_titulo"]]
    dimg = scaled(ims["D_vertical"], 360)
    left_h = sum(im.height + label_h + pad for im in left)
    right_h = dimg.height + label_h
    H = max(left_h, right_h) + pad
    Wc = pad + colw + pad + dimg.width + pad
    sheet = Image.new("RGB", (Wc, H), "white")
    try:
        f = ImageFont.truetype(_FP, 22); fb = ImageFont.truetype(_FP.replace("DejaVuSans", "DejaVuSans-Bold"), 22)
    except Exception:
        f = fb = ImageFont.load_default()
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    labels = {"A_boxed_titulo": "A — cards + faixa de título (linha)",
              "B_medalhao_titulo": "B — medalhões + faixa de título (ícone cheio)",
              "C_boxed_sem_titulo": "C — cards SEM faixa de título (mais compacto)",
              "D_vertical": "D — timeline vertical (1 coluna)"}
    y = pad
    for k, im in zip(["A_boxed_titulo", "B_medalhao_titulo", "C_boxed_sem_titulo"], left):
        d.text((pad, y), labels[k], fill="#14172A", font=fb); y += label_h
        sheet.paste(im, (pad, y)); y += im.height + pad
    xr = pad + colw + pad
    d.text((xr, pad), labels["D_vertical"], fill="#14172A", font=fb)
    sheet.paste(dimg, (xr, pad + label_h))
    sheet.save("reports/fig_pipeline_variacoes.png")
    print("wrote reports/fig_pipeline_variacoes.png + reports/fig_pipeline_v2.pdf")
