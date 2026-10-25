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
