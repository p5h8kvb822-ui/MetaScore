"""3 citations par jour (thèmes : Amour, Amitié, Bonheur, Famille ; 3 thèmes sur 4 chaque jour, en rotation).
Textes écrits par l'IA (clé ANTHROPIC_API_KEY) ; sinon petite banque de secours.
Écrit published/citations/<date>/ (images + manifest.json) et published/latest_citations.txt. Test d'une autre date : MATCH_DATE."""
import json, os, pathlib, datetime, re
from zoneinfo import ZoneInfo
import ia
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
THEMES = ["Amour", "Amitié", "Bonheur", "Famille"]
HASHTAGS = "#quote #citation #Amour #Amitié #Bonheur"
INK = (10, 10, 10)
S, SORTIE = 2048, 1080

CONSIGNE = """Tu écris 3 citations ORIGINALES (inventées par toi, jamais attribuées à une personne réelle, jamais copiées d'un auteur)
pour un compte Instagram francophone de citations, avec un texte d'accompagnement pour chacune.
Thèmes imposés, dans cet ordre : {themes}. Date : {date}.
Citation : une seule phrase ou deux courtes, belle, juste, facile à retenir et à partager, entre 60 et 160 caractères, sans guillemets,
sans nom d'auteur, sans hashtag, sans émoji. Chaque citation doit sonner différemment (image, contraste, formule inattendue).
Texte d'accompagnement : 2 à 4 phrases chaleureuses en français qui prolongent la citation, parlent directement au lecteur
(« vous »), puis terminent par une question ou une invitation à taguer ou à commenter. Entre 150 et 380 caractères, 0 à 2 émojis,
sans hashtag (ils sont ajoutés ensuite).
Réponds UNIQUEMENT par un tableau JSON de 3 objets {{"theme": ..., "citation": ..., "texte": ...}}."""

SECOURS = {
    "Amour": [("Aimer, ce n'est pas se regarder l'un l'autre, c'est regarder ensemble dans la même direction.", ""),
              ("L'amour ne se compte pas en grands gestes, mais en petites attentions qui reviennent chaque jour.", ""),
              ("Le plus beau des voyages commence quand on trouve quelqu'un avec qui se taire est aussi doux que parler.", ""),
              ("On ne tombe pas amoureux d'une perfection, mais d'une façon unique d'être imparfait.", "")],
    "Amitié": [("Un vrai ami est celui qui reste quand tout le monde a trouvé une bonne excuse pour partir.", ""),
               ("Certaines amitiés n'ont pas besoin de nouvelles : elles reprennent comme si l'on s'était quittés hier.", ""),
               ("Les amis sont la famille que le cœur choisit.", ""),
               ("Un ami sincère vous dit la vérité avec douceur et vous aime malgré elle.", "")],
    "Bonheur": [("Le bonheur n'est pas une destination, c'est la manière dont on voyage.", ""),
                ("Les petits bonheurs sont des grains de lumière : il suffit de les ramasser un à un.", ""),
                ("Être heureux, c'est souvent remarquer ce que l'on avait déjà.", ""),
                ("Un sourire offert est un bonheur qui revient toujours avec des intérêts.", "")],
    "Famille": [("La famille, c'est l'endroit où l'on peut enlever son armure et rester soi-même.", ""),
                ("On n'hérite pas seulement d'un nom, mais d'une façon d'aimer.", ""),
                ("Une maison devient un foyer le jour où l'on y entend des rires qui nous ressemblent.", ""),
                ("Les racines d'une famille sont invisibles, mais ce sont elles qui nous font tenir debout.", "")],
}
TEXTES_SECOURS = {
    "Amour": "L'amour se cache souvent dans les gestes les plus simples. À qui allez-vous le montrer aujourd'hui ? 💛",
    "Amitié": "Les vrais amis sont rares et précieux. Taguez celui ou celle qui compte pour vous 🤍",
    "Bonheur": "Le bonheur se joue dans les petits instants. Quel est le vôtre aujourd'hui ? ☀️",
    "Famille": "La famille, c'est notre premier refuge. Dédiez cette citation à quelqu'un des vôtres 🏡",
}


def themes_du_jour(jour):
    n = jour.toordinal()
    return [t for k, t in enumerate(THEMES) if k != n % 4]


def generer_ia(themes, jour):
    if not ia.disponible():
        print("Pas de clé OPENAI_API_KEY : citations de secours.")
        return None
    try:
        brut = ia.demander(CONSIGNE.format(themes=", ".join(themes), date=jour.strftime("%d/%m/%Y")), 2000)
        liste = json.loads(re.search(r"\[.*\]", brut, re.S).group(0))
        if len(liste) != 3:
            raise ValueError("format inattendu")
        return [{"citation": " ".join(str(x["citation"]).split()).strip("«» \""), "texte": str(x["texte"]).strip()} for x in liste]
    except Exception as e:
        print(f"IA indisponible ({e}) : citations de secours.")
        return None


def secours(theme, jour):
    liste = SECOURS[theme]
    return {"citation": liste[jour.toordinal() % len(liste)][0], "texte": TEXTES_SECOURS[theme]}


def dessiner(citation, chemin):
    img = Image.open(ROOT / "fond_citation.png").convert("RGB").resize((S, S), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    taille = 130
    while True:
        f = ImageFont.truetype(str(ROOT / "HugMeTight.ttf"), taille)
        lignes, cur = [], ""
        for mot in citation.split():
            t = f"{cur} {mot}".strip()
            if d.textlength(t, font=f) <= 1400:
                cur = t
            else:
                lignes.append(cur); cur = mot
        lignes.append(cur)
        pas = int(taille * 1.3)
        if len(lignes) * pas <= 1150 or taille <= 70:
            break
        taille -= 4
    # centrage exact de l'encre du texte entre la ligne dorée du haut et celle du bas
    boites = [d.textbbox((S // 2, i * pas), l, font=f, anchor="mm") for i, l in enumerate(lignes)]
    encre_haut, encre_bas = min(b[1] for b in boites), max(b[3] for b in boites)
    haut = round((165 + 1895) / 2 - (encre_haut + encre_bas) / 2)
    for i, l in enumerate(lignes):
        d.text((S // 2, haut + i * pas), l, font=f, fill=INK, anchor="mm")
    img.resize((SORTIE, SORTIE), Image.LANCZOS).save(chemin, quality=95)


def main():
    env = os.getenv("MATCH_DATE", "").strip()
    jour = datetime.date.fromisoformat(env) if env else datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    pub = ROOT / "published"
    pub.mkdir(exist_ok=True)
    (pub / "latest_citations.txt").unlink(missing_ok=True)
    dossier = pub / "citations" / jour.isoformat()
    dossier.mkdir(parents=True, exist_ok=True)
    themes = themes_du_jour(jour)
    ia = generer_ia(themes, jour)
    posts = []
    for i, theme in enumerate(themes):
        c = ia[i] if ia and 30 <= len(ia[i]["citation"]) <= 220 and 60 <= len(ia[i]["texte"]) <= 700 else secours(theme, jour)
        nom = f"citation_{i + 1}_{theme.lower().replace('é', 'e')}.png"
        dessiner(c["citation"], dossier / nom)
        posts.append({"images": [nom], "caption": f"{c['texte']}\n\n{HASHTAGS}"})
    (dossier / "manifest.json").write_text(json.dumps({"date": jour.isoformat(), "pause": 20, "posts": posts},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    (pub / "latest_citations.txt").write_text(f"published/citations/{jour.isoformat()}/manifest.json", encoding="utf-8")
    print(f"{len(posts)} citations ({', '.join(themes)}) -> {dossier}")


if __name__ == "__main__":
    main()
