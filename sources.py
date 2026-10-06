"""Source de données : API-Football (api-sports.io) -> fetch_finished_matches.
Avec "sample_mode": true dans config.json, on lit sample_finished.json (aucun accès réseau).
Clé à fournir : variable d'environnement API_FOOTBALL_KEY."""
import json, os, pathlib, datetime, time, unicodedata
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


NATIONAL_KEYS = ("nations league", "world cup", "euro championship", "european championship", "friendlies",
                 "qualification", "copa america", "africa cup", "asian cup", "gold cup")


def _is_national(league_name):
    n = league_name.lower()
    return any(k in n for k in NATIONAL_KEYS) and "club" not in n


def _fold(t):
    """minuscules sans accents, pour chercher une équipe par son nom."""
    return "".join(c for c in unicodedata.normalize("NFKD", t.lower()) if not unicodedata.combining(c))


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
                best = {"id": pl.get("id"), "name": pl.get("name"), "photo": pl.get("photo"), "position": g.get("position"),
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
        "stats_home": hs, "stats_away": as_,  # toutes les stats d'équipe fournies par l'API
        "league_logo": fx["league"].get("logo"),
        "is_national": _is_national(fx["league"].get("name", "")),
        "best_player": _best_player(fx),
    }


def fetch_finished_matches(cfg, day=None, team=None):
    """Matchs terminés d'un jour. Sans `team` : seulement tes compétitions.
    Avec `team` (ex. "Lyon") : tous les matchs terminés de ce jour où joue une équipe dont le nom contient
    ce texte, quelle que soit la compétition (pour tester sur un match précis)."""
    if cfg.get("sample_mode"):
        return _sample("sample_finished.json")
    day = day or datetime.date.today().isoformat()
    gap = cfg.get("api_min_interval_seconds", 7)
    names = {c["api_football_id"]: name for name, c in cfg["leagues"].items()}
    todays = _get("fixtures", gap, date=day)  # 1 appel : tous les matchs du jour
    key = _fold(team) if team else None

    def wanted(f):
        if f["fixture"]["status"]["short"] not in FINISHED:
            return False
        if key:
            return key in _fold(f["teams"]["home"]["name"] + " " + f["teams"]["away"]["name"])
        return f["league"]["id"] in names

    ids = [f["fixture"]["id"] for f in todays if wanted(f)]
    print(f"Date utilisée : {day}")
    print(f"{len(todays)} matchs ce jour, {len(ids)} terminés" + (f" avec « {team} »" if team else " dans tes compétitions"))
    if key and not ids:  # aide au diagnostic : on montre ce que l'API a trouvé avec ce nom, quel que soit le statut
        near = [f for f in todays if key in _fold(f["teams"]["home"]["name"] + " " + f["teams"]["away"]["name"])]
        if near:
            for f in near[:10]:
                print(f"  trouvé : {f['teams']['home']['name']} - {f['teams']['away']['name']} "
                      f"({f['league']['name']}) statut = {f['fixture']['status']['short']} ({f['fixture']['status']['long']})")
        else:
            print(f"  aucun match avec « {team} » dans les {len(todays)} matchs de ce jour : essaie l'autre équipe ou vérifie la date")
    out = []
    for fid in ids[: cfg["max_matches"]]:  # 1 appel par match (le paramètre « ids » est refusé par le plan gratuit)
        for fx in _get("fixtures", gap, id=fid):  # stats, joueurs et événements du match
            m = normalize(fx)
            m["league"] = names.get(fx["league"]["id"], fx["league"]["name"])
            bp = m.get("best_player")
            if bp and bp.get("id"):  # fiche du joueur : date de naissance, nationalité, taille...
                try:
                    res = _get("players/profiles", gap, player=bp["id"])
                    if res:
                        bp["profile"] = res[0].get("player", res[0])
                except Exception as e:  # on continue sans ces infos
                    print(f"  profil du joueur indisponible : {e}")
            out.append(m)
    return out
