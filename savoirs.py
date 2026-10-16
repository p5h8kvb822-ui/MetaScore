"""3 publications « savoirs inutiles » par jour : photo 4:3 adaptée au thème (générée avec la clé OpenAI) + texte en dessous.
Écrit published/savoirs/<date>/ (images + manifest.json) et published/latest_savoirs.txt. Test d'une autre date : MATCH_DATE."""
import json, os, pathlib, datetime, re
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont
import ia
from visuel import _nettoyer

ROOT = pathlib.Path(__file__).resolve().parent
W, H, PHOTO_H = 1080, 1350, 810          # image 4:5 : photo 4:3 (1080x810) en haut, texte en dessous
BG, GOLD, INK = (0, 0, 0), (201, 162, 39), (255, 255, 255)   # fond noir, « le saviez-vous » doré, textes blancs
HASHTAGS = "#savoirinutile #lesavieztvous #culturegenerale #insolite #anecdote"

THEMES = ["animaux", "corps humain", "espace", "histoire", "science", "nature", "géographie", "nourriture",
          "langue française", "inventions", "océans", "records", "architecture", "musique", "sport"]

CONSIGNE = """Tu écris 3 publications « savoirs inutiles » pour un compte Instagram francophone : des faits surprenants, vrais et vérifiables,
qui donnent envie de dire « ah, je ne savais pas ! » et de partager. Date : {date}. Thèmes imposés, dans cet ordre : {themes}.
Exigences : faits bien établis (aucune légende urbaine, aucun chiffre incertain, pas de fait contesté), formulés avec précision ;
si un chiffre varie selon les sources, reste qualitatif. Chaque fait doit être inattendu et différent des classiques les plus rebattus.
Pour chaque publication fournis :
- "titre" : l'accroche, une phrase percutante (entre 30 et 75 caractères), sans point d'exclamation ;
- "texte" : l'explication en 2 ou 3 phrases courtes, claires, avec « vous » si besoin (entre 140 et 260 caractères) ;
- "legende" : le texte d'accompagnement Instagram, 2 à 3 phrases chaleureuses, 1 à 2 émojis, qui se termine par une question ou
  une invitation à taguer ou commenter (entre 120 et 330 caractères, sans hashtag) ;
- "photo" : une description EN ANGLAIS d'une photographie réaliste qui illustre exactement le sujet (sujet clair au centre, belle lumière,
  style photo de magazine), sans aucun texte ni lettre dans l'image, sans logo, sans personne réelle ou célèbre.
Réponds UNIQUEMENT par un tableau JSON de 3 objets {{"theme": ..., "titre": ..., "texte": ..., "legende": ..., "photo": ...}}."""

SECOURS = [
    ("Une pieuvre possède trois cœurs.", "Deux cœurs envoient le sang vers les branchies, le troisième vers le reste du corps. Son sang est bleu, grâce à une molécule à base de cuivre.", "animaux"),
    ("La tour Eiffel grandit quand il fait chaud.", "Sous l'effet de la chaleur, le métal se dilate : en été, la Dame de fer peut gagner une quinzaine de centimètres.", "architecture"),
    ("Une banane est une baie, mais pas une fraise.", "En botanique, une baie vient d'un seul ovaire et contient plusieurs graines à l'intérieur : la banane en est une, la fraise non.", "nature"),
    ("Sur Vénus, un jour dure plus longtemps qu'une année.", "Vénus met environ 243 jours terrestres pour tourner sur elle-même, mais seulement 225 pour faire le tour du Soleil.", "espace"),
    ("Les loutres de mer se tiennent la main pour dormir.", "Pour ne pas être emportées par le courant pendant leur sommeil, elles s'attachent souvent par les pattes.", "animaux"),
    ("Le miel peut se conserver pendant des années.", "Très peu d'eau, une forte acidité : la plupart des bactéries ne peuvent pas s'y développer, même longtemps après la récolte.", "nourriture"),
]
EMOJI_THEME = {"animaux": "🐙", "corps humain": "🫀", "espace": "🪐", "histoire": "🏛️", "science": "🔬", "nature": "🌿",
               "géographie": "🗺️", "nourriture": "🍯", "langue française": "📖", "inventions": "💡", "océans": "🌊",
               "records": "🏆", "architecture": "🏗️", "musique": "🎵", "sport": "⚽"}
POLICE_EMOJI = ["/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", "/usr/share/fonts/noto/NotoColorEmoji.ttf"]


def themes_du_jour(jour):
    n = jour.toordinal()
    return [THEMES[(n * 3 + k * 5) % len(THEMES)] for k in range(3)]


def generer_ia(themes, jour):
    if not ia.disponible():
        print("Pas de clé OPENAI_API_KEY : savoirs de secours.")
        return None
    try:
        brut = ia.demander(CONSIGNE.format(themes=", ".join(themes), date=jour.strftime("%d/%m/%Y")), 3000)
        liste = json.loads(re.search(r"\[.*\]", brut, re.S).group(0))
        if len(liste) != 3:
            raise ValueError("format inattendu")
        return [{k: " ".join(str(x.get(k, "")).split()) for k in ("titre", "texte", "legende", "photo")} for x in liste]
    except Exception as e:
        print(f"IA indisponible ({e}) : savoirs de secours.")
        return None


def valide(c):
    return 25 <= len(c["titre"]) <= 90 and 100 <= len(c["texte"]) <= 320 and 80 <= len(c["legende"]) <= 450


def _police(nom, taille):
    return ImageFont.truetype(str(ROOT / nom), taille)


def _lignes(d, texte, f, largeur):
    out, cur = [], ""
    for mot in texte.split():
        t = f"{cur} {mot}".strip()
        if d.textlength(t, font=f) <= largeur:
            cur = t
        else:
            out.append(cur); cur = mot
    return out + [cur] if cur else out


def _emoji(emoji):
    for chemin in POLICE_EMOJI:
        if pathlib.Path(chemin).exists():
            try:
                toile = Image.new("RGBA", (260, 160), (0, 0, 0, 0))
                ImageDraw.Draw(toile).text((10, 10), emoji, font=ImageFont.truetype(chemin, 109), embedded_color=True)
                return toile.crop(toile.getbbox())
            except Exception:
                return None
    return None


def photo_4_3(img):
    """Recadre au centre en 4:3 puis redimensionne en 1080x810."""
    w, h = img.size
    cible = 4 / 3
    if w / h > cible:
        nw = round(h * cible); img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = round(w / cible); img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return img.resize((W, PHOTO_H), Image.LANCZOS)


def panneau_secours(theme):
    """Si aucune photo n'est disponible : fond sombre et émoji du thème."""
    img = Image.new("RGB", (W, PHOTO_H), (28, 28, 30))
    e = _emoji(EMOJI_THEME.get(theme, "💡"))
    if e:
        e = e.resize((round(e.width * 360 / e.height), 360), Image.LANCZOS)
        img.paste(e, ((W - e.width) // 2, (PHOTO_H - e.height) // 2), e)
    return img


def dessiner(titre, texte, photo, chemin):
    titre, texte = _nettoyer(titre).upper(), _nettoyer(texte)   # titres en capitales
    img = Image.new("RGB", (W, H), BG)
    img.paste(photo, (0, 0))
    d = ImageDraw.Draw(img)
    marge, largeur = 60, W - 120
    zone_haut, zone_bas = PHOTO_H, H - 30
    # polices : on réduit jusqu'à ce que tout tienne
    t_titre, t_texte = 46, 34
    while True:
        ft, fx = _police("Poppins-Bold.ttf", t_titre), _police("Quote.ttf", t_texte)
        lt, lx = _lignes(d, titre, ft, largeur), _lignes(d, texte, fx, largeur)
        h_tot = 40 + 16 + len(lt) * int(t_titre * 1.2) + 18 + len(lx) * int(t_texte * 1.35)
        if h_tot <= zone_bas - zone_haut - 30 or (t_titre <= 30 and t_texte <= 26):
            break
        t_titre, t_texte = max(30, t_titre - 2), max(26, t_texte - 1)
    y = zone_haut + ((zone_bas - zone_haut) - h_tot) // 2
    d.text((W // 2, y + 14), "LE SAVIEZ-VOUS ?", font=_police("HugMeTight.ttf", 26), fill=GOLD, anchor="mm")
    y += 40 + 16
    for l in lt:
        d.text((W // 2, y), l, font=ft, fill=INK, anchor="mt"); y += int(t_titre * 1.2)
    y += 18
    for l in lx:
        d.text((W // 2, y), l, font=fx, fill=INK, anchor="mt"); y += int(t_texte * 1.35)
    img.save(chemin, quality=95)


def main():
    env = os.getenv("MATCH_DATE", "").strip()
    jour = datetime.date.fromisoformat(env) if env else datetime.datetime.now(ZoneInfo("Europe/Paris")).date()
    pub = ROOT / "published"
    pub.mkdir(exist_ok=True)
    (pub / "latest_savoirs.txt").unlink(missing_ok=True)
    dossier = pub / "savoirs" / jour.isoformat()
    dossier.mkdir(parents=True, exist_ok=True)
    themes = themes_du_jour(jour)
    gen = generer_ia(themes, jour)
    posts = []
    for i in range(3):
        if gen and valide(gen[i]):
            c, theme = gen[i], themes[i]
            photo = ia.generer_image(c["photo"] + " Photorealistic, no text, no letters, no watermark.") if c["photo"] else None
        else:
            titre, texte, theme = SECOURS[(jour.toordinal() * 3 + i) % len(SECOURS)]
            c = {"titre": titre, "texte": texte, "legende": f"{texte} Le saviez-vous ? Dites-le en commentaire 👇", "photo": ""}
            photo = None
        photo = photo_4_3(photo) if photo else panneau_secours(theme)
        nom = f"savoir_{i + 1}.png"
        dessiner(c["titre"], c["texte"], photo, dossier / nom)
        posts.append({"images": [nom], "caption": f"{c['legende']}\n\n{HASHTAGS}"})
    (dossier / "manifest.json").write_text(json.dumps({"date": jour.isoformat(), "pause": 20, "posts": posts},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    (pub / "latest_savoirs.txt").write_text(f"published/savoirs/{jour.isoformat()}/manifest.json", encoding="utf-8")
    print(f"{len(posts)} savoirs ({', '.join(themes)}) -> {dossier}")


if __name__ == "__main__":
    main()
