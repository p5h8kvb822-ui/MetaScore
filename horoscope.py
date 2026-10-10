"""Horoscope du jour : 12 images (une par signe) + légendes, dans published/horoscope/<date>/.
Écrit published/latest_horoscope.txt (chemin du manifest). Variable optionnelle : MATCH_DATE (AAAA-MM-JJ) pour tester une autre date."""
import json, os, pathlib, datetime, re
import ia
from zoneinfo import ZoneInfo
from textes import SIGNES, SYMBOLES, horoscope
from visuel import visuel

ROOT = pathlib.Path(__file__).resolve().parent
HASHTAGS = "#horoscope #astrologie #horoscopedujour #signeastrologique #citasie"


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
CONSIGNE = """Tu écris l'horoscope du jour pour un compte Instagram francophone, pour les 12 signes du zodiaque.
Date : {date}. Tutoiement interdit : on vouvoie le lecteur (« vous »).
Pour chaque signe : un texte PERSONNEL, qui donne l'impression de parler directement à la personne, avec une situation
précise et reconnaissable (un message qu'on n'ose pas envoyer, un café qui refroidit, une décision repoussée, un ex qui reviendrait,
une envie de tout plaquer...), un trait de caractère propre au signe, une touche d'humour ou de franchise, et une chute
qui donne envie de le partager ou d'identifier un proche. Le ton est chaleureux, piquant, jamais vague ni générique.
Contraintes : 3 ou 4 phrases courtes, entre 170 et 260 caractères au total, sans émoji, sans hashtag, sans retour à la ligne,
sans promesse médicale, financière ou absolue (« vous allez gagner »), et chaque texte doit être très différent des autres.
Pour chaque signe, donne aussi une NOTE de 1 à 5 (entier) qui dit la qualité de la journée : 5 = journée exceptionnelle,
3 = correcte, 1 = journée difficile. Les notes doivent être variées et crédibles (au moins un signe à 2 ou moins, au moins un à 5,
moyenne autour de 3,5) et le texte doit être cohérent avec la note (jour difficile : conseil bienveillant et humour).
Réponds UNIQUEMENT par un tableau JSON de 12 objets {{"note": 1 à 5, "texte": "..."}}, dans cet ordre : {signes}."""


def textes_ia(jour):
    """12 textes écrits par l'IA, ou None si la clé est absente ou si la réponse est inutilisable."""
    if not ia.disponible():
        print("Pas de clé OPENAI_API_KEY : textes de la banque.")
        return None
    date = f"{JOURS[jour.weekday()]} {jour.strftime('%d/%m/%Y')}"
    try:
        brut = ia.demander(CONSIGNE.format(date=date, signes=", ".join(SIGNES)))
        liste = json.loads(re.search(r"\[.*\]", brut, re.S).group(0))
        if len(liste) != 12:
            raise ValueError("format inattendu")
        out = []
        for x in liste:
            note = int(x["note"])
            if not 1 <= note <= 5:
                raise ValueError("note hors 1-5")
            out.append({"note": note, "texte": " ".join(str(x["texte"]).split())})
        return out
    except Exception as e:
        print(f"IA indisponible ({e}) : textes de la banque.")
        return None


def texte_ok(t):
    return 80 <= len(t) <= 330


NOTES_SECOURS = [3, 4, 5, 4, 2, 3, 5, 4, 3, 2, 4, 5]
PAR_CARROUSEL = 12  # un seul carrousel de 12 images (Instagram accepte 20 images par carrousel)


def etoiles(n):
    return "★" * n + "☆" * (5 - n)


def main():
    env = os.getenv("MATCH_DATE", "").strip()
    jour = datetime.date.fromisoformat(env) if env else datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    date_txt = jour.strftime("%d/%m/%Y")
    pub = ROOT / "published"
    pub.mkdir(exist_ok=True)
    (pub / "latest_horoscope.txt").unlink(missing_ok=True)
    dossier = pub / "horoscope" / jour.isoformat()
    dossier.mkdir(parents=True, exist_ok=True)
    ia = textes_ia(jour)
    fiches = []
    for i, signe in enumerate(SIGNES):
        if ia and texte_ok(ia[i]["texte"]):
            texte, note = ia[i]["texte"], ia[i]["note"]
        else:
            texte, note = horoscope(i, jour), NOTES_SECOURS[(jour.toordinal() + i) % 12]
        slug = signe.lower().replace("é", "e").replace("è", "e")
        nom = f"{i + 1:02d}_{slug}.png"
        visuel(signe, date_txt, texte, dossier / nom, etoiles=note)
        fiches.append({"i": i, "signe": signe, "slug": slug, "nom": nom, "note": note})
    posts = []
    nb = 12 // PAR_CARROUSEL
    for p in range(nb):
        groupe = fiches[p * PAR_CARROUSEL:(p + 1) * PAR_CARROUSEL]
        lignes = "\n".join(f"{SYMBOLES[f['i']]}\ufe0f {f['signe']} {etoiles(f['note'])}" for f in groupe)
        tags = " ".join("#" + f["slug"] for f in groupe)
        caption = (f"🔮 Horoscope du {date_txt} ({p + 1}/{nb})\n\nLa note de la journée pour chaque signe, "
                   f"swipez pour lire le détail :\n\n{lignes}\n\n{tags} {HASHTAGS}")
        posts.append({"images": [f["nom"] for f in groupe], "caption": caption})
    posts.reverse()  # le carrousel Bélier-Vierge est publié en dernier : il apparaît en premier sur le profil
    (dossier / "manifest.json").write_text(json.dumps({"date": jour.isoformat(), "pause": 20, "posts": posts},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    (pub / "latest_horoscope.txt").write_text(f"published/horoscope/{jour.isoformat()}/manifest.json", encoding="utf-8")
    print(f"{len(posts)} horoscopes -> {dossier}")


if __name__ == "__main__":
    main()
