/* Site des sources : choix de la partie, ouverture des passages, liens directs.
   Sans JavaScript, la page reste complète : les deux parties s'affichent l'une après l'autre. */
(function () {
  "use strict";
  var parts = Array.prototype.slice.call(document.querySelectorAll(".part"));
  if (!parts.length) { return; }
  var picks = Array.prototype.slice.call(document.querySelectorAll(".pick"));

  function partById(id) {
    for (var i = 0; i < parts.length; i++) { if (parts[i].id === id) { return parts[i]; } }
    return null;
  }

  function show(id) {
    var target = partById(id);
    if (!target) { return false; }
    parts.forEach(function (p) { p.hidden = p !== target; });
    picks.forEach(function (a) {
      a.setAttribute("aria-current", a.getAttribute("href") === "#" + id ? "true" : "false");
    });
    return true;
  }

  function syncButton(part) {
    var btn = part.querySelector(".btn-all");
    if (!btn) { return; }
    var all = part.querySelectorAll("details.pas");
    var open = part.querySelectorAll("details.pas[open]");
    btn.textContent = all.length && open.length === all.length ? "Tout fermer" : "Tout ouvrir";
  }

  function fromHash(scroll) {
    var h = "";
    try { h = decodeURIComponent(window.location.hash.slice(1)); } catch (e) { h = ""; }
    if (!h) { show(parts[0].id); return; }
    if (show(h)) {
      var top = document.getElementById("sources");
      if (scroll && top) { top.scrollIntoView({ block: "start" }); }
      return;
    }
    var el = document.getElementById(h);
    if (el && el.matches && el.matches("details.pas")) {
      var part = el.closest(".part");
      if (part) { show(part.id); }
      el.open = true;
      if (part) { syncButton(part); }
      if (scroll) { el.scrollIntoView({ block: "start" }); }
      return;
    }
    show(parts[0].id);
  }

  picks.forEach(function (a) {
    a.addEventListener("click", function (ev) {
      var id = a.getAttribute("href").slice(1);
      if (show(id)) {
        ev.preventDefault();
        if (window.history && window.history.replaceState) { window.history.replaceState(null, "", "#" + id); }
      }
    });
  });

  parts.forEach(function (part) {
    var btn = part.querySelector(".btn-all");
    if (btn) {
      btn.hidden = false;
      btn.addEventListener("click", function () {
        var all = part.querySelectorAll("details.pas");
        var open = part.querySelectorAll("details.pas[open]");
        var target = !(all.length && open.length === all.length);
        Array.prototype.forEach.call(all, function (d) { d.open = target; });
        syncButton(part);
      });
    }
    Array.prototype.forEach.call(part.querySelectorAll("details.pas"), function (d) {
      d.addEventListener("toggle", function () { syncButton(part); });
    });
    syncButton(part);
  });

  window.addEventListener("hashchange", function () { fromHash(true); });
  window.addEventListener("beforeprint", function () {
    Array.prototype.forEach.call(document.querySelectorAll("details.pas"), function (d) { d.open = true; });
  });
  fromHash(true);
})();

/* Lecteur sur la page. Rien n'est chargé depuis YouTube avant un clic : sur la miniature en tête de page
   (le lecteur prend sa place), ou sur « Regarder ici ». Lecteur de youtube-nocookie.com (confidentialité renforcée),
   sans lecture automatique : c'est le bouton de lecture de YouTube qui lance la vidéo, ce qui la compte comme une vue
   (une lecture lancée par le script ne compte pas).
   Quand la tête de page sort de l'écran pendant la lecture, le lecteur se détache en bas à droite (sans être déplacé
   dans la page, ce qui le rechargerait), puis reprend sa place quand on remonte.
   Quand il est ouvert, « Revoir ce passage » avance le lecteur au bon moment au lieu d'ouvrir YouTube : par le
   lecteur lui-même si la lecture a déjà été lancée, sinon en le rechargeant calé sur le passage. */
(function () {
  "use strict";
  var boutons = Array.prototype.slice.call(document.querySelectorAll(".btn-voir"));
  var tete = document.querySelector(".hero-video");
  if ((!boutons.length && !tete) || !window.postMessage) { return; }
  var ORIGINE = "https://www.youtube-nocookie.com";
  var lecteur = null, cadre = null, titre = null, actuel = null, enTete = false, visible = true;

  function creer() {
    lecteur = document.createElement("div");
    lecteur.className = "lecteur";
    lecteur.setAttribute("role", "region");
    lecteur.setAttribute("aria-label", "Lecteur de la vidéo");
    var barre = document.createElement("div");
    barre.className = "lecteur-barre";
    titre = document.createElement("span");
    titre.className = "lecteur-titre";
    var fermer = document.createElement("button");
    fermer.type = "button";
    fermer.className = "lecteur-fermer";
    fermer.textContent = "Fermer";
    fermer.addEventListener("click", fermerLecteur);
    barre.appendChild(titre);
    barre.appendChild(fermer);
    cadre = document.createElement("div");
    cadre.className = "lecteur-cadre";
    lecteur.appendChild(barre);
    lecteur.appendChild(cadre);
  }

  // Le lecteur flotte en bas à droite quand il n'a pas de place en tête de page, ou quand la tête est hors de l'écran.
  function placer() {
    if (!lecteur || !actuel) { return; }
    var flotte = !enTete || !visible;
    lecteur.classList.toggle("flottant", flotte);
    document.body.classList.toggle("lecteur-flottant", flotte);
  }

  function charger(id, t, nom) {
    if (!lecteur) { creer(); }
    var place = tete && tete.getAttribute("data-video") === id;
    var cadreTete = tete ? tete.querySelector(".hero-cadre") : null;
    if (place && lecteur.parentNode !== cadreTete) { cadreTete.appendChild(lecteur); }
    else if (!place && lecteur.parentNode !== document.body) { document.body.appendChild(lecteur); }
    enTete = !!place;
    if (tete) { tete.classList.toggle("actif", enTete); }
    var f = document.createElement("iframe");
    f.src = ORIGINE + "/embed/" + encodeURIComponent(id) + "?enablejsapi=1&rel=0&playsinline=1&origin=" +
      encodeURIComponent(window.location.origin) + (t > 0 ? "&start=" + t : "");
    f.title = nom + " (lecteur YouTube)";
    f.setAttribute("allow", "encrypted-media; picture-in-picture; fullscreen");
    f.setAttribute("allowfullscreen", "");
    f.setAttribute("referrerpolicy", "strict-origin-when-cross-origin");
    f.addEventListener("load", function () {
      // Demande au lecteur d'envoyer son état (lecture, pause…) à la page.
      if (f.contentWindow) { f.contentWindow.postMessage(JSON.stringify({ event: "listening", id: 1, channel: "widget" }), ORIGINE); }
    });
    cadre.innerHTML = "";
    cadre.appendChild(f);
    titre.textContent = nom;
    actuel = { id: id, cadre: f, lance: false };
    lecteur.hidden = false;
    document.body.classList.add("avec-lecteur");
    boutons.forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-video") === id ? "true" : "false"); });
    placer();
  }

  function commande(func, args) {
    if (actuel && actuel.cadre.contentWindow) {
      actuel.cadre.contentWindow.postMessage(JSON.stringify({ event: "command", func: func, args: args || [] }), ORIGINE);
    }
  }

  function fermerLecteur() {
    cadre.innerHTML = "";
    actuel = null;
    lecteur.hidden = true;
    lecteur.classList.remove("flottant");
    if (tete) { tete.classList.remove("actif"); }
    document.body.classList.remove("avec-lecteur", "lecteur-flottant");
    boutons.forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
  }

  window.addEventListener("message", function (ev) {
    if (ev.origin !== ORIGINE || !actuel || ev.source !== actuel.cadre.contentWindow) { return; }
    var d = null;
    try { d = typeof ev.data === "string" ? JSON.parse(ev.data) : ev.data; } catch (e) { return; }
    if (!d) { return; }
    var etat = d.event === "onStateChange" ? d.info : (d.info && typeof d.info.playerState === "number" ? d.info.playerState : null);
    if (etat === 1 || etat === 2 || etat === 3) { actuel.lance = true; } // lecture, pause, chargement : la lecture a commencé
  });

  if (tete) {
    Array.prototype.forEach.call(tete.querySelectorAll(".hero-lien, .hero-lire"), function (lien) {
      lien.addEventListener("click", function (ev) {
        ev.preventDefault();
        if (actuel && actuel.id === tete.getAttribute("data-video")) { return; }
        charger(tete.getAttribute("data-video"), 0, tete.getAttribute("data-titre"));
      });
    });
    if (window.IntersectionObserver) {
      new IntersectionObserver(function (entrees) {
        visible = entrees[0].isIntersecting;
        placer();
      }, { threshold: 0.25 }).observe(tete.querySelector(".hero-cadre"));
    }
  }

  boutons.forEach(function (b) {
    b.hidden = false;
    b.setAttribute("aria-pressed", "false");
    b.addEventListener("click", function () {
      var id = b.getAttribute("data-video");
      if (actuel && actuel.id === id) { fermerLecteur(); return; }
      charger(id, 0, b.getAttribute("data-titre"));
    });
  });

  document.addEventListener("click", function (ev) {
    var a = ev.target.closest ? ev.target.closest("a.again[data-video]") : null;
    if (!a || !actuel) { return; }
    ev.preventDefault();
    var t = parseInt(a.getAttribute("data-t"), 10) || 0;
    if (actuel.id === a.getAttribute("data-video") && actuel.lance) { commande("seekTo", [t, true]); }
    else { charger(a.getAttribute("data-video"), t, a.getAttribute("data-titre")); }
  });
})();
