"""Horoscope du jour : 12 images (une par signe) + légendes, dans published/horoscope/<date>/.
Écrit published/latest_horoscope.txt (chemin du manifest). Variable optionnelle : MATCH_DATE (AAAA-MM-JJ) pour tester une autre date."""
import json, os, pathlib, datetime, re
import requests
from zoneinfo import ZoneInfo
from textes import SIGNES, SYMBOLES, horoscope
from visuel import visuel

ROOT = pathlib.Path(__file__).resolve().parent
HASHTAGS = "#horoscope #astrologie #horoscopedujour #signeastrologique #citasie"


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MODELE = "claude-sonnet-5-5"
CONSIGNE = """Tu écris l'horoscope du jour pour un compte Instagram francophone, pour les 12 signes du zodiaque.
Date : {date}. Tutoiement interdit : on vouvoie le lecteur (« vous »).
Pour chaque signe : un texte PERSONNEL, qui donne l'impression de parler directement à la personne, avec une situation
précise et reconnaissable (un message qu'on n'ose pas envoyer, un café qui refroidit, une décision repoussée, un ex qui reviendrait,
une envie de tout plaquer...), un trait de caractère propre au signe, une touche d'humour ou de franchise, et une chute
qui donne envie de le partager ou d'identifier un proche. Le ton est chaleureux, piquant, jamais vague ni générique.
Contraintes : 3 ou 4 phrases courtes, entre 170 et 260 caractères au total, sans émoji, sans hashtag, sans retour à la ligne,
sans promesse médicale, financière ou absolue (« vous allez gagner »), et chaque texte doit être très différent des autres.
Réponds UNIQUEMENT par un tableau JSON de 12 chaînes, dans cet ordre : {signes}."""


def textes_ia(jour):
    """12 textes écrits par l'IA, ou None si la clé est absente ou si la réponse est inutilisable."""
    cle = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not cle:
        print("Pas de clé ANTHROPIC_API_KEY : textes de la banque.")
        return None
    date = f"{JOURS[jour.weekday()]} {jour.strftime('%d/%m/%Y')}"
    try:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=120,
                          headers={"x-api-key": cle, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                          json={"model": MODELE, "max_tokens": 3000, "temperature": 1,
                                "messages": [{"role": "user", "content": CONSIGNE.format(date=date, signes=", ".join(SIGNES))}]})
        r.raise_for_status()
        brut = "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")
        liste = json.loads(re.search(r"\[.*\]", brut, re.S).group(0))
        if len(liste) != 12 or not all(isinstance(t, str) for t in liste):
            raise ValueError("format inattendu")
        return [" ".join(t.split()) for t in liste]
    except Exception as e:
        print(f"IA indisponible ({e}) : textes de la banque.")
        return None


def texte_ok(t):
    return 80 <= len(t) <= 330


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
    ia = textes_ia(jour)
    for i, signe in enumerate(SIGNES):
        texte = ia[i] if ia and texte_ok(ia[i]) else horoscope(i, jour)
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
