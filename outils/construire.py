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


LANGUES = {"EN": "en anglais", "FR": "", "DE": "en allemand", "ES": "en espagnol", "IT": "en italien", "JA": "en japonais", "NL": "en néerlandais", "PT": "en portugais"}


def minutage(t):
    """« 05:54 » devient « 5:54 », comme sur YouTube."""
    return t[1:] if len(t) == 5 and t[0] == "0" else t


def preparer_dossier(d, chaine, site):
    """Résout les sources citées, compte, et ajoute ce dont les pages ont besoin."""
    erreurs = []
    for cle in ("illustration", "image_entete", "image_alt", "avertissement", "titre_rapports"):
        d.setdefault(cle, "")
    d.setdefault("suivi", None)
    d["chaine"] = chaine
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
        langue = LANGUES.get(b.get("langue", "EN"), "")
        if langue:
            morceaux.append(langue)
        if b.get("pdf"):
            morceaux.append("PDF")
        if b.get("url"):
            urls.add(b["url"])
        return {"nom": b["nom"], "url": b.get("url", ""), "officielle": bool(b.get("officielle")), "meta": ", ".join(morceaux)}

    passages = {}
    for p in d["parties"]:
        for s in p["passages"]:
            s["secondes"] = secondes(s["t"])
            s["ancre"] = "p%d-%s" % (p["numero"], s["t"].replace(":", "-"))
            s.setdefault("nuances", [])
            s["corrections"] = []
            passages[(p["numero"], s["t"])] = (p, s)
            n = 0
            for it in s["items"]:
                it["sources"] = [source(*x) for x in it["sources"]]
                n += len(it["sources"])
            s["nb"] = n

    # Corrections : rattachées au passage concerné quand il est indiqué.
    for c in d.get("corrections", []):
        c.setdefault("texte", "")
        c.setdefault("dit", "")
        c.setdefault("juste", "")
        c["sources"] = [source(*x) for x in c.get("sources", [])]
        c["lien_video"] = ""
        c["lien_passage"] = "/%s/%s/#corrections" % (chaine["slug"], d["slug"])
        c["dossier"] = d
        if c.get("passage"):
            cle = (c.get("partie", 1), c["passage"])
            if cle not in passages:
                erreurs.append("correction : passage introuvable %s dans %s" % (cle, d["slug"]))
                continue
            p, s = passages[cle]
            s["corrections"].append(c)
            c["ancre"] = s["ancre"]
            c["lien_passage"] = "/%s/%s/#%s" % (chaine["slug"], d["slug"], s["ancre"])
            t = c.get("t") or s["t"]
            c["t_affiche"] = minutage(t)
            c["lien_video"] = "https://youtu.be/%s?t=%d" % (p["youtube"], secondes(t))
    d["nb_corrections"] = len(d.get("corrections", []))

    # Mise à jour publiée après la vidéo (ce qui a changé depuis), avec ses sources.
    if d["suivi"]:
        for pt in d["suivi"]["points"]:
            pt["sources"] = [source(*x) for x in pt["sources"]]

    for r in d.get("rapports", []):
        r["liens"] = [{"label": label, "url": source(cle)["url"]} for label, cle in r["liens"]]
    d["plus_loin"] = [dict(source(cle), label=label) for cle, label in d.get("plus_loin", [])]
    d["nb_sources"] = len(urls)
    titre = "%s, %s %s de %s : les sources" % (d["titre"], chaine["unite"].lower(), d["numero"], chaine["nom"])
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
    env.filters["en_lettres"] = lambda n: {1: "une", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq"}.get(n, str(n))
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
        if not c["liste"]:
            continue
        for d in c["liste"]:
            chemin = "/%s/%s/" % (c["slug"], d["slug"])
            html = env.get_template("dossier.html").render(
                commun, d=d, chaine=c, theme=c["theme"], chemin=chemin, titre_page=d["titre_page"],
                description=d["description"], image=d.get("image_partage"), script=True)
            ecrire(chemin.strip("/") + "/index.html", html)
        chemin = "/%s/" % c["slug"]
        mot = c["titre_liste"][4:].lower()  # « Les dossiers » → « dossiers »
        html = env.get_template("chaine.html").render(
            commun, chaine=c, theme=c["theme"], chemin=chemin,
            titre_page="%s · les %s et leurs sources" % (c["nom"], mot),
            description="Les sources des %s de %s, passage par passage." % (mot, c["nom"]))
        ecrire(chemin.strip("/") + "/index.html", html)

    ecrire("index.html", env.get_template("accueil.html").render(
        commun, theme="neutre", chemin="/", titre_page="Les sources · La mécanique du pire et Carte & Cachet",
        description="Les sources des vidéos de La mécanique du pire et de Carte & Cachet, passage par passage."))
    # Toutes les corrections du site, les plus récentes d'abord.
    mois = {"janv.": 1, "févr.": 2, "mars": 3, "avr.": 4, "mai": 5, "juin": 6, "juil.": 7, "juill.": 7,
            "août": 8, "sept.": 9, "oct.": 10, "nov.": 11, "déc.": 12}

    def cle_date(c):
        j, m, a = c["date"].split()
        return (int(a), mois.get(m, 0), int(j))

    for c in site["chaines"]:
        c["corrections"] = sorted([x for d in c["liste"] for x in d.get("corrections", [])], key=cle_date, reverse=True)
    ecrire("corrections/index.html", env.get_template("corrections.html").render(
        commun, theme="neutre", chemin="/corrections/", titre_page="Corrections · Les sources",
        description="Les erreurs relevées dans les vidéos de La mécanique du pire et de Carte & Cachet après leur mise en ligne, et ce qui est juste."))
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
