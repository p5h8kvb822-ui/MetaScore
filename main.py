"""Génère une image carrée + une légende PAR match (un post Instagram par match).
Écrit published/<date>/ (images, manifest.json) et published/latest.txt (chemin du manifest).
Ordre de publication : du moins bien noté au mieux noté (le meilleur match finit en haut du profil)."""
import json, pathlib, datetime
from sources import fetch_finished_matches
from rating import rate_all, tier
from images import match_card, fr
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
    posts = []
    for i, m in enumerate(ms, 1):
        name = f"match_{i}.png"
        match_card(m, date_fr, name, use_logos=real)
        _, _, emoji = tier(m["rating"])
        caption = (f"{emoji} {m['home']} {m['score_home']}-{m['score_away']} {m['away']}\n"
                   f"Note : {fr(m['rating'])}/10\n\n{cfg['hashtags']} {leagues[m['league']]['tag']}")
        posts.append({"image": name, "caption": caption})
    posts.reverse()  # moins bien noté d'abord, meilleur en dernier

    (folder / "manifest.json").write_text(
        json.dumps({"date": day.isoformat(), "pause": cfg["pause_between_posts_seconds"], "posts": posts},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "published" / "latest.txt").write_text(f"published/{day.isoformat()}/manifest.json", encoding="utf-8")
    for p in posts:
        print(p["caption"].replace("\n", " | "))
    print(f"\n{len(posts)} post(s) -> {folder}")


if __name__ == "__main__":
    main()
