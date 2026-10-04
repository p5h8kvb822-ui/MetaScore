# Notes des matchs de foot sur Instagram

Un post Instagram par match terminé (Ligue 1, Premier League, La Liga, Bundesliga, Serie A) :
image carrée avec logos, score, note /10 colorée et stats. Tourne chaque soir via GitHub Actions.

Fichiers : main.py (génère images + légendes), sources.py (données), rating.py (note et couleurs),
images.py (image carrée), post_instagram.py (publication), config.json (réglages).
Test : `"sample_mode": true` dans config.json = données de démonstration. Mettre `false` pour le réel.
Secret GitHub à créer : IG_ACCESS_TOKEN.
