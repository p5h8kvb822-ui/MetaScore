import pathlib, io, hashlib, colorsys
import requests
from PIL import Image, ImageDraw, ImageFont
from rating import tier

OUT = pathlib.Path(__file__).resolve().parent / "out"
S = 1080  # image carrée 1:1
LOGO_PATH = pathlib.Path(__file__).resolve().parent / "logo.png"
LOGO_H = 130
BG, CARD, TXT, SUB = (14, 20, 36), (26, 36, 62), (255, 255, 255), (150, 165, 195)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"}


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _lum(rgb):
    return 0.2126 * _lin(rgb[0]) + 0.7152 * _lin(rgb[1]) + 0.0722 * _lin(rgb[2])


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _mix(a, b, t):
    return tuple(round(a[i] * (1 - t) + b[i] * t) for i in range(3))


def make_theme(bg_hex):
    """Choisit texte blanc ou foncé selon le meilleur contraste avec le fond, puis dérive
    le texte secondaire (contraste >= 4,5 si possible) et la couleur des cartes."""
    h = bg_hex.lstrip("#")
    bg = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    white, dark = (255, 255, 255), (14, 20, 36)
    txt = white if contrast(bg, white) >= contrast(bg, dark) else dark
    # cartes : on s'éloigne du fond tant que le texte secondaire reste lisible dessus
    best = None
    for k in (0.12, 0.10, 0.08, 0.06):
        card = _mix(bg, txt, k)
        for t in (0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0):
            sub = _mix(txt, bg, t)
            if contrast(sub, bg) >= 4.5 and contrast(sub, card) >= 4.5:
                best = (card, sub)
                break
        if best:
            break
    card, sub = best if best else (_mix(bg, txt, 0.06), txt)
    return bg, card, txt, sub


ORIGINAL = ((14, 20, 36), (26, 36, 62), (255, 255, 255), (150, 165, 195))
THEMED = False


def _apply_theme(bg_hex=None):
    """Sans couleur demandée : fond bleu nuit d'origine. (make_theme reste disponible si besoin.)"""
    global BG, CARD, TXT, SUB, THEMED
    if bg_hex:
        BG, CARD, TXT, SUB = make_theme(bg_hex)
        THEMED = True
    else:
        BG, CARD, TXT, SUB = ORIGINAL
        THEMED = False


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


def get_logo(url):
    """Logo du club (image à partir de son adresse). None si indisponible."""
    if not url:
        return None
    try:
        r = requests.get(url, headers=UA, timeout=20)
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
    d.text((cx, cy), txt, font=_f(FB, 60), fill=(255, 255, 255), anchor="mm")


def _paste_logo(img, height=None):
    """Ton logo (logo.png, fond transparent) centré en bas de l'image. Ignoré si le fichier est absent."""
    if not LOGO_PATH.exists():
        return
    logo = Image.open(LOGO_PATH).convert("RGBA")
    h = height or LOGO_H
    w = round(logo.width * h / logo.height)
    logo = logo.resize((w, h), Image.LANCZOS)
    img.paste(logo, ((S - w) // 2, S - h - 28), logo)


def _crest(img, d, name, team_id, cx, cy, r, use_logos):
    logo = get_logo(team_id) if use_logos else None
    if logo:
        logo.thumbnail((2 * r, 2 * r))
        img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
    else:
        _placeholder(d, name, cx, cy, r)


def match_card(m, date_str, path, use_logos=False, bg=None):
    """Une image 1080x1080 par match : logos, score, note colorée, 4 stats clés."""
    OUT.mkdir(exist_ok=True)
    _apply_theme(bg)
    _, color, _ = tier(m["rating"])
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S, 14], fill=color)
    d.text((60, 62), f'{m["league"].upper()} · {date_str}', font=_f(FB, 28), fill=SUB)
    d.text((S - 60, 62), "TERMINÉ", font=_f(FB, 28), fill=SUB, anchor="ra")

    cy = 285
    _crest(img, d, m["home"], m.get("home_logo"), 235, cy, 105, use_logos)
    _crest(img, d, m["away"], m.get("away_logo"), 845, cy, 105, use_logos)
    d.text((540, cy), f'{m["score_home"]} - {m["score_away"]}', font=_f(FB, 120), fill=TXT, anchor="mm")
    d.text((235, 440), m["home"], font=_fit(d, m["home"], FB, 40, 420), fill=TXT, anchor="mm")
    d.text((845, 440), m["away"], font=_fit(d, m["away"], FB, 40, 420), fill=TXT, anchor="mm")

    # pastille de note (couleur selon le palier)
    d.rounded_rectangle([350, 510, 730, 625], 57, fill=color, outline=TXT if THEMED else None, width=6)
    lum = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
    d.text((540, 568), fr(m["rating"]), font=_f(FB, 96), fill=(14, 20, 36) if lum > 140 else (255, 255, 255), anchor="mm")

    # statistiques clés : grille 2x2
    stats = []
    if m.get("xg_home") is not None:
        stats.append(("xG", f'{fr(m["xg_home"])} – {fr(m["xg_away"])}'))
    if m.get("sot_home") is not None:
        stats.append(("TIRS CADRÉS", f'{round(m["sot_home"])} – {round(m["sot_away"])}'))
    if m.get("shots_home") is not None:
        stats.append(("TIRS", f'{round(m["shots_home"])} – {round(m["shots_away"])}'))
    if m.get("poss_home") is not None:
        stats.append(("POSSESSION", f'{round(m["poss_home"])}% – {round(m["poss_away"])}%'))
    if m.get("corners_home") is not None:
        stats.append(("CORNERS", f'{round(m["corners_home"])} – {round(m["corners_away"])}'))
    for i, (lab, val) in enumerate(stats[:4]):
        x0 = 60 if i % 2 == 0 else 555
        y0 = 670 if i < 2 else 785
        d.rounded_rectangle([x0, y0, x0 + 465, y0 + 100], 22, fill=CARD)
        d.text((x0 + 232, y0 + 28), lab, font=_f(FR, 22), fill=SUB, anchor="mm")
        d.text((x0 + 232, y0 + 69), val, font=_f(FB, 38), fill=TXT, anchor="mm")
    _paste_logo(img)
    p = OUT / path
    img.save(p)
    return str(p)


# ------------------------------------------------------------------ 2e swipe : meilleur joueur
POS_FR = {"G": "Gardien", "D": "Défenseur", "M": "Milieu", "F": "Attaquant"}


def _num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def player_stat_lines(st):
    """Stats du match du joueur (structure API-Football) -> [(libellé, valeur)], non nulles seulement."""
    out = []

    def g(sec, key):
        v = (st.get(sec) or {}).get(key)
        try:
            return float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None

    def cnt(label, sec, key):
        v = g(sec, key)
        if v:
            out.append((label, str(int(v))))

    def frac(label, ok, tot):
        a, b = ok, tot
        if a is not None and b:
            out.append((label, f"{int(a)}/{int(b)}"))

    mins = g("games", "minutes")
    if mins:
        out.append(("Minutes jouées", f"{int(mins)}'"))
    cnt("Buts", "goals", "total"); cnt("Passes décisives", "goals", "assists")
    shots, on = g("shots", "total"), g("shots", "on")
    if shots:
        out.append(("Tirs (cadrés)", f"{int(shots)} ({int(on or 0)})"))
    cnt("Penaltys marqués", "penalty", "scored"); cnt("Penaltys ratés", "penalty", "missed")
    cnt("Penaltys arrêtés", "penalty", "saved")
    cnt("Arrêts", "goals", "saves"); cnt("Buts encaissés", "goals", "conceded")
    tot, acc = g("passes", "total"), g("passes", "accuracy")
    if tot and acc is not None:
        frac("Passes réussies", acc if acc <= tot else round(tot * acc / 100), tot)
    elif tot:
        out.append(("Passes", str(int(tot))))
    cnt("Passes clés", "passes", "key")
    frac("Dribbles réussis", g("dribbles", "success"), g("dribbles", "attempts"))
    frac("Duels gagnés", g("duels", "won"), g("duels", "total"))
    cnt("Tacles", "tackles", "total"); cnt("Interceptions", "tackles", "interceptions")
    cnt("Contres", "tackles", "blocks")
    cnt("Fautes subies", "fouls", "drawn"); cnt("Fautes commises", "fouls", "committed")
    cnt("Cartons jaunes", "cards", "yellow"); cnt("Cartons rouges", "cards", "red")
    return out


def get_player_photo(url):
    if not url:
        return None
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None


def player_card(m, date_str, path, use_logos=False, bg=None):
    """2e image du carrousel : meilleur joueur du match + toutes ses stats (16 max)."""
    OUT.mkdir(exist_ok=True)
    _apply_theme(bg)
    bp = m["best_player"]
    _, mcolor, _ = tier(m["rating"])
    _, pcolor, _ = tier(bp["rating"])
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S, 14], fill=pcolor)
    d.text((60, 62), "MEILLEUR JOUEUR DU MATCH", font=_f(FB, 28), fill=SUB)
    d.text((S - 60, 62), f'{m["home"]} {m["score_home"]}-{m["score_away"]} {m["away"]}',
           font=_fit(d, f'{m["home"]} {m["score_home"]}-{m["score_away"]} {m["away"]}', FR, 26, 420), fill=SUB, anchor="ra")

    # photo (ou initiales) + nom + note du joueur
    cx, cy, r = 190, 255, 110
    photo = get_player_photo(bp.get("photo")) if use_logos else None
    if photo:
        photo.thumbnail((2 * r, 2 * r))
        mask = Image.new("L", photo.size, 0)
        ImageDraw.Draw(mask).ellipse([0, 0, photo.width, photo.height], fill=255)
        img.paste(photo, (cx - photo.width // 2, cy - photo.height // 2), mask)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=5)
    else:
        _placeholder(d, bp["name"], cx, cy, r)
    d.text((340, 205), bp["name"], font=_fit(d, bp["name"], FB, 56, S - 340 - 50), fill=TXT, anchor="lm")
    info = " · ".join(x for x in [bp["team"], POS_FR.get(bp.get("position")), f'n°{bp["shirt"]}' if bp.get("shirt") else None] if x)
    d.text((340, 262), info, font=_fit(d, info, FR, 28, S - 340 - 50), fill=SUB, anchor="lm")
    d.rounded_rectangle([340, 305, 560, 385], 40, fill=pcolor, outline=TXT if THEMED else None, width=5)
    lum = 0.299 * pcolor[0] + 0.587 * pcolor[1] + 0.114 * pcolor[2]
    d.text((450, 345), fr(bp["rating"]), font=_f(FB, 54), fill=(14, 20, 36) if lum > 140 else (255, 255, 255), anchor="mm")

    # grille de stats : 2 colonnes
    lines = player_stat_lines(bp.get("stats", {}))[:16]
    for i, (lab, val) in enumerate(lines):
        x0 = 60 if i % 2 == 0 else 555
        y0 = 430 + (i // 2) * 62
        d.rounded_rectangle([x0, y0, x0 + 465, y0 + 52], 14, fill=CARD)
        d.text((x0 + 20, y0 + 26), lab, font=_fit(d, lab, FR, 22, 270), fill=SUB, anchor="lm")
        d.text((x0 + 445, y0 + 26), val, font=_f(FB, 28), fill=TXT, anchor="rm")
    _paste_logo(img, 100)
    p = OUT / path
    img.save(p)
    return str(p)
