"""Prédictions du jour (service sports.bzzoiro.com) -> une image par match + légende, dans published/pronostics/<date>/.
Variables : BSD_API_KEY (clé), MATCH_DATE (optionnel, AAAA-MM-JJ). Aucune limite de nombre de matchs.
Écrit published/latest_pronostics.txt (chemin du manifest)."""
import json, os, pathlib, datetime, time
from zoneinfo import ZoneInfo
import requests
import images
from images import prediction_card, JOURS
from noms_fr import fr_team, fr_comp
from legende import tag_equipe

ROOT = pathlib.Path(__file__).resolve().parent
BASE = "https://sports.bzzoiro.com/api/v2"
PARIS = ZoneInfo("Europe/Paris")
COUPES = {"champions league": "Ligue des champions", "europa league": "Europa League",
          "conference league": "Conference League"}


def _get(path, **params):
    key = os.environ["BSD_API_KEY"]
    r = requests.get(f"{BASE}/{path}", params=params, headers={"Authorization": f"Token {key}"}, timeout=60)
    if r.status_code == 429:
        time.sleep(20)
        r = requests.get(f"{BASE}/{path}", params=params, headers={"Authorization": f"Token {key}"}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"BSD {r.status_code} : {r.text[:300]}")
    return r.json()


def _all(path, **params):
    out, offset = [], 0
    while True:
        data = _get(path, limit=200, offset=offset, **params)
        res = data.get("results", [])
        out += res
        if not data.get("next") or not res or offset > 2000:
            return out
        offset += 200


def _find(d, *keys):
    """Première valeur trouvée parmi plusieurs noms de champ possibles (le format exact n'est pas garanti)."""
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, ""):
            return d[k]
    return None


def _name(v):
    return (v.get("name") if isinstance(v, dict) else v) or ""


def _kickoff(ev):
    raw = _find(ev, "event_date", "kickoff", "kickoff_time", "start_time", "date", "datetime", "start")
    if not raw:
        return None
    try:
        dt = datetime.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.astimezone(PARIS)
    except ValueError:
        return None


def _pct(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v * 100 if 0 <= v <= 1 else v


def build(p, leagues_by_bsd, forced_league=None):
    ev, mk = p.get("event") or {}, p.get("markets") or {}
    mr, ou, bt, sc = mk.get("match_result") or {}, mk.get("over_under") or {}, mk.get("btts") or {}, mk.get("score") or {}
    ph, pd_, pa = _pct(mr.get("prob_home")), _pct(mr.get("prob_draw")), _pct(mr.get("prob_away"))
    po, pb = _pct(ou.get("prob_over_25")), _pct(bt.get("prob_yes"))
    if None in (ph, pd_, pa, po, pb):
        return None
    lg = ev.get("league")
    lname = forced_league or _name(lg) or _find(ev, "league_name") or ""
    if not forced_league:
        lid = _find(ev, "league_id") or (lg.get("id") if isinstance(lg, dict) else None)
        if lid in leagues_by_bsd:
            lname = leagues_by_bsd[lid]
        else:
            low = str(lname).lower()
            lname = next((v for k, v in COUPES.items() if k in low and "women" not in low and "qualif" not in low), "")
    if not lname:
        return None
    ko = _kickoff(ev)
    home, away = _name(ev.get("home_team")), _name(ev.get("away_team"))
    score = sc.get("most_likely")
    return {"league": fr_comp(lname), "league_key": lname, "home": fr_team(home), "away": fr_team(away),
            "home_logo": _find(ev, "home_team_logo", "home_logo", "home_crest"),
            "away_logo": _find(ev, "away_team_logo", "away_logo", "away_crest"),
            "league_logo": _find(ev, "league_logo"),
            "kickoff": ko.strftime("%H:%M") if ko else None, "ko_dt": ko,
            "p_home": ph, "p_draw": pd_, "p_away": pa, "p_over25": po, "p_btts": pb,
            "score": str(score).replace(":", "-").replace(" ", "") if score else None}


def legende(m, tag_ligue):
    h, a = m["home"], m["away"]
    l = [f"🏆 {m['league']}", f"{h} - {a}"]
    if m.get("kickoff"):
        l.append(f"🕘 Coup d'envoi : {m['kickoff'].replace(':', 'h')}")
    l += [f"Victoire {h} : {round(m['p_home'])}% | Nul : {round(m['p_draw'])}% | Victoire {a} : {round(m['p_away'])}%",
          f"+2,5 buts : {round(m['p_over25'])}% | Les 2 équipes marquent : {round(m['p_btts'])}%"]
    if m.get("score"):
        l.append(f"Score le plus probable : {m['score']}")
    tags = ["#Football", tag_ligue, "#Pronostics", tag_equipe(h), tag_equipe(a)]
    seen, out = set(), []
    for t in tags:
        if t and t.lower() not in seen:
            seen.add(t.lower()); out.append(t)
    return "\n".join(l) + "\n\n" + " ".join(out)


def main():
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    leagues = cfg["leagues"]
    env_day = os.getenv("MATCH_DATE", "").strip()
    day = datetime.date.fromisoformat(env_day) if env_day else datetime.datetime.now(PARIS).date()
    (ROOT / "published").mkdir(exist_ok=True)
    (ROOT / "published" / "latest_pronostics.txt").unlink(missing_ok=True)
    real = not cfg.get("sample_mode")
    ms, debug = [], {}
    if not real:
        raw = json.loads((ROOT / "sample_pronostics.json").read_text(encoding="utf-8"))
        ms = [build(p, {}, p["_league"]) for p in raw]
    else:
        by_bsd = {v["bsd_id"]: k for k, v in leagues.items() if v.get("bsd_id")}
        window = dict(date_from=day.isoformat(), date_to=(day + datetime.timedelta(days=1)).isoformat())
        raw = _all("predictions/", **window)
        debug["total_recu"] = len(raw)
        debug["exemple_brut"] = raw[0] if raw else None
        seen = set()
        for p in raw:
            m = build(p, by_bsd)
            if not m or (m["ko_dt"] and m["ko_dt"].date() != day):
                continue
            k = (m["league_key"], m["home"], m["away"])
            if k not in seen:
                seen.add(k); ms.append(m)
    ms = [m for m in ms if m]
    folder = ROOT / "published" / "pronostics" / day.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "debug_pronostics.json").write_text(json.dumps(debug, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    if not ms:
        print("Aucune prédiction pour les compétitions suivies aujourd'hui."); return
    ms.sort(key=lambda m: m["ko_dt"] or datetime.datetime.max.replace(tzinfo=PARIS), reverse=True)
    images.OUT = folder
    date_fr = f"{JOURS[day.weekday()]} {day.strftime('%d/%m/%Y')}"
    posts = []
    for i, m in enumerate(ms, 1):
        name = f"prono_{i}.png"
        prediction_card(m, date_fr, name, use_logos=real)
        tag = next((v.get("tag", "") for k, v in leagues.items() if fr_comp(k) == m["league"] or k == m["league_key"]), "")
        posts.append({"images": [name], "caption": legende(m, tag)})
    (folder / "manifest.json").write_text(json.dumps({"date": day.isoformat(), "pause": cfg["pause_between_posts_seconds"],
                                                      "posts": posts}, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "published" / "latest_pronostics.txt").write_text(f"published/pronostics/{day.isoformat()}/manifest.json", encoding="utf-8")
    for p in posts:
        print(p["caption"].replace("\n", " | "))
    print(f"\n{len(posts)} prédiction(s) -> {folder}")


if __name__ == "__main__":
    main()
