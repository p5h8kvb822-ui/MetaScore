"""Images Instagram 1080x1440 (3:4), fond blanc.
1) match_card  : compétition, équipes, score, jauge de note avec curseur, toutes les stats d'équipe
2) player_card : meilleur joueur (identité + toutes ses stats)"""
import pathlib, io, hashlib, colorsys, datetime
from noms_fr import fr_pays
import requests
from PIL import Image, ImageDraw, ImageFont
from rating import tier

OUT = pathlib.Path(__file__).resolve().parent / "out"
LOGO_PATH = pathlib.Path(__file__).resolve().parent / "logo.png"
W, H = 1080, 1440
WHITE, NAVY, GRAY = (255, 255, 255), (14, 20, 36), (105, 116, 137)
LIGHT, LINE = (241, 244, 249), (222, 227, 236)
HOME_C, AWAY_C = (45, 100, 230), (32, 184, 150)
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124 Safari/537.36"}
GAUGE = [(1, (229, 72, 77)), (4, (245, 165, 36)), (6, (242, 201, 76)), (7.5, (46, 204, 113)), (9, (142, 124, 255)),
         (10, (142, 124, 255))]


# ------------------------------------------------------------------ outils
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
    while size > 14 and d.textlength(text, font=_f(path, size)) > max_w:
        size -= 2
    return _f(path, size)


def _lum(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def get_image(url):
    """Image (logo, photo, drapeau) à partir de son adresse. None si indisponible."""
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
    col = tuple(int(255 * v) for v in colorsys.hsv_to_rgb(hue, 0.55, 0.78))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    words = name.split()
    txt = "".join(w[0] for w in words[:2]).upper() if len(words) > 1 else name[:3].upper()
    d.text((cx, cy), txt, font=_f(FB, int(r * 0.62)), fill=WHITE, anchor="mm")


def _crest(img, d, name, url, cx, cy, r, use_logos):
    logo = get_image(url) if use_logos else None
    if logo:
        logo.thumbnail((2 * r, 2 * r))
        img.paste(logo, (cx - logo.width // 2, cy - logo.height // 2), logo)
    else:
        _placeholder(d, name, cx, cy, r)


def _league_logo(img, d, m, x, y, size, use_logos):
    logo = get_image(m.get("league_logo")) if use_logos else None
    if logo:
        logo.thumbnail((size, size))
        img.paste(logo, (x + (size - logo.width) // 2, y + (size - logo.height) // 2), logo)
    else:
        d.rounded_rectangle([x, y, x + size, y + size], 14, fill=LIGHT, outline=LINE, width=2)
        words = m["league"].split()
        txt = "".join(w[0] for w in words[:3]).upper()
        d.text((x + size // 2, y + size // 2), txt, font=_f(FB, size // 3), fill=GRAY, anchor="mm")


def _footer_logo(img):
    """Ton logo (version claire, fond transparent) centré en bas de l'image."""
    if not LOGO_PATH.exists():
        print("ATTENTION : logo.png introuvable à côté de images.py : images publiées sans logo")
        return
    logo = Image.open(LOGO_PATH).convert("RGBA")
    h = 132
    w = round(logo.width * h / logo.height)
    logo = logo.resize((w, h), Image.LANCZOS)
    img.paste(logo, ((W - w) // 2, H - h - 22), logo)


def _gauge_color(v):
    v = max(1, min(10, v))
    for (a, ca), (b, cb) in zip(GAUGE, GAUGE[1:]):
        if a <= v <= b:
            t = 0 if b == a else (v - a) / (b - a)
            return tuple(round(ca[i] * (1 - t) + cb[i] * t) for i in range(3))
    return GAUGE[-1][1]


def draw_gauge(img, d, rating, y_title, title="NOTE DU MATCH", compact=False):
    """Jauge de couleur 1 -> 10 avec un curseur (bulle + repère) sur la note obtenue."""
    x0, x1, bh = 70, 1010, 30
    _, color, _ = tier(rating)
    d.text((W // 2, y_title), title, font=_f(FB, 26), fill=GRAY, anchor="mm")
    y_bar = y_title + (100 if compact else 115)
    bar = Image.new("RGB", (x1 - x0, bh))
    bd = ImageDraw.Draw(bar)
    for x in range(x1 - x0):
        bd.line([(x, 0), (x, bh)], fill=_gauge_color(1 + 9 * x / (x1 - x0 - 1)))
    mask = Image.new("L", bar.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bar.width - 1, bh - 1], bh // 2, fill=255)
    img.paste(bar, (x0, y_bar), mask)
    # graduations
    for v in (1, 4, 6, 7.5, 9, 10):
        tx = x0 + (v - 1) / 9 * (x1 - x0)
        d.text((tx, y_bar + bh + 24), fr(v), font=_f(FR, 20), fill=GRAY, anchor="mm")
    # curseur
    cx = x0 + (max(1, min(10, rating)) - 1) / 9 * (x1 - x0)
    cy = y_bar + bh // 2
    d.ellipse([cx - 24, cy - 24, cx + 24, cy + 24], fill=WHITE, outline=NAVY, width=6)
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=color)
    bw_, bh_ = (116, 56) if compact else (128, 64)
    by = y_bar - 30 - bh_
    d.rounded_rectangle([cx - bw_ // 2, by, cx + bw_ // 2, by + bh_], 22, fill=color)
    d.polygon([(cx - 14, by + bh_ - 1), (cx + 14, by + bh_ - 1), (cx, by + bh_ + 16)], fill=color)
    d.text((cx, by + bh_ // 2), fr(rating), font=_f(FB, 38 if compact else 42), fill=NAVY if _lum(color) > 140 else WHITE, anchor="mm")
    return y_bar + bh + (44 if compact else 50)


# ------------------------------------------------------------------ stats d'équipe (toutes celles de l'API)
TEAM_STATS = [
    ("Ball Possession", "Possession"), ("expected_goals", "xG"), ("Total Shots", "Tirs"),
    ("Shots on Goal", "Tirs cadrés"), ("Shots off Goal", "Tirs non cadrés"), ("Blocked Shots", "Tirs contrés"),
    ("Shots insidebox", "Tirs dans la surface"), ("Shots outsidebox", "Tirs hors surface"),
    ("Corner Kicks", "Corners"), ("Fouls", "Fautes"), ("Offsides", "Hors-jeu"),
    ("Yellow Cards", "Cartons jaunes"), ("Red Cards", "Cartons rouges"), ("Goalkeeper Saves", "Arrêts du gardien"),
    ("Total passes", "Passes"), ("Passes accurate", "Passes réussies"), ("Passes %", "Précision des passes"),
    ("goals_prevented", "Buts évités"),
]


def _n(v):
    try:
        return float(str(v).replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def _disp(key, v):
    if v is None:
        return "0"
    if isinstance(v, str) and v.strip().endswith("%"):
        return v.strip()
    n = _n(v)
    if n is None:
        return str(v)
    if key in ("expected_goals", "goals_prevented"):
        return fr(f"{n:.2f}")
    return str(int(n)) if n == int(n) else fr(round(n, 2))


def team_stat_rows(m):
    hs, as_ = m.get("stats_home") or {}, m.get("stats_away") or {}
    known = {k for k, _ in TEAM_STATS}
    keys = [(k, lab) for k, lab in TEAM_STATS] + [(k, k) for k in hs if k not in known]
    rows = []
    for key, lab in keys:
        hv, av = hs.get(key), as_.get(key)
        if hv is None and av is None:
            continue
        rows.append((lab, key, hv, av))
    return rows


def draw_team_rows(d, rows, y0, row_h=36):
    xl, xr = 150, 930      # zone des barres : [150, 405] et [675, 930]
    for i, (lab, key, hv, av) in enumerate(rows):
        yc = y0 + i * row_h + row_h // 2
        hn, an = _n(hv) or 0, _n(av) or 0
        mx = max(hn, an)
        for side in (0, 1):
            a, b = (150, 405) if side == 0 else (675, 930)
            d.rounded_rectangle([a, yc - 6, b, yc + 6], 6, fill=LIGHT)
            v = hn if side == 0 else an
            if mx > 0 and v > 0:
                ln = max(10, round((b - a) * v / mx))
                if side == 0:
                    d.rounded_rectangle([b - ln, yc - 6, b, yc + 6], 6, fill=HOME_C)
                else:
                    d.rounded_rectangle([a, yc - 6, a + ln, yc + 6], 6, fill=AWAY_C)
        d.text((540, yc), lab, font=_fit(d, lab, FR, 22, 262), fill=NAVY, anchor="mm")
        d.text((60, yc), _disp(key, hv), font=_f(FB if hn >= an else FR, 24), fill=NAVY, anchor="lm")
        d.text((1020, yc), _disp(key, av), font=_f(FB if an >= hn else FR, 24), fill=NAVY, anchor="rm")


# ------------------------------------------------------------------ carte 1 : le match
def match_card(m, date_str, path, use_logos=False):
    OUT.mkdir(exist_ok=True)
    _, color, _ = tier(m["rating"])
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 18], fill=color)

    _league_logo(img, d, m, 60, 46, 72, use_logos)
    d.text((152, 70), m["league"].upper(), font=_fit(d, m["league"].upper(), FB, 30, 620), fill=NAVY, anchor="lm")
    d.text((152, 110), date_str, font=_f(FR, 24), fill=GRAY, anchor="lm")
    d.text((W - 60, 70), "TERMINÉ", font=_f(FB, 26), fill=GRAY, anchor="rm")

    cy = 270
    _crest(img, d, m["home"], m.get("home_logo"), 215, cy, 85, use_logos)
    _crest(img, d, m["away"], m.get("away_logo"), 865, cy, 85, use_logos)
    d.text((540, cy), f'{m["score_home"]} - {m["score_away"]}', font=_f(FB, 120), fill=NAVY, anchor="mm")
    d.text((215, 395), m["home"], font=_fit(d, m["home"], FB, 38, 380), fill=NAVY, anchor="mm")
    d.text((865, 395), m["away"], font=_fit(d, m["away"], FB, 38, 380), fill=NAVY, anchor="mm")

    # pastille de couleur avec la note du match, libellé au-dessus
    d.text((540, 440), "NOTE DU MATCH", font=_f(FB, 24), fill=GRAY, anchor="mm")
    d.rounded_rectangle([350, 462, 730, 577], 57, fill=color)
    d.text((540, 520), fr(m["rating"]), font=_f(FB, 92), fill=NAVY if _lum(color) > 140 else WHITE, anchor="mm")

    d.text((W // 2, 628), "STATISTIQUES DU MATCH", font=_f(FB, 24), fill=GRAY, anchor="mm")
    rows = team_stat_rows(m)[:18]
    row_h, y_rows = 33, 654
    draw_team_rows(d, rows, y_rows, row_h)
    y_end = y_rows + len(rows) * row_h + 6
    d.rounded_rectangle([60, y_end + 4, 76, y_end + 16], 4, fill=HOME_C)
    d.text((86, y_end + 10), m["home"], font=_fit(d, m["home"], FR, 20, 330), fill=GRAY, anchor="lm")
    d.rounded_rectangle([1004, y_end + 4, 1020, y_end + 16], 4, fill=AWAY_C)
    d.text((994, y_end + 10), m["away"], font=_fit(d, m["away"], FR, 20, 330), fill=GRAY, anchor="rm")
    _footer_logo(img)
    p = OUT / path
    img.save(p)
    return str(p)


# ------------------------------------------------------------------ carte 2 : le meilleur joueur
POS_FR = {"G": "Gardien", "D": "Défenseur", "M": "Milieu", "F": "Attaquant"}

NAT_CODES = {
    "france": "fr", "spain": "es", "germany": "de", "england": "gb-eng", "scotland": "gb-sct", "wales": "gb-wls",
    "northern ireland": "gb-nir", "ireland": "ie", "italy": "it", "portugal": "pt", "netherlands": "nl",
    "belgium": "be", "luxembourg": "lu", "switzerland": "ch", "austria": "at", "denmark": "dk", "norway": "no",
    "sweden": "se", "finland": "fi", "iceland": "is", "poland": "pl", "czech republic": "cz", "czechia": "cz",
    "slovakia": "sk", "slovenia": "si", "croatia": "hr", "serbia": "rs", "bosnia and herzegovina": "ba",
    "montenegro": "me", "north macedonia": "mk", "albania": "al", "kosovo": "xk", "greece": "gr", "turkey": "tr",
    "türkiye": "tr", "bulgaria": "bg", "romania": "ro", "hungary": "hu", "ukraine": "ua", "russia": "ru",
    "belarus": "by", "georgia": "ge", "armenia": "am", "azerbaijan": "az", "kazakhstan": "kz", "israel": "il",
    "cyprus": "cy", "malta": "mt", "estonia": "ee", "latvia": "lv", "lithuania": "lt", "moldova": "md",
    "brazil": "br", "argentina": "ar", "uruguay": "uy", "colombia": "co", "chile": "cl", "peru": "pe",
    "ecuador": "ec", "venezuela": "ve", "paraguay": "py", "bolivia": "bo", "mexico": "mx", "usa": "us",
    "united states": "us", "canada": "ca", "costa rica": "cr", "panama": "pa", "jamaica": "jm", "honduras": "hn",
    "haiti": "ht", "curacao": "cw", "morocco": "ma", "algeria": "dz", "tunisia": "tn", "egypt": "eg",
    "senegal": "sn", "ivory coast": "ci", "cote d'ivoire": "ci", "cameroon": "cm", "nigeria": "ng", "ghana": "gh",
    "mali": "ml", "guinea": "gn", "burkina faso": "bf", "dr congo": "cd", "congo dr": "cd", "congo": "cg",
    "gabon": "ga", "angola": "ao", "south africa": "za", "cape verde": "cv", "gambia": "gm", "benin": "bj",
    "togo": "tg", "mozambique": "mz", "zambia": "zm", "zimbabwe": "zw", "madagascar": "mg", "comoros": "km",
    "japan": "jp", "south korea": "kr", "korea republic": "kr", "china": "cn", "australia": "au",
    "new zealand": "nz", "iran": "ir", "iraq": "iq", "saudi arabia": "sa", "qatar": "qa", "uae": "ae",
    "uzbekistan": "uz", "philippines": "ph", "indonesia": "id", "thailand": "th",
}


def nat_code(nationality):
    if not nationality:
        return None
    return NAT_CODES.get(nationality.lower().replace("-", " ").strip())


def draw_flag(img, d, nationality, x, y, w, h, use_logos):
    """Drapeau (flagcdn.com) ; sans réseau : drapeau simple ou pastille avec le code pays."""
    code = nat_code(nationality)
    flag = get_image(f"https://flagcdn.com/w160/{code}.png") if (use_logos and code) else None
    if flag:
        flag = flag.resize((w, h), Image.LANCZOS)
        img.paste(flag, (x, y), flag)
    elif code == "fr":
        for i, c in enumerate([(0, 38, 150), (255, 255, 255), (237, 41, 57)]):
            d.rectangle([x + i * w // 3, y, x + (i + 1) * w // 3, y + h], fill=c)
    else:
        d.rectangle([x, y, x + w, y + h], fill=LIGHT)
        d.text((x + w // 2, y + h // 2), (code or "?").upper()[:3], font=_f(FB, h // 2), fill=GRAY, anchor="mm")
    d.rectangle([x, y, x + w, y + h], outline=LINE, width=2)


def _f_int(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def player_stat_rows(st, position):
    """TOUTES les stats du match fournies pour le joueur (zéros inclus) -> [(libellé, valeur)]."""
    out = []

    def g(sec, key):
        return _f_int((st.get(sec) or {}).get(key))

    def add(label, val):
        if val is not None:
            out.append((label, val))

    def num(label, sec, key, skip_zero=False):
        v = g(sec, key)
        if v is not None and not (skip_zero and v == 0):
            out.append((label, str(int(v))))

    def pair(label, ok, tot):
        a, b = ok, tot
        if a is not None and b is not None:
            out.append((label, f"{int(a)}/{int(b)}"))

    mins = g("games", "minutes")
    if mins is not None:
        add("Minutes jouées", f"{int(mins)}'")
    if (st.get("games") or {}).get("captain"):
        add("Capitaine", "Oui")
    num("Buts", "goals", "total"); num("Passes décisives", "goals", "assists")
    shots, on = g("shots", "total"), g("shots", "on")
    if shots is not None:
        add("Tirs (cadrés)", f"{int(shots)} ({int(on or 0)})")
    off = _f_int(st.get("offsides"))
    if off is not None:
        add("Hors-jeu", str(int(off)))
    if position == "G":
        num("Arrêts", "goals", "saves"); num("Buts encaissés", "goals", "conceded")
    else:
        num("Arrêts", "goals", "saves", skip_zero=True); num("Buts encaissés", "goals", "conceded", skip_zero=True)
    tot, acc = g("passes", "total"), g("passes", "accuracy")
    if tot is not None and acc is not None:
        pair("Passes réussies", acc if acc <= tot else round(tot * acc / 100), tot)
    elif tot is not None:
        add("Passes", str(int(tot)))
    num("Passes clés", "passes", "key")
    pair("Dribbles réussis", g("dribbles", "success"), g("dribbles", "attempts"))
    num("Dribbles subis", "dribbles", "past")
    pair("Duels gagnés", g("duels", "won"), g("duels", "total"))
    num("Tacles", "tackles", "total"); num("Interceptions", "tackles", "interceptions"); num("Contres", "tackles", "blocks")
    num("Fautes subies", "fouls", "drawn"); num("Fautes commises", "fouls", "committed")
    num("Cartons jaunes", "cards", "yellow"); num("Cartons rouges", "cards", "red")
    num("Penaltys obtenus", "penalty", "won"); num("Penaltys concédés", "penalty", "commited")
    num("Penaltys marqués", "penalty", "scored"); num("Penaltys ratés", "penalty", "missed")
    num("Penaltys arrêtés", "penalty", "saved")
    return out


def _age(birth, ref=None):
    try:
        b = datetime.date.fromisoformat(birth)
    except (TypeError, ValueError):
        return None
    ref = ref or datetime.date.today()
    return ref.year - b.year - ((ref.month, ref.day) < (b.month, b.day))


def player_card(m, date_str, path, use_logos=False):
    OUT.mkdir(exist_ok=True)
    bp = m["best_player"]
    prof = bp.get("profile") or {}
    rating = round(bp["rating"], 1)
    _, pcolor, _ = tier(rating)
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 18], fill=pcolor)

    _league_logo(img, d, m, 60, 46, 56, use_logos)
    d.text((132, 74), "HOMME DU MATCH", font=_f(FB, 28), fill=GRAY, anchor="lm")
    line = f'{m["home"]} {m["score_home"]}-{m["score_away"]} {m["away"]}'
    d.text((W - 60, 74), line, font=_fit(d, line, FR, 24, 380), fill=GRAY, anchor="rm")

    # photo
    cx, cy, r = 170, 262, 110
    photo = get_image(bp.get("photo")) if use_logos else None
    if photo:
        size = 2 * r
        scale = max(size / photo.width, size / photo.height)
        photo = photo.resize((round(photo.width * scale), round(photo.height * scale)), Image.LANCZOS)
        left, top = (photo.width - size) // 2, round((photo.height - size) * 0.15)
        photo = photo.crop((left, top, left + size, top + size))
        base = Image.new("RGBA", (size, size), LIGHT + (255,))
        base.alpha_composite(photo)
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
        img.paste(base.convert("RGB"), (cx - r, cy - r), mask)
    else:
        _placeholder(d, bp["name"], cx, cy, r)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=pcolor, width=6)

    # nom, puis drapeau de sa nationalité et logo de son club en dessous
    x_txt = 320
    d.text((x_txt, 205), bp["name"], font=_fit(d, bp["name"], FB, 60, W - x_txt - 50), fill=NAVY, anchor="lm")
    tx = x_txt
    nat = prof.get("nationality")
    if nat:
        draw_flag(img, d, nat, tx, 252, 66, 44, use_logos)
        tx += 66 + 24
    club_logo = bp.get("team_logo") or (m.get("home_logo") if bp.get("team") == m["home"] else m.get("away_logo"))
    _crest(img, d, bp.get("team") or "?", club_logo, tx + 34, 275, 34, use_logos)

    # pastille de couleur avec la note du joueur : même taille, même endroit que sur la fiche du match
    d.text((540, 440), "NOTE DU JOUEUR", font=_f(FB, 24), fill=GRAY, anchor="mm")
    d.rounded_rectangle([350, 462, 730, 577], 57, fill=pcolor)
    d.text((540, 520), fr(rating), font=_f(FB, 92), fill=NAVY if _lum(pcolor) > 140 else WHITE, anchor="mm")

    # toutes les stats du match
    d.text((W // 2, 628), "STATISTIQUES DU MATCH", font=_f(FB, 24), fill=GRAY, anchor="mm")
    rows = player_stat_rows(bp.get("stats", {}), bp.get("position"))
    pitch, top0 = 46, 654
    avail = (H - 22 - 132 - 14) - top0                # place avant le logo
    max_rows = max(2, (avail // pitch) * 2)
    for i, (lab, val) in enumerate(rows[:max_rows]):
        x0 = 60 if i % 2 == 0 else 555
        y0 = top0 + (i // 2) * pitch
        d.rounded_rectangle([x0, y0, x0 + 465, y0 + 40], 13, fill=LIGHT)
        d.text((x0 + 18, y0 + 20), lab, font=_fit(d, lab, FR, 24, 300), fill=NAVY, anchor="lm")
        d.text((x0 + 447, y0 + 20), val, font=_f(FB, 28), fill=NAVY, anchor="rm")
    if len(rows) > max_rows:
        print(f"  note : {len(rows) - max_rows} stat(s) du joueur non affichées (manque de place)")
    _footer_logo(img)
    p = OUT / path
    img.save(p)
    return str(p)


# ------------------------------------------------------------------ pronostics (avant le match)
DRAW_C = (178, 187, 205)


def draw_segment_bar(d, img, title, segments, y_title):
    """Barre à segments (même style pour les 3 pronostics) : [(pourcentage, couleur, libellé), ...]."""
    x0, x1, bh = 70, 1010, 50
    d.text((W // 2, y_title), title, font=_f(FB, 26), fill=GRAY, anchor="mm")
    tot = sum(p for p, _, _ in segments) or 1
    y_bar = y_title + 80
    bar = Image.new("RGB", (x1 - x0, bh))
    bd = ImageDraw.Draw(bar)
    x, centers = 0, []
    for p, c, _ in segments:
        w = round((x1 - x0) * p / tot)
        bd.rectangle([x, 0, x + w, bh], fill=c)
        centers.append(x0 + x + w / 2)
        x += w
    mask = Image.new("L", bar.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, bar.width - 1, bh - 1], bh // 2, fill=255)
    img.paste(bar, (x0, y_bar), mask)
    best = max(range(len(segments)), key=lambda i: segments[i][0])
    for i, ((p, c, label), cx) in enumerate(zip(segments, centers)):
        cx = min(max(cx, x0 + 70), x1 - 70)
        d.text((cx, y_bar - 30), f"{round(p)}%", font=_f(FB, 46 if i == best else 36), fill=NAVY if i == best else GRAY, anchor="mm")
        d.text((cx, y_bar + bh + 32), label, font=_fit(d, label, FB if i == best else FR, 24, 300), fill=NAVY if i == best else GRAY, anchor="mm")
    return y_bar + bh + 64


def prediction_card(m, date_str, path, use_logos=False):
    """Pronostic d'un match à venir : victoire, +2,5 buts, les deux équipes marquent (barres à segments)."""
    OUT.mkdir(exist_ok=True)
    img = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 18], fill=HOME_C)
    _league_logo(img, d, m, 60, 46, 72, use_logos)
    d.text((152, 70), m["league"].upper(), font=_fit(d, m["league"].upper(), FB, 30, 620), fill=NAVY, anchor="lm")
    d.text((152, 110), date_str, font=_f(FR, 24), fill=GRAY, anchor="lm")
    d.text((W - 60, 70), "PRONOSTIC", font=_f(FB, 26), fill=HOME_C, anchor="rm")

    cy = 270
    _crest(img, d, m["home"], m.get("home_logo"), 215, cy, 85, use_logos)
    _crest(img, d, m["away"], m.get("away_logo"), 865, cy, 85, use_logos)
    d.text((540, cy - 52), "COUP D'ENVOI", font=_f(FB, 22), fill=GRAY, anchor="mm")
    d.text((540, cy + 10), m["time"], font=_f(FB, 96), fill=NAVY, anchor="mm")
    d.text((215, 395), m["home"], font=_fit(d, m["home"], FB, 38, 380), fill=NAVY, anchor="mm")
    d.text((865, 395), m["away"], font=_fit(d, m["away"], FB, 38, 380), fill=NAVY, anchor="mm")

    y = draw_segment_bar(d, img, "VICTOIRE", [(m["p_home"], HOME_C, m["home"]), (m["p_draw"], DRAW_C, "Nul"),
                                              (m["p_away"], AWAY_C, m["away"])], 480)
    po = round(m["p_over25"])
    y = draw_segment_bar(d, img, "NOMBRE DE BUTS", [(po, HOME_C, "Plus de 2,5 buts"), (100 - po, DRAW_C, "Moins de 2,5 buts")], y + 50)
    pb = round(m["p_btts"])
    draw_segment_bar(d, img, "LES DEUX ÉQUIPES MARQUENT", [(pb, AWAY_C, "Oui"), (100 - pb, DRAW_C, "Non")], y + 50)
    _footer_logo(img)
    p = OUT / path
    img.save(p)
    return str(p)
