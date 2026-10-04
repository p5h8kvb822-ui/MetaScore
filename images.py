import pathlib, io, hashlib, colorsys
import requests
from PIL import Image, ImageDraw, ImageFont
from rating import tier

OUT = pathlib.Path(__file__).resolve().parent / "out"
S = 1080  # image carrée 1:1
BG, CARD, TXT, SUB = (14, 20, 36), (26, 36, 62), (255, 255, 255), (150, 165, 195)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"}


def fr(x):
    """Nombre à la française : virgule décimale."""
    return str(x).replace(".", ",")


def _f(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _fit(d, text, path, size, max_w):
    """Réduit la taille de police jusqu'à ce que le texte tienne dans max_w."""
    while size > 16 and d.textlength(text, font=_f(path, size)) > max_w:
        size -= 2
    return _f(path, size)


def get_logo(team_id):
    """Logo du club (PNG). None si indisponible."""
    if not team_id:
        return None
    try:
        r = requests.get(f"https://api.sofascore.com/api/v1/team/{team_id}/image", headers=UA, timeout=20)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def _placeholder(d, name, cx, cy, r):
    """Écusson de remplacement : cercle coloré + initiales (si le logo est introuvable)."""
    hue = int(hashlib.md5(name.encode()).hexdigest()[:6], 16) % 360 / 360
    col = tuple(int(255 * v) for v in colorsys.hsv_to_rgb(hue, 0.6, 0.75))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col, outline=(255, 255, 255), width=5)
    words = name.split()
    txt = "".join(w[0] for w in words[:2]).upper() if len(words) > 1 else name[:3].upper()
    d.text((cx, cy), txt, font=_f(FB, 60), fill=TXT, anchor="mm")


def _crest(img, d, name, team_id, cx, cy, r, use_logos):
    logo = get_logo(team_id) if use_logos else None
    if logo:
        logo.thumbnail((2 * r, 2 * r))
        img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
    else:
        _placeholder(d, name, cx, cy, r)


def match_card(m, date_str, path, use_logos=False):
    """Une image 1080x1080 par match : logos, score, note colorée, 4 stats clés."""
    OUT.mkdir(exist_ok=True)
    _, color, _ = tier(m["rating"])
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S, 14], fill=color)
    d.text((60, 62), f'{m["league"].upper()} · {date_str}', font=_f(FB, 28), fill=SUB)
    d.text((S - 60, 62), "TERMINÉ", font=_f(FB, 28), fill=SUB, anchor="ra")

    cy = 300
    _crest(img, d, m["home"], m.get("home_id"), 235, cy, 105, use_logos)
    _crest(img, d, m["away"], m.get("away_id"), 845, cy, 105, use_logos)
    d.text((540, cy), f'{m["score_home"]} - {m["score_away"]}', font=_f(FB, 120), fill=TXT, anchor="mm")
    d.text((235, 455), m["home"], font=_fit(d, m["home"], FB, 40, 420), fill=TXT, anchor="mm")
    d.text((845, 455), m["away"], font=_fit(d, m["away"], FB, 40, 420), fill=TXT, anchor="mm")

    # pastille de note (couleur selon le palier)
    d.rounded_rectangle([280, 535, 800, 655], 60, fill=color)
    lum = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    d.text((540, 595), f'{fr(m["rating"])}/10', font=_f(FB, 88), fill=BG if lum > 140 else TXT, anchor="mm")

    # statistiques clés : grille 2x2
    stats = []
    if m.get("xg_home") is not None:
        stats.append(("xG", f'{fr(m["xg_home"])} – {fr(m["xg_away"])}'))
    if m.get("sot_home") is not None:
        stats.append(("TIRS CADRÉS", f'{m["sot_home"]} – {m["sot_away"]}'))
    if m.get("big_home") is not None:
        stats.append(("GROSSES OCCASIONS", f'{m["big_home"]} – {m["big_away"]}'))
    if m.get("poss_home") is not None:
        stats.append(("POSSESSION", f'{round(m["poss_home"])}% – {round(m["poss_away"])}%'))
    for i, (lab, val) in enumerate(stats[:4]):
        x0 = 60 if i % 2 == 0 else 555
        y0 = 725 if i < 2 else 855
        d.rounded_rectangle([x0, y0, x0 + 465, y0 + 115], 22, fill=CARD)
        d.text((x0 + 232, y0 + 32), lab, font=_f(FR, 22), fill=SUB, anchor="mm")
        d.text((x0 + 232, y0 + 77), val, font=_f(FB, 40), fill=TXT, anchor="mm")
    p = OUT / path
    img.save(p)
    return str(p)
