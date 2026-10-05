"""Note /10 d'un match terminé, estimée à partir des données API-Football.
Composantes (0-1) pondérées ; si une donnée manque, sa pondération est redistribuée."""

WEIGHTS = {
    "goals": 0.25,    # nombre de buts
    "xg": 0.15,       # xG cumulés
    "sot": 0.15,      # tirs cadrés
    "shots": 0.10,    # tirs au total
    "close": 0.15,    # score serré
    "drama": 0.10,    # buts tardifs / rebondissements, rouge
    "star": 0.10,     # meilleure note individuelle
}


def _sum(*xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) if xs else None


def components(m):
    c = {}
    goals = m["score_home"] + m["score_away"]
    c["goals"] = min(1, goals / 5)
    xg = _sum(m.get("xg_home"), m.get("xg_away"))
    c["xg"] = None if xg is None else min(1, xg / 4)
    sot = _sum(m.get("sot_home"), m.get("sot_away"))
    c["sot"] = None if sot is None else min(1, sot / 12)
    shots = _sum(m.get("shots_home"), m.get("shots_away"))
    c["shots"] = None if shots is None else min(1, shots / 25)
    margin = abs(m["score_home"] - m["score_away"])
    c["close"] = 1 - min(1, margin / 3) if goals > 0 else 0.35  # 0-0 = peu d'intérêt
    late = sum(1 for t in m.get("goal_minutes", []) if t >= 80)
    drama = 0.5 * min(1, late) + 0.3 * min(1, m.get("red_cards", 0)) + 0.2 * (1 if goals >= 4 else 0)
    c["drama"] = drama
    r = m.get("max_player_rating")
    c["star"] = None if r is None else max(0, min(1, (r - 6.5) / 2.5))
    return c


def rate_finished(m):
    c = components(m)
    used = {k: v for k, v in c.items() if v is not None}
    w = sum(WEIGHTS[k] for k in used)
    score = sum(WEIGHTS[k] * v for k, v in used.items()) / w
    return round(1 + 9 * score, 1)  # échelle 1-10


def rate_all(matches):
    return sorted(({**m, "rating": rate_finished(m)} for m in matches),
                  key=lambda x: x["rating"], reverse=True)


# Système de couleur : (note mini, libellé, couleur RGB, emoji)
TIERS = [
    (9.0, "Chef-d'œuvre", (142, 124, 255), "🟣"),
    (7.5, "À voir absolument", (46, 204, 113), "🟢"),
    (6.0, "Bon match", (242, 201, 76), "🟡"),
    (4.0, "Match moyen", (245, 165, 36), "🟠"),
    (0.0, "À oublier", (229, 72, 77), "🔴"),
]


def tier(rating):
    for low, label, color, emoji in TIERS:
        if rating >= low:
            return label, color, emoji
    return TIERS[-1][1:]
