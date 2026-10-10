"""Visuel horoscope : fond crème, date verticale (Hug Me Tight), signe (Ellisha), texte (Malerose), logo Citasie."""
import pathlib, math
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent
S = 2048            # dessin en haute définition, réduit ensuite à 1080
BG, GOLD, INK = (253, 245, 230), (201, 162, 39), (10, 10, 10)
ETOILE = (211, 174, 55)  # #D3AE37
SORTIE = 1080


def _font(nom, taille):
    return ImageFont.truetype(str(ROOT / nom), taille)


def _wrap(d, texte, font, largeur):
    lignes, cur = [], ""
    for mot in texte.split():
        test = f"{cur} {mot}".strip()
        if d.textlength(test, font=font) <= largeur:
            cur = test
        else:
            lignes.append(cur); cur = mot
    return lignes + [cur] if cur else lignes


def _etoile(d, cx, cy, r, pleine):
    """Étoile à 5 branches : pleine (note obtenue) ou simple contour (note manquante)."""
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    if pleine:
        d.polygon(pts, fill=ETOILE)
    else:
        d.line(pts + [pts[0]], fill=ETOILE, width=5, joint="curve")


def visuel(signe, date_txt, texte, chemin, etoiles=None):
    img = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(img)

    # signe (haut gauche, à droite de la date)
    f = _font("Ellisha.ttf", 215)
    while d.textlength(signe, font=f) > 1550 and f.size > 120:
        f = _font("Ellisha.ttf", f.size - 10)
    d.text((200, 335), signe, font=f, fill=GOLD, anchor="ls")

    # date verticale, lue de bas en haut
    fd = _font("HugMeTight.ttf", 64)
    w = int(d.textlength(date_txt, font=fd)) + 20
    bande = Image.new("RGBA", (w, 90), (0, 0, 0, 0))
    ImageDraw.Draw(bande).text((10, 45), date_txt, font=fd, fill=INK, anchor="lm")
    bande = bande.rotate(90, expand=True)
    img.paste(bande, (50, 100), bande)

    # note du jour : 1 à 5 étoiles #D3AE37
    if etoiles:
        for k in range(5):
            _etoile(d, 245 + k * 92, 490, 38, k < etoiles)

    # texte centré : on réduit la police jusqu'à ce que le bloc tienne
    taille = 118
    while True:
        ft = _font("Malerose.otf", taille)
        lignes = _wrap(d, texte, ft, 1480)
        pas = int(taille * 1.3)
        if len(lignes) * pas <= 900 or taille <= 70:
            break
        taille -= 4
    # centrage exact de l'encre du texte entre le bas des étoiles (ou du nom) et le haut du logo Citasie
    haut_zone = 530 if etoiles else 440
    bas_zone = 1885
    haut = 0
    boites = [d.textbbox((S // 2, haut + i * pas), l, font=ft, anchor="mm") for i, l in enumerate(lignes)]
    encre_haut, encre_bas = min(b[1] for b in boites), max(b[3] for b in boites)
    haut = round((haut_zone + bas_zone) / 2 - (encre_haut + encre_bas) / 2)
    for i, l in enumerate(lignes):
        d.text((S // 2, haut + i * pas), l, font=ft, fill=INK, anchor="mm")

    # logo Citasie (extrait de ton visuel d'origine)
    logo = Image.open(ROOT / "citasie_logo.png").convert("RGBA")
    img.paste(logo, ((S - logo.width) // 2, 1885), logo)

    img = img.resize((SORTIE, SORTIE), Image.LANCZOS)
    img.save(chemin, quality=95)
    return chemin


if __name__ == "__main__":
    visuel("Bélier", "10/10/2026",
           "Votre curiosité est en éveil. De nouvelles rencontres ou idées stimulent votre esprit. "
           "Communication fluide, idéale pour négocier ou partager. Attention à la dispersion.", "test.png")
