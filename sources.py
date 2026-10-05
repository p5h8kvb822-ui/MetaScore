"""Source de données : API-Football (api-sports.io) -> fetch_finished_matches.
Avec "sample_mode": true dans config.json, on lit sample_finished.json (aucun accès réseau).
Clé à fournir : variable d'environnement API_FOOTBALL_KEY."""
import json, os, pathlib, datetime, time
import requests

ROOT = pathlib.Path(__file__).resolve().parent
API = "https://v3.football.api-sports.io"
FINISHED = ("FT", "AET", "PEN")
_last_call = 0.0


def _sample(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _get(path, interval=7, **params):
    """Appel API avec pause entre appels (le plan gratuit limite à ~10 appels/minute)."""
    global _last_call
    wait = interval - (time.time() - _last_call)
    if wait > 0:
        time.sleep(wait)
    r = requests.get(f"{API}/{path}", params=params, timeout=60,
                     headers={"x-apisports-key": os.environ["API_FOOTBALL_KEY"]})
    _last_call = time.time()
    r.raise_for_status()
    data = r.json()
    if data.get("errors"):  # l'API répond 200 même pour un refus de plan / de saison
        raise RuntimeError(f"API-Football : {data['errors']}")
    return data.get("response", [])


def _num(v):
    """'55%' -> 55.0 ; '1.8' -> 1.8 ; None -> None."""
    if v is None or v == "":
        return None
    try:
        return float(str(v).replace("%", "").strip())
    except ValueError:
        return None


def _team_stats(statistics, team_id):
    for blk in statistics or []:
        if blk.get("team", {}).get("id") == team_id:
            return {s.get("type"): s.get("value") for s in blk.get("statistics", [])}
    return {}


def _best_player(fx):
    """Joueur avec la meilleure note (les deux équipes confondues)."""
    best = None
    for blk in fx.get("players") or []:
        team = blk.get("team", {}).get("name")
        for p in blk.get("players", []):
            st = (p.get("statistics") or [{}])[0]
            rating = _num(st.get("games", {}).get("rating"))
            if rating and (best is None or rating > best["rating"]):
                pl = p.get("player", {})
                g = st.get("games", {})
                best = {"name": pl.get("name"), "photo": pl.get("photo"), "position": g.get("position"),
                        "shirt": g.get("number"), "team": team, "rating": rating, "stats": st}
    return best


def normalize(fx):
    home, away = fx["teams"]["home"], fx["teams"]["away"]
    hs = _team_stats(fx.get("statistics"), home["id"])
    as_ = _team_stats(fx.get("statistics"), away["id"])
    goal_minutes, reds = [], 0
    for e in fx.get("events") or []:
        t = e.get("time", {})
        minute = (t.get("elapsed") or 0) + (t.get("extra") or 0)
        if e.get("type") == "Goal" and e.get("detail") != "Missed Penalty":
            goal_minutes.append(minute)
        if e.get("type") == "Card" and "Red" in (e.get("detail") or ""):
            reds += 1
    g = lambda d, k: _num(d.get(k))
    return {
        "league": None, "home": home["name"], "away": away["name"],
        "home_logo": home.get("logo"), "away_logo": away.get("logo"),
        "score_home": fx["goals"]["home"] or 0, "score_away": fx["goals"]["away"] or 0,
        "xg_home": g(hs, "expected_goals"), "xg_away": g(as_, "expected_goals"),
        "sot_home": g(hs, "Shots on Goal"), "sot_away": g(as_, "Shots on Goal"),
        "shots_home": g(hs, "Total Shots"), "shots_away": g(as_, "Total Shots"),
        "poss_home": g(hs, "Ball Possession"), "poss_away": g(as_, "Ball Possession"),
        "corners_home": g(hs, "Corner Kicks"), "corners_away": g(as_, "Corner Kicks"),
        "red_cards": reds, "goal_minutes": goal_minutes,
        "best_player": _best_player(fx),
    }


def fetch_finished_matches(cfg, day=None):
    if cfg.get("sample_mode"):
        return _sample("sample_finished.json")
    day = day or datetime.date.today().isoformat()
    gap = cfg.get("api_min_interval_seconds", 7)
    names = {c["api_football_id"]: name for name, c in cfg["leagues"].items()}
    todays = _get("fixtures", gap, date=day)  # 1 appel : tous les matchs du jour
    ids = [f["fixture"]["id"] for f in todays
           if f["league"]["id"] in names and f["fixture"]["status"]["short"] in FINISHED]
    print(f"{len(todays)} matchs ce jour, {len(ids)} terminés dans tes compétitions")
    out = []
    for i in range(0, len(ids[: cfg["max_matches"]]), 20):  # détails (stats, joueurs, événements) par lots de 20
        for fx in _get("fixtures", gap, ids="-".join(map(str, ids[i:i + 20]))):
            m = normalize(fx)
            m["league"] = names[fx["league"]["id"]]
            out.append(m)
    return out
