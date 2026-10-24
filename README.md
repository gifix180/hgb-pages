# hgb-pages

Pages privées du projet HGB, protégées par mot de passe.

- `index.html` : page « Montes et partants », **chiffrée** (AES-256-GCM, clé tirée du mot de passe). Déposée par le
  dépôt privé du projet après chaque passage du suivi.
- `pmu.enc` : relevé PMU du jour (données publiques du PMU), **chiffré** de la même façon ; mis à jour toutes les
  30 minutes pendant les courses par `releve.py` (`.github/workflows/releve.yml`).

Ce dépôt ne contient aucune donnée en clair : sans le mot de passe, la page n'affiche qu'un champ « mot de passe ».
L'historique est volontairement réduit à un seul commit (les fichiers sont remplacés à chaque mise à jour).
