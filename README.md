# Les sources

Les sources des vidéos des chaînes YouTube **La mécanique du pire** et **Carte & Cachet**, rangées passage par passage.

Site : https://sidereaastra-collab.github.io

## Comment c'est fait

- `donnees/site.json` : les chaînes et la liste de leurs dossiers.
- `donnees/<chaîne>/<dossier>.json` : un dossier. Il contient les parties (identifiant YouTube, passages avec minutage, phrase de la vidéo, sources citées, prudences), les rapports officiels et la liste des sources.
- `outils/modeles/` : les gabarits des pages (Jinja2).
- `outils/construire.py` : fabrique les pages HTML à la racine du dépôt, que GitHub Pages publie telles quelles.

Pour reconstruire après une modification :

```
python3 outils/construire.py
```

Le script s'arrête si une source citée n'existe pas, et signale les sources déclarées mais jamais citées.

## Liens directs

- Une partie : `/mecanique-du-pire/titan/#partie-2`
- Un passage : `/mecanique-du-pire/titan/#p2-04-12` (partie 2, 04:12), qui s'ouvre tout seul.

Polices auto-hébergées sous licence SIL Open Font License (voir `assets/fonts`). Aucun cookie, aucune mesure d'audience.
