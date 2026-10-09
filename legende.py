"""Légende Instagram d'un post : compétition, score, notes, homme du match, stats, hashtags du match."""
import re, unicodedata

# Hashtags courts pour les clubs dont le nom français est long (clé en minuscules)
COURTS = {
    "paris sg": "PSG", "paris saint-germain": "PSG", "marseille": "OM", "olympique de marseille": "OM",
    "lyon": "OL", "olympique lyonnais": "OL", "manchester city": "ManCity", "manchester united": "ManUtd",
    "tottenham": "Spurs", "newcastle": "NUFC", "real madrid": "RealMadrid", "atlético de madrid": "Atletico",
    "atletico madrid": "Atletico", "fc barcelone": "Barca", "barcelone": "Barca", "bayern munich": "FCBayern",
    "borussia dortmund": "BVB", "bayer leverkusen": "Bayer04", "inter": "Inter", "inter milan": "Inter",
    "ac milan": "ACMilan", "juventus": "Juve", "as monaco": "ASMonaco", "monaco": "ASMonaco",
    "rb leipzig": "RBLeipzig", "paris fc": "ParisFC",
}


def _slug(txt):
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]", "", txt)


def tag_equipe(nom):
    t = COURTS.get(nom.lower().strip()) or _slug(nom)
    return "#" + t.upper() if t else ""


def _pl(n, un, plus):
    return f"{n} {un if n == 1 else plus}"


def stats_joueur(bp):
    st = bp.get("stats") or {}
    g = lambda a, b: int(((st.get(a) or {}).get(b)) or 0)
    items = [
        (g("goals", "total"), "but", "buts", "⚽️ "),
        (g("goals", "assists"), "passe D", "passes D", ""),
        (g("shots", "on"), "tir cadré", "tirs cadrés", ""),
        (g("goals", "saves"), "arrêt", "arrêts", ""),
        (g("passes", "key"), "passe clé", "passes clés", ""),
        (g("tackles", "interceptions") + g("tackles", "total"), "récupération", "récupérations", ""),
        (g("dribbles", "success"), "dribble réussi", "dribbles réussis", ""),
    ]
    parts = [_pl(n, u, p) for n, u, p, _ in items if n > 0][:4]
    return parts


def legende(m):
    pt = lambda x: f"{x:.1f}"
    l = [f"🏆 {m['league']}",
         f"{m['home']} {m['score_home']}-{m['score_away']} {m['away']}",
         f"Note du match : {pt(m['rating'])}/10 ⭐"]
    bp = m.get("best_player")
    if bp:
        l.append(f"Homme du match : {bp['name']}")
        parts = stats_joueur(bp) + [f"Note : {pt(bp['rating'])}"]
        l.append(" | ".join(parts))
    tags = ["#Football", m.get("league_tag", ""), "#MOTM", tag_equipe(m["home"]), tag_equipe(m["away"])]
    seen, out = set(), []
    for t in tags:
        if t and t.lower() not in seen:
            seen.add(t.lower()); out.append(t)
    return "\n".join(l) + "\n\n" + " ".join(out)
