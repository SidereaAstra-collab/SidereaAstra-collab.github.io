#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Construit le site des sources à partir des fichiers de `donnees/`.

Utilisation, depuis la racine du dépôt :
    python3 outils/construire.py

Chaque dossier est un fichier `donnees/<chaine>/<slug>.json`. Le script vérifie
que chaque source citée existe, compte les sources, puis écrit les pages HTML
à la racine du dépôt (c'est elle que GitHub Pages publie).
"""
import json
import os
import re
import sys
import time

from jinja2 import Environment, FileSystemLoader, StrictUndefined

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DONNEES = os.path.join(RACINE, "donnees")
MODELES = os.path.join(RACINE, "outils", "modeles")


def lire(chemin):
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def ecrire(chemin_relatif, contenu):
    chemin = os.path.join(RACINE, chemin_relatif)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)
    print("  écrit", chemin_relatif)


def secondes(t):
    morceaux = [int(x) for x in t.split(":")]
    s = 0
    for m in morceaux:
        s = s * 60 + m
    return s


def preparer_dossier(d, chaine, site):
    """Résout les sources citées, compte, et ajoute ce dont les pages ont besoin."""
    erreurs = []
    S = d["sources"]
    urls = set()

    def source(cle, precision=None):
        if cle not in S:
            erreurs.append("source inconnue : " + cle)
            return {"nom": cle, "url": "", "officielle": False, "meta": ""}
        b = S[cle]
        morceaux = [b["domaine"]]
        if precision:
            morceaux.append(precision)
        morceaux.append(b.get("langue", "EN"))
        if b.get("pdf"):
            morceaux.append("PDF")
        if b.get("url"):
            urls.add(b["url"])
        return {"nom": b["nom"], "url": b.get("url", ""), "officielle": bool(b.get("officielle")), "meta": " · ".join(morceaux)}

    for p in d["parties"]:
        for s in p["passages"]:
            s["secondes"] = secondes(s["t"])
            s["ancre"] = "p%d-%s" % (p["numero"], s["t"].replace(":", "-"))
            s.setdefault("prudences", [])
            n = 0
            for it in s["items"]:
                it["sources"] = [source(*x) for x in it["sources"]]
                n += len(it["sources"])
            s["nb"] = n
    for r in d.get("rapports", []):
        r["liens"] = [{"label": label, "url": source(cle)["url"]} for label, cle in r["liens"]]
    d["plus_loin"] = [dict(source(cle), label=label) for cle, label in d.get("plus_loin", [])]
    d["nb_sources"] = len(urls)
    titre = "%s, Dossier N° %s · %s : les sources" % (d["titre"], d["numero"], chaine["nom"])
    d["lien_signaler"] = "%s/issues/new?title=%s" % (site["depot"], (d["titre"] + " : ").replace(" ", "%20").replace(":", "%3A"))
    d["titre_page"] = titre
    # Les sources déclarées mais jamais citées sont signalées (pas bloquantes).
    citees = set()
    texte = json.dumps(lire(d["_fichier"]), ensure_ascii=False)
    for cle in S:
        if re.search(r'\["%s"' % re.escape(cle), texte):
            citees.add(cle)
    for cle in S:
        if cle not in citees:
            print("  attention : source déclarée mais jamais citée :", cle)
    return erreurs


def main():
    site = lire(os.path.join(DONNEES, "site.json"))
    env = Environment(loader=FileSystemLoader(MODELES), undefined=StrictUndefined,
                      autoescape=True, trim_blocks=False, lstrip_blocks=False)
    env.globals["site"] = site
    env.filters["nbsp"] = lambda x: str(x).replace(" ", "\u00a0")
    version = time.strftime("%Y%m%d%H%M")
    commun = {"version": version, "image": None, "script": False}
    erreurs = []

    for c in site["chaines"]:
        c["liste"] = []
        for slug in c["dossiers"]:
            fichier = os.path.join(DONNEES, c["slug"], slug + ".json")
            d = lire(fichier)
            d["_fichier"] = fichier
            erreurs += preparer_dossier(d, c, site)
            c["liste"].append(d)

    if erreurs:
        print("\n".join(erreurs))
        sys.exit(1)

    for c in site["chaines"]:
        if c["theme"] == "mdp":
            for d in c["liste"]:
                chemin = "/%s/%s/" % (c["slug"], d["slug"])
                html = env.get_template("dossier.html").render(
                    commun, d=d, chaine=c, theme="mdp", chemin=chemin, titre_page=d["titre_page"],
                    description=d["description"], image=d.get("image_partage"), script=True)
                ecrire(chemin.strip("/") + "/index.html", html)
            chemin = "/%s/" % c["slug"]
            html = env.get_template("chaine.html").render(
                commun, chaine=c, theme="mdp", chemin=chemin,
                titre_page="La mécanique du pire · les dossiers et leurs sources",
                description="Les sources des dossiers de La mécanique du pire, passage par passage.")
            ecrire(chemin.strip("/") + "/index.html", html)

    ecrire("index.html", env.get_template("accueil.html").render(
        commun, theme="neutre", chemin="/", titre_page="Les sources · La mécanique du pire et Carte & Cachet",
        description="Les sources des vidéos de La mécanique du pire et de Carte & Cachet, passage par passage."))
    ecrire("mentions-legales/index.html", env.get_template("mentions.html").render(
        commun, theme="neutre", chemin="/mentions-legales/", titre_page="Mentions légales · Les sources",
        description="Mentions légales du site des sources."))
    ecrire("404.html", env.get_template("404.html").render(
        commun, theme="neutre", chemin="/404.html", titre_page="Page introuvable · Les sources",
        description="Page introuvable."))
    for c in site["chaines"]:
        for d in c["liste"]:
            print("%s · %s : %d sources en ligne" % (c["nom"], d["titre"], d["nb_sources"]))


if __name__ == "__main__":
    main()
