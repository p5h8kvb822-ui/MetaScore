# Notes des matchs de foot sur Instagram

Un carrousel Instagram par match terminé (2 images carrées : le match, puis le meilleur joueur).
Compétitions : Ligue 1, Premier League, La Liga, Bundesliga, Serie A, Ligue des champions, Europa League, Conference League.
Données : API-Football (api-sports.io). Tourne chaque soir via GitHub Actions.

Fichiers : main.py (génère images + légendes), sources.py (données), rating.py (note et couleurs),
images.py (images carrées), post_instagram.py (publication), config.json (réglages).
Secrets GitHub à créer : API_FOOTBALL_KEY et IG_ACCESS_TOKEN.
Test : "sample_mode": true dans config.json = données de démonstration (aucun accès réseau).

Prédictions du jour (sports.bzzoiro.com) : pronostics.py + workflow pronostics.yml (07h00 UTC), secret BSD_API_KEY.
Légendes : legende.py (notes) et pronostics.py (prédictions).
