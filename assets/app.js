(function () {
  "use strict";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var root = document.documentElement;
  var slug = document.body.dataset.slug;

  function load(key, fallback) {
    try { var v = localStorage.getItem(key); return v == null ? fallback : JSON.parse(v); } catch (e) { return fallback; }
  }
  function save(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* storage blocked: progress lives for this page view only */ }
  }

  /* ---------- theme ---------- */
  $("#theme-btn").addEventListener("click", function () {
    var dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    var next = dark ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem("sdh-theme", next); } catch (e) {}
  });

  /* ---------- mobile drawer ---------- */
  var sidebar = $("#sidebar"), scrim = $("#scrim"), menuBtn = $("#menu-btn");
  function drawer(open) {
    sidebar.classList.toggle("open", open);
    scrim.hidden = !open;
    menuBtn.setAttribute("aria-expanded", String(open));
  }
  menuBtn.addEventListener("click", function () { drawer(!sidebar.classList.contains("open")); });
  scrim.addEventListener("click", function () { drawer(false); });
  var cur = $('.sidebar a[aria-current="page"]');
  if (cur) cur.scrollIntoView({ block: "center" });

  /* ---------- progress ---------- */
  var done = load("sdh-done", {});
  var parts = (window.SDH_META || { parts: [] }).parts;
  function renderProgress() {
    $$("a[data-slug]").forEach(function (a) { a.classList.toggle("is-done", !!done[a.dataset.slug]); });
    var total = 0, totalDone = 0;
    parts.forEach(function (slugs, i) {
      var n = slugs.filter(function (s) { return done[s]; }).length;
      total += slugs.length; totalDone += n;
      $$('[data-part="' + i + '"]').forEach(function (el) {
        el.textContent = el.classList.contains("nav-count") ? (n ? n + "/" + slugs.length : "") : n + " / " + slugs.length;
      });
      var bar = $('[data-bar="' + i + '"]');
      if (bar) bar.style.width = (100 * n / slugs.length) + "%";
    });
    var oc = $("#overall-count"), ob = $("#overall-bar");
    if (oc) oc.textContent = totalDone + " / " + total;
    if (ob) ob.style.width = (total ? 100 * totalDone / total : 0) + "%";
    var btn = $("#done-btn");
    if (btn) {
      btn.setAttribute("aria-pressed", String(!!done[slug]));
      $(".done-label", btn).textContent = done[slug] ? "Completed" : "Mark as done";
    }
  }
  var doneBtn = $("#done-btn");
  if (doneBtn) doneBtn.addEventListener("click", function () {
    if (done[slug]) delete done[slug]; else done[slug] = Date.now();
    save("sdh-done", done);
    renderProgress();
  });
  renderProgress();

  /* ---------- on-this-page TOC + scroll spy ---------- */
  var toc = $("#toc");
  if (toc) {
    var heads = $$(".article-body h2[id], .article-body h3[id]");
    heads.forEach(function (h) {
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent;
      if (h.tagName === "H3") a.className = "sub";
      toc.appendChild(a);
    });
    var links = $$("a", toc);
    var spy = function () {
      var y = window.scrollY + innerHeight * 0.3, active = 0;
      heads.forEach(function (h, i) { if (h.offsetTop <= y) active = i; });
      links.forEach(function (a, i) { a.classList.toggle("active", i === active); });
    };
    if (heads.length) { addEventListener("scroll", spy, { passive: true }); spy(); }
  }

  /* ---------- copy buttons ---------- */
  $$(".copy-btn").forEach(function (b) {
    b.addEventListener("click", function () {
      var code = b.closest(".code").querySelector("code").innerText;
      var ok = function () { b.textContent = "Copied"; setTimeout(function () { b.textContent = "Copy"; }, 1400); };
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(ok, function () {
        var r = document.createRange(); r.selectNodeContents(b.closest(".code").querySelector("pre"));
        var s = getSelection(); s.removeAllRanges(); s.addRange(r);
      });
    });
  });

  /* ---------- search ---------- */
  var index = null;   // loaded on first open so normal page views skip the download
  var modal = $("#search-modal"), input = $("#search-input"), list = $("#search-results");
  var sel = 0, results = [];
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function mark(text, words) {
    var out = esc(text);
    words.forEach(function (w) { if (w) out = out.replace(new RegExp("(" + w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "ig"), "<mark>$1</mark>"); });
    return out;
  }
  function score(e, words) {
    var s = 0, match = "";
    for (var i = 0; i < words.length; i++) {
      var w = words[i], ws = 0;
      if (e.t.toLowerCase().indexOf(w) >= 0) ws = 10;
      else {
        var h = e.h.concat(e.k).find(function (x) { return x.toLowerCase().indexOf(w) >= 0; });
        if (h) { ws = 4; if (!match) match = h; }
        else if (e.d.toLowerCase().indexOf(w) >= 0) ws = 2;
        else if (e.x.indexOf(w) >= 0) ws = 1;
      }
      if (!ws) return null;
      s += ws;
    }
    return { e: e, s: s, m: match };
  }
  function runSearch() {
    if (!index) return;
    var q = input.value.trim().toLowerCase();
    var words = q.split(/\s+/).filter(Boolean);
    results = words.length
      ? index.map(function (e) { return score(e, words); }).filter(Boolean).sort(function (a, b) { return b.s - a.s; }).slice(0, 12)
      : index.slice(0, 8).map(function (e) { return { e: e, m: "" }; });
    sel = 0;
    list.innerHTML = results.length ? results.map(function (r, i) {
      return '<li role="option" aria-selected="' + (i === 0) + '"><a href="' + r.e.s + '.html' + '">' +
        '<span class="sr-t">' + mark(r.e.t, words) + '</span><span class="sr-p">' + esc(r.e.p) + '</span>' +
        '<span class="sr-d">' + mark(r.e.d, words) + '</span>' +
        (r.m ? '<span class="sr-m">Section: ' + mark(r.m, words) + '</span>' : "") + "</a></li>";
    }).join("") : '<li class="empty">No topics match "' + esc(input.value) + '". Try a broader term.</li>';
  }
  function move(d) {
    var items = $$("li[role=option]", list);
    if (!items.length) return;
    items[sel].setAttribute("aria-selected", "false");
    sel = (sel + d + items.length) % items.length;
    items[sel].setAttribute("aria-selected", "true");
    items[sel].scrollIntoView({ block: "nearest" });
  }
  function openSearch() {
    modal.hidden = false; input.value = ""; input.focus();
    if (index) return runSearch();
    list.innerHTML = '<li class="empty">Loading index…</li>';
    var sc = document.createElement("script");
    sc.src = "assets/search-index.js";
    sc.onload = function () { index = window.SDH_INDEX || []; runSearch(); };
    sc.onerror = function () { list.innerHTML = '<li class="empty">Search index failed to load. Reload the page and try again.</li>'; };
    document.body.appendChild(sc);
  }
  function closeSearch() { modal.hidden = true; }
  $("#search-btn").addEventListener("click", openSearch);
  modal.addEventListener("click", function (e) { if (e.target === modal) closeSearch(); });
  input.addEventListener("input", runSearch);
  input.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter") { var a = $$("li[role=option] a", list)[sel]; if (a) location.href = a.href; }
  });
  addEventListener("keydown", function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); modal.hidden ? openSearch() : closeSearch(); }
    else if (e.key === "/" && modal.hidden && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); openSearch(); }
    else if (e.key === "Escape") { if (!modal.hidden) closeSearch(); else drawer(false); }
  });

  /* ---------- interactive figures: <figure data-steps> with buttons that toggle data-step ---------- */
  $$("figure[data-steps]").forEach(function (fig) {
    var btns = $$(".fig-controls button", fig);
    btns.forEach(function (b) {
      b.addEventListener("click", function () {
        fig.dataset.step = b.dataset.step;
        btns.forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      });
    });
  });
})();
