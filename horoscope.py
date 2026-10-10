"""Horoscope du jour : 12 images (une par signe) + légendes, dans published/horoscope/<date>/.
Écrit published/latest_horoscope.txt (chemin du manifest). Variable optionnelle : MATCH_DATE (AAAA-MM-JJ) pour tester une autre date."""
import json, os, pathlib, datetime
from zoneinfo import ZoneInfo
from textes import SIGNES, SYMBOLES, horoscope
from visuel import visuel

ROOT = pathlib.Path(__file__).resolve().parent
HASHTAGS = "#horoscope #astrologie #horoscopedujour #signeastrologique #citasie"


def main():
    env = os.getenv("MATCH_DATE", "").strip()
    jour = datetime.date.fromisoformat(env) if env else datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    date_txt = jour.strftime("%d/%m/%Y")
    pub = ROOT / "published"
    pub.mkdir(exist_ok=True)
    (pub / "latest_horoscope.txt").unlink(missing_ok=True)
    dossier = pub / "horoscope" / jour.isoformat()
    dossier.mkdir(parents=True, exist_ok=True)
    posts = []
    for i, signe in enumerate(SIGNES):
        texte = horoscope(i, jour)
        slug = signe.lower().replace("é", "e").replace("è", "e")
        nom = f"{i + 1:02d}_{slug}.png"
        visuel(signe, date_txt, texte, dossier / nom)
        tag = "#" + slug
        posts.append({"images": [nom],
                      "caption": f"{SYMBOLES[i]}️ {signe} : horoscope du {date_txt}\n\n{texte}\n\n{tag} {HASHTAGS}"})
    posts.reverse()  # Poissons d'abord, Bélier en dernier : il apparaît en premier sur le profil
    (dossier / "manifest.json").write_text(json.dumps({"date": jour.isoformat(), "pause": 20, "posts": posts},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    (pub / "latest_horoscope.txt").write_text(f"published/horoscope/{jour.isoformat()}/manifest.json", encoding="utf-8")
    print(f"{len(posts)} horoscopes -> {dossier}")


if __name__ == "__main__":
    main()
