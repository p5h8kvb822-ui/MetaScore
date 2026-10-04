"""Génère, pour chaque match terminé, un carrousel Instagram de 2 images carrées :
  1) la carte du match (logos, score, note, stats)   2) le meilleur joueur du match et toutes ses stats.
Écrit published/<date>/ (images, manifest.json) et published/latest.txt (chemin du manifest).
Ordre de publication : du moins bien noté au mieux noté (le meilleur match finit en haut du profil)."""
import json, pathlib, datetime
from sources import fetch_finished_matches
from rating import rate_all, tier
from images import match_card, player_card, fr
import images

ROOT = pathlib.Path(__file__).resolve().parent


def main():
    (ROOT / "published").mkdir(exist_ok=True)
    (ROOT / "published" / "latest.txt").unlink(missing_ok=True)  # évite de republier la veille
    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    leagues = cfg["leagues"]
    day = datetime.date.today()
    date_fr = day.strftime("%d/%m/%Y")
    real = not cfg.get("sample_mode")

    ms = rate_all([m for m in fetch_finished_matches(cfg) if m["league"] in leagues])[: cfg["max_matches"]]
    if not ms:
        print("Aucun match terminé à noter."); return

    folder = ROOT / "published" / day.isoformat()
    folder.mkdir(parents=True, exist_ok=True)
    images.OUT = folder
    posts, debug = [], {}
    for i, m in enumerate(ms, 1):
        files = [f"match_{i}_a.png"]
        match_card(m, date_fr, files[0], use_logos=real)
        if m.get("best_player"):
            files.append(f"match_{i}_b.png")
            player_card(m, date_fr, files[1], use_logos=real)
            debug[f"{m['home']}-{m['away']}"] = m["best_player"]  # pour vérifier les stats reçues
        _, _, emoji = tier(m["rating"])
        caption = (f"{emoji} {m['home']} {m['score_home']}-{m['score_away']} {m['away']}\n"
                   f"Note : {fr(m['rating'])}/10\n"
                   + (f"⭐ Meilleur joueur : {m['best_player']['name']} ({fr(m['best_player']['rating'])})\n"
                      if m.get("best_player") else "")
                   + f"\n{cfg['hashtags']} {leagues[m['league']]['tag']}")
        posts.append({"images": files, "caption": caption})
    posts.reverse()  # moins bien noté d'abord, meilleur en dernier

    (folder / "manifest.json").write_text(
        json.dumps({"date": day.isoformat(), "pause": cfg["pause_between_posts_seconds"], "posts": posts},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (folder / "debug_best_players.json").write_text(json.dumps(debug, ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "published" / "latest.txt").write_text(f"published/{day.isoformat()}/manifest.json", encoding="utf-8")
    for p in posts:
        print(p["caption"].replace("\n", " | "), f"[{len(p['images'])} image(s)]")
    print(f"\n{len(posts)} post(s) -> {folder}")


if __name__ == "__main__":
    main()
