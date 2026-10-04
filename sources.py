"""Source de données : SofaScore (stats de fin de match) -> fetch_finished_matches
Avec "sample_mode": true dans config.json, on lit data/sample_*.json (aucun accès réseau)."""
import json, pathlib, datetime
import requests

ROOT = pathlib.Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept-Language": "en"}


def _sample(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- SofaScore
API = "https://api.sofascore.com/api/v1"


def _get(path):
    r = requests.get(API + path, headers=UA, timeout=30)
    r.raise_for_status()
    return r.json()


def _stat(stats, *needles):
    """Cherche une stat par nom (période ALL). Renvoie (home, away) ou (None, None)."""
    for period in stats.get("statistics", []):
        if period.get("period") != "ALL":
            continue
        for g in period.get("groups", []):
            for it in g.get("statisticsItems", []):
                name = it.get("name", "").lower()
                if any(n in name for n in needles):
                    return it.get("homeValue"), it.get("awayValue")
    return None, None


def normalize_event(ev, stats, incidents, lineups):
    h, a = _stat(stats, "expected goals")
    sh, sa = _stat(stats, "shots on target")
    bh, ba = _stat(stats, "big chances")
    rh, ra = _stat(stats, "red cards")
    ph, pa = _stat(stats, "ball possession")
    minutes = [i.get("time") for i in incidents.get("incidents", [])
               if i.get("incidentType") == "goal" and i.get("time") is not None]
    ratings = [p.get("statistics", {}).get("rating") for side in ("home", "away")
               for p in lineups.get(side, {}).get("players", [])]
    ratings = [x for x in ratings if x]
    return {
        "league": None, "home": ev["homeTeam"]["name"], "away": ev["awayTeam"]["name"],
        "home_id": ev["homeTeam"].get("id"), "away_id": ev["awayTeam"].get("id"),
        "score_home": ev["homeScore"].get("current", 0), "score_away": ev["awayScore"].get("current", 0),
        "xg_home": h, "xg_away": a, "sot_home": sh, "sot_away": sa, "big_home": bh, "big_away": ba,
        "poss_home": ph, "poss_away": pa, "red_cards": (rh or 0) + (ra or 0), "goal_minutes": minutes,
        "max_player_rating": max(ratings) if ratings else None,
    }


def fetch_finished_matches(cfg, day=None):
    if cfg.get("sample_mode"):
        return _sample("sample_finished.json")
    day = day or datetime.date.today().isoformat()
    ids = {c["sofascore_id"]: name for name, c in cfg["leagues"].items()}
    out = []
    for ev in _get(f"/sport/football/scheduled-events/{day}").get("events", []):
        tid = ev.get("tournament", {}).get("uniqueTournament", {}).get("id")
        if tid not in ids or ev.get("status", {}).get("type") != "finished":
            continue
        eid = ev["id"]
        safe = lambda p: _try(lambda: _get(p))
        m = normalize_event(ev, safe(f"/event/{eid}/statistics"), safe(f"/event/{eid}/incidents"),
                            safe(f"/event/{eid}/lineups"))
        m["league"] = ids[tid]
        out.append(m)
    return out


def _try(fn):
    try:
        return fn()
    except Exception:
        return {}
