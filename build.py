#!/usr/bin/env python3
"""Build the static site: wrap content/<slug>.html fragments in the shared template.

Usage: python3 build.py            -> writes site/
Stdlib only. Content fragments are plain HTML bodies; see CONTRIBUTING.md for the conventions.
"""
import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "site"

# (part title, short blurb, [(slug, title, one-line summary)])
PARTS = [
    ("Foundations", "The vocabulary and mental models every other page builds on.", [
        ("approach", "Approaching a Design Interview", "A repeatable framework for the 45 minutes: scope, estimate, sketch, deepen, wrap up."),
        ("estimation", "Back-of-Envelope Estimation", "Turn vague scale into concrete QPS, storage and bandwidth numbers in two minutes."),
        ("scalability", "Scalability", "Vertical vs horizontal scaling, statelessness, and where systems actually stop scaling."),
        ("latency-availability", "Latency, Throughput & Availability", "Percentiles, the nines, SLIs/SLOs/SLAs, and how availability composes."),
        ("cap-pacelc", "CAP & PACELC", "What you really give up during a partition, and what you trade the rest of the time."),
        ("consistency-models", "Consistency Models", "From linearizable to eventual: what each guarantee lets a client observe."),
    ]),
    ("Networking & Edge", "How requests find your servers and get spread across them.", [
        ("dns", "DNS", "Resolution path, record types, TTLs, and DNS as a load balancing and failover tool."),
        ("network-protocols", "TCP, UDP & HTTP", "Handshakes, head-of-line blocking, and what HTTP/2 and HTTP/3 fix."),
        ("load-balancing", "Load Balancing", "L4 vs L7, balancing algorithms, health checks, and avoiding the LB as a single point of failure."),
        ("proxies-gateways", "Proxies & API Gateways", "Forward vs reverse proxies, and the cross-cutting work a gateway takes off your services."),
        ("cdn", "Content Delivery Networks", "Edge caching, push vs pull, cache keys, and invalidation."),
        ("realtime", "Polling, SSE & WebSockets", "Choosing a transport for pushing updates from server to client."),
    ]),
    ("Data", "Storing, finding and moving data at scale.", [
        ("sql-vs-nosql", "SQL vs NoSQL", "Relational, key-value, document, wide-column and graph stores, and how to pick."),
        ("transactions", "ACID & Isolation Levels", "What each isolation level prevents, and the anomalies that slip through."),
        ("indexing", "Indexing: B-Trees & LSM Trees", "How databases find rows fast, and the read/write trade-off between the two engine families."),
        ("replication", "Replication", "Single-leader, multi-leader and leaderless replication, lag, and quorums."),
        ("sharding", "Sharding & Partitioning", "Splitting data across machines: keys, strategies, hotspots and resharding."),
        ("consistent-hashing", "Consistent Hashing", "Spread keys across a changing set of nodes while moving as little data as possible."),
        ("caching", "Caching", "Where to cache, read/write patterns, eviction, invalidation and stampedes."),
        ("blob-storage", "Blob & Object Storage", "Storing large files: object stores, chunking, presigned URLs and durability."),
        ("search", "Search & Inverted Indexes", "How full-text search works, from tokenizing to ranking to sharding the index."),
        ("data-modeling", "Data Modeling", "Modeling for access patterns: normalization, denormalization and choosing keys."),
    ]),
    ("Async & Streaming", "Decoupling work in time with queues, logs and events.", [
        ("message-queues", "Message Queues", "Buffering work between producers and consumers: acks, retries, dead letters, ordering."),
        ("event-streaming", "Pub/Sub & Event Streaming", "Kafka-style logs: partitions, consumer groups, offsets and retention."),
        ("event-driven", "Event-Driven Architecture", "Events vs commands, choreography vs orchestration, and the costs of going async."),
        ("cqrs-event-sourcing", "CQRS & Event Sourcing", "Separate read and write models, and storing state as a log of facts."),
        ("batch-stream", "Batch vs Stream Processing", "MapReduce to Flink: windows, watermarks and the lambda/kappa debate."),
    ]),
    ("Architecture & APIs", "Shaping services and the contracts between them.", [
        ("microservices", "Monolith vs Microservices", "When to split, how to draw boundaries, and what distribution costs you."),
        ("api-design", "API Design", "REST, gRPC and GraphQL, plus pagination, versioning and error contracts."),
        ("rate-limiting", "Rate Limiting", "Token bucket, leaky bucket and window algorithms, and enforcing them across many servers."),
        ("service-discovery", "Service Discovery", "How services find each other: registries, client vs server-side discovery, and service meshes."),
        ("distributed-transactions", "Distributed Transactions", "Two-phase commit, sagas, and the transactional outbox."),
        ("idempotency", "Idempotency & Delivery Semantics", "At-most, at-least and effectively-once delivery, and idempotency keys."),
    ]),
    ("Reliability & Operations", "Keeping distributed systems correct, observable and safe.", [
        ("consensus", "Consensus & Leader Election", "How Raft gets a cluster to agree, and where you need consensus at all."),
        ("id-generation", "Distributed ID Generation", "UUIDs, ticket servers, Snowflake and ULIDs: uniqueness, ordering and size."),
        ("fault-tolerance", "Timeouts, Retries & Circuit Breakers", "Failure handling that contains problems instead of amplifying them."),
        ("observability", "Observability", "Logs, metrics and traces, and alerting on what users feel."),
        ("security", "Security Fundamentals", "Authentication, authorization, OAuth 2.0, JWTs, TLS and secrets."),
        ("probabilistic", "Probabilistic Data Structures", "Bloom filters, HyperLogLog and Count-Min Sketch: big answers in tiny memory."),
    ]),
    ("Case Studies", "Full interview walkthroughs that combine the concepts above.", [
        ("url-shortener", "Design a URL Shortener", "Key generation, redirects at scale, and analytics without slowing the hot path."),
        ("rate-limiter-design", "Design a Rate Limiter", "A distributed limiter service that adds under a millisecond to every request."),
        ("chat-system", "Design a Chat System", "1:1 and group messaging with delivery receipts, presence and offline sync."),
        ("news-feed", "Design a News Feed", "Fan-out on write vs read, ranking, and the celebrity problem."),
        ("video-streaming", "Design a Video Platform", "Upload, transcoding pipelines, adaptive bitrate streaming and CDN delivery."),
        ("ride-sharing", "Design a Ride-Sharing Service", "Live location ingestion, geospatial matching and trip state."),
        ("web-crawler", "Design a Web Crawler", "Frontier management, politeness, deduplication and crawling billions of pages."),
        ("notification-system", "Design a Notification System", "Multi-channel delivery with preferences, retries and rate limits."),
        ("key-value-store", "Design a Key-Value Store", "A Dynamo-style store: partitioning, replication, versioning and repair."),
        ("autocomplete", "Design Search Autocomplete", "Top-k suggestions per prefix in tens of milliseconds."),
    ]),
]

PAGES = [(pi, slug, title, summary) for pi, (_, _, items) in enumerate(PARTS) for slug, title, summary in items]

META = json.dumps({"parts": [[s for s, _, _ in items] for _, _, items in PARTS]}, separators=(",", ":"))

FONTS = ("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700"
         "&family=JetBrains+Mono:wght@400;500&display=swap")

# Shared SVG defs: arrowheads usable from every inline diagram on the page via url(#arr) etc.
SVG_DEFS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="var(--d-stroke)"/></marker>
<marker id="arr-accent" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="var(--accent)"/></marker>
<marker id="arr-red" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="var(--d-red)"/></marker>
<marker id="arr-green" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="var(--d-green)"/></marker>
</defs></svg>"""

THEME_BOOT = ("<script>try{var t=localStorage.getItem('sdh-theme');"
              "if(t)document.documentElement.dataset.theme=t}catch(e){}</script>")

ICON_SEARCH = '<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><circle cx="9" cy="9" r="6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M13.5 13.5L18 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
ICON_THEME = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><circle cx="10" cy="10" r="7" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M10 3a7 7 0 0 1 0 14z" fill="currentColor"/></svg>'
ICON_MENU = '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true"><path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'


# ---------- Python syntax highlighting (build time, no runtime dependency) ----------
PY_KEYWORDS = ("False None True and as assert async await break class continue def del elif else except "
               "finally for from global if import in is lambda nonlocal not or pass raise return try while with yield").split()
PY_BUILTINS = "print len range dict list set tuple int str float bool min max sum sorted enumerate zip map any all isinstance self hash bytes abs".split()
PY_TOKEN = re.compile(
    r"(?P<com>#[^\n]*)"
    r"|(?P<str>[rbf]?(\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|\"[^\"\n]*\"|'[^'\n]*'))"
    r"|(?P<ent>&[a-z]+;|&#\d+;)"
    r"|(?P<num>\b\d[\d_]*(\.\d+)?\b)"
    r"|(?P<word>\b[A-Za-z_][A-Za-z0-9_]*\b)"
)


def highlight_python(src: str) -> str:
    out, pos, prev_word = [], 0, ""
    for m in PY_TOKEN.finditer(src):
        out.append(src[pos:m.start()])
        tok, kind = m.group(0), m.lastgroup
        if kind == "word":
            if tok in PY_KEYWORDS:
                kind = "kw"
            elif prev_word in ("def", "class"):
                kind = "fn"
            elif tok in PY_BUILTINS:
                kind = "bi"
            else:
                kind = None
            prev_word = tok
        if kind in (None, "ent"):
            out.append(tok)
        else:
            out.append(f'<span class="tk-{kind}">{tok}</span>')
        pos = m.end()
    out.append(src[pos:])
    return "".join(out)


def highlight(body: str) -> str:
    """Wrap every <pre><code class="language-x"> in a titled block with a copy button; colour Python."""
    def wrap(m):
        lang, src = m.group(1), m.group(2)
        code = highlight_python(src) if lang == "python" else src
        return (f'<div class="code"><div class="code-head"><span>{lang}</span>'
                f'<button class="copy-btn" type="button">Copy</button></div>'
                f'<pre><code class="language-{lang}">{code}</code></pre></div>')
    return re.sub(r'<pre><code class="language-(\w+)">([\s\S]*?)</code></pre>', wrap, body)


# ---------- helpers ----------
def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def sidebar(current: str) -> str:
    parts = []
    for pi, (ptitle, _, items) in enumerate(PARTS):
        open_attr = " open" if any(s == current for s, _, _ in items) or current == "index" else ""
        links = "".join(
            f'<li><a href="{s}.html" data-slug="{s}"{" aria-current=\"page\"" if s == current else ""}>'
            f'<span class="nav-check" aria-hidden="true"></span><span>{html.escape(t)}</span></a></li>'
            for s, t, _ in items
        )
        parts.append(
            f'<details class="nav-part"{open_attr}><summary><span class="nav-num">{pi + 1}</span>'
            f'{html.escape(ptitle)}<span class="nav-count" data-part="{pi}"></span></summary><ul>{links}</ul></details>'
        )
    return "".join(parts)


def shell(title: str, desc: str, current: str, main: str, toc: bool) -> str:
    toc_html = ('<aside class="toc" aria-label="On this page"><div class="toc-title">On this page</div>'
                '<nav id="toc"></nav></aside>') if toc else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/style.css">
{THEME_BOOT}
</head>
<body data-slug="{current}">
{SVG_DEFS}
<header class="topbar">
  <button class="icon-btn menu-btn" id="menu-btn" aria-label="Open navigation" aria-controls="sidebar" aria-expanded="false">{ICON_MENU}</button>
  <a class="brand" href="index.html"><span class="brand-mark" aria-hidden="true"></span>System Design Handbook</a>
  <button class="search-btn" id="search-btn" aria-label="Search topics">{ICON_SEARCH}<span>Search topics</span><kbd>⌘K</kbd></button>
  <button class="icon-btn" id="theme-btn" aria-label="Toggle dark mode">{ICON_THEME}</button>
</header>
<div class="layout{' has-toc' if toc else ''}">
  <nav class="sidebar" id="sidebar" aria-label="Topics">{sidebar(current)}</nav>
  <div class="scrim" id="scrim" hidden></div>
  <main class="main" id="main">{main}</main>
  {toc_html}
</div>
<div class="search-modal" id="search-modal" hidden role="dialog" aria-modal="true" aria-label="Search">
  <div class="search-panel">
    <div class="search-input-row">{ICON_SEARCH}<input id="search-input" type="search" placeholder="Search concepts, e.g. quorum, saga, CDN" autocomplete="off" aria-label="Search"><kbd>Esc</kbd></div>
    <ul class="search-results" id="search-results" role="listbox"></ul>
  </div>
</div>
<script>window.SDH_META={META};</script>
<script src="assets/app.js"></script>
</body>
</html>
"""


def topic_page(idx: int, body: str) -> str:
    pi, slug, title, summary = PAGES[idx]
    ptitle = PARTS[pi][0]
    prev_ = PAGES[idx - 1] if idx > 0 else None
    next_ = PAGES[idx + 1] if idx + 1 < len(PAGES) else None
    pn = '<nav class="pager" aria-label="Previous and next">'
    pn += (f'<a class="pager-prev" href="{prev_[1]}.html"><span>Previous</span>{html.escape(prev_[2])}</a>'
           if prev_ else "<span></span>")
    pn += (f'<a class="pager-next" href="{next_[1]}.html"><span>Next</span>{html.escape(next_[2])}</a>'
           if next_ else "<span></span>")
    pn += "</nav>"
    main = f"""<article class="article">
<div class="eyebrow">Part {pi + 1} · {html.escape(ptitle)}</div>
<h1>{html.escape(title)}</h1>
<p class="summary">{html.escape(summary)}</p>
<div class="article-body">{highlight(body)}</div>
<div class="done-row"><button class="done-btn" id="done-btn" aria-pressed="false"><span class="done-box" aria-hidden="true"></span><span class="done-label">Mark as done</span></button></div>
{pn}
</article>"""
    return shell(f"{title} · System Design Handbook", summary, slug, main, toc=True)


def stub_body(title: str) -> str:
    return (f'<div class="callout note"><div class="callout-title">In progress</div>'
            f'<p>The full chapter on {html.escape(title)} is being written.</p></div>')


def home_page() -> str:
    cards = []
    for pi, (ptitle, blurb, items) in enumerate(PARTS):
        lis = "".join(f'<li><a href="{s}.html" data-slug="{s}"><span class="nav-check" aria-hidden="true"></span>{html.escape(t)}</a></li>'
                      for s, t, _ in items)
        cards.append(f"""<section class="part-card">
  <div class="part-head"><span class="part-num">Part {pi + 1}</span><span class="part-progress" data-part="{pi}">0 / {len(items)}</span></div>
  <h2>{html.escape(ptitle)}</h2>
  <p>{html.escape(blurb)}</p>
  <div class="bar"><span data-bar="{pi}"></span></div>
  <ul>{lis}</ul>
</section>""")
    n_concepts = sum(len(items) for _, _, items in PARTS[:-1])
    n_cases = len(PARTS[-1][2])
    main = f"""<div class="home">
<section class="hero">
  <div class="eyebrow">Interview-focused · {n_concepts} concepts · {n_cases} case studies</div>
  <h1>Learn how large systems are built, one mechanism at a time.</h1>
  <p class="lede">Each chapter explains how something actually works, draws it, works through an example, weighs the trade-offs, and ends with how interviewers probe it. Case studies then put the pieces together the way you would at a whiteboard.</p>
  <div class="hero-actions"><a class="btn primary" href="approach.html">Start with the interview framework</a><a class="btn" href="url-shortener.html">Jump to a case study</a></div>
  <div class="overall"><div class="overall-label"><span>Your progress</span><span id="overall-count">0 / {len(PAGES)}</span></div><div class="bar"><span id="overall-bar"></span></div></div>
</section>
<section class="howto">
  <div><h3>Read in order</h3><p>Parts build on each other. Foundations gives the vocabulary that later chapters assume.</p></div>
  <div><h3>Every chapter, same shape</h3><p>Mechanism, diagrams, a worked example, a trade-off table, and an interview angle box.</p></div>
  <div><h3>Practice with cases</h3><p>Each case study follows the interview flow: requirements, estimates, API, data, design, deep dives.</p></div>
</section>
<div class="parts-grid">{''.join(cards)}</div>
</div>"""
    return shell("System Design Handbook", "Interview-focused system design: concepts, diagrams and case studies.",
                 "index", main, toc=False)


def search_entry(slug, title, summary, part, body):
    heads = [strip_tags(h) for h in re.findall(r"<h[23][^>]*>([\s\S]*?)</h[23]>", body)]
    terms = sorted({strip_tags(t) for t in re.findall(r"<(?:strong|dfn)>([\s\S]*?)</(?:strong|dfn)>", body)})
    text = strip_tags(re.sub(r"<(svg|pre)[\s\S]*?</\1>", " ", body)).lower()
    words = sorted({w for w in re.findall(r"[a-z0-9][a-z0-9-]{2,}", text)})
    return {"s": slug, "t": title, "d": summary, "p": part, "h": heads, "k": terms[:60], "x": " ".join(words)}


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, OUT / "assets" / f.name)

    index, missing = [], []
    for i, (pi, slug, title, summary) in enumerate(PAGES):
        src = CONTENT / f"{slug}.html"
        if src.exists():
            body = src.read_text()
        else:
            body = stub_body(title)
            missing.append(slug)
        (OUT / f"{slug}.html").write_text(topic_page(i, body))
        index.append(search_entry(slug, title, summary, PARTS[pi][0], body))

    home = home_page()
    (OUT / "index.html").write_text(home)
    # claude.ai artifacts wrap the entry page in their own document skeleton, so ship a body-only copy
    head = re.search(r"<head>([\s\S]*?)</head>", home).group(1)
    head = re.sub(r'<meta (charset|name="viewport")[^>]*>\n', "", head)
    body = re.search(r"<body[^>]*>([\s\S]*?)</body>", home).group(1)
    (OUT / "artifact-entry.html").write_text(head + '<script>document.body.dataset.slug="index"</script>' + body)
    (OUT / "assets" / "search-index.js").write_text(
        "window.SDH_INDEX=" + json.dumps(index, separators=(",", ":")) + ";\n")

    print(f"built {len(PAGES) + 1} pages into {OUT}/ ({len(PAGES) - len(missing)} written, {len(missing)} stubs)")


if __name__ == "__main__":
    build()
