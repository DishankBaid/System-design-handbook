# Writing a chapter

Each chapter is one file, `content/<slug>.html`, containing only the article body.
`build.py` wraps it with the title, summary, sidebar, table of contents, "Mark as done" button and prev/next links.
The slug, title and one-line summary already live in `PARTS` in `build.py`; do not repeat the title or summary in the file.

Two finished chapters set the standard.
Read both completely before writing:

- `content/consistent-hashing.html` - concept chapter
- `content/url-shortener.html` - case study

Build and view with `python3 build.py`, then open `site/<slug>.html`.

## Writing rules

- Never use the em dash or en dash characters. Use a plain hyphen "-", a comma, a colon or a new sentence.
- Short, direct sentences. Plain words. No filler ("it is worth noting", "in today's world", "let's dive in").
- Explain each idea once. Depth comes from new angles: mechanism, failure modes, concrete numbers, real systems, trade-offs. Never restate a point in different words.
- Use concrete examples with real-looking values (keys, URLs, timestamps, request rates), not "foo" and "bar".
- Every number you state must be correct. If you can compute or measure it with a script, do so.
- Name things the way practitioners do, and define every term the first time it appears with `<dfn>term</dfn>`.
- Cross-link other chapters by slug, e.g. `<a href="replication.html">Replication</a>`. Only link slugs that exist in `PARTS`.
- References: 3 to 5 canonical sources you are certain exist (original papers, official documentation, well-known engineering blog posts). Prefer fewer links to guessed ones.

## Concept chapter anatomy

1. `<h2 id="why">Why it matters</h2>` with a `<p class="lead">` opening: the problem this concept solves, made concrete.
2. Mechanism sections (`h2` with `h3` subsections). This is the core of the chapter: how it actually works, step by step.
3. At least three SVG diagrams. At least one should be interactive (step-through) or animated when that helps understanding.
4. A worked example with concrete numbers, often as a table.
5. A Python snippet when there is an algorithm to show. It must run with `python3 -I` using only the standard library, and any output claimed in a comment must match a real run.
6. A trade-off table and/or comparison of alternatives.
7. "In the real world": how named systems (PostgreSQL, Kafka, DynamoDB, Cassandra, Redis, Envoy, Netflix, Uber, Discord, etc.) do it.
8. The interview box (see components), then `<h2 id="references">References</h2>`.

## Case study anatomy

Follow `url-shortener.html` exactly: numbered `h2` sections for requirements, estimation (`.stats` + `.calc`), API, data model, high-level design (architecture diagram, ideally with an animated `.flow` hot path), two or three deep dives each with a diagram, a bottlenecks table, key trade-offs, interview box, references.

## Length

Roughly 2,500 to 4,500 words per chapter, like the exemplars.

## HTML components

Every `h2` and `h3` needs a unique, short, kebab-case `id`; the table of contents is built from them.

```html
<p class="lead">Larger intro paragraph.</p>
<dfn>defined term</dfn>   <strong>emphasis</strong>   <code>inline_code</code>

<div class="callout note"><div class="callout-title">Title</div><p>...</p></div>
<div class="callout warn"><div class="callout-title">Common mistake</div><p>...</p></div>

<div class="table-wrap"><table>
<thead><tr><th>...</th></tr></thead>
<tbody><tr><th>row label</th><td class="yes">good</td><td class="no">bad</td><td class="meh">so-so</td><td class="num">42</td></tr></tbody>
</table></div>

<div class="defs"><div><h4>Term</h4><p>Short card text.</p></div>...</div>
<ol class="steps"><li><strong>Step.</strong> ...</li></ol>
<div class="stats"><div><b>~116k/s</b><span>label</span></div>...</div>
<div class="calc">Monospace worked arithmetic, <span class="r">highlighted result</span></div>

<pre><code class="language-python">...python, with &lt; &gt; &amp; escaped...</code></pre>
<pre><code class="language-sql">...</code></pre>   (any language name works; only python is colour-highlighted)

<div class="callout interview">
<div class="callout-title">Interview angle</div>
<h4>When to bring it up</h4><p>...</p>
<h4>Follow-ups to expect</h4><ul><li>...</li></ul>
<h4>Red flags</h4><ul><li>...</li></ul>
</div>

<ul class="refs">
<li><a href="https://..." target="_blank" rel="noopener">Title</a><span>Authors, venue, year. Why it is worth reading.</span></li>
</ul>
```

## Diagrams

Diagrams are inline SVG inside a figure.
Never hard-code colours: use the classes below, or `style="fill:var(--d-db)"` style CSS variables, so both light and dark themes work.

```html
<figure class="fig">            <!-- add class "wide" for wide architecture diagrams -->
<div class="fig-frame">
<svg viewBox="0 0 720 300" role="img" aria-label="Plain description of the diagram">
  ...
</svg>
</div>
<figcaption><b>Short title.</b> One or two sentences on what to notice.</figcaption>
</figure>
```

Shapes (`rect`, `circle`) take `class="n"` plus a role:
`client`, `svc` (services, indigo), `db` (stores, green), `cache` (amber), `queue` (queues/logs, pink), `ext` (external/infra, slate), `ghost` (dashed outline), `good` (green), `bad` (red).
Zones/regions: `class="zone"`.

Text: `class="t"` plus modifiers: `b` bold, `sm` 11.5px, `xs` 10.5px, `mono`, `mute` grey, `accent`, `red`, `green`, `mid` centred, `end` right-aligned.
Default text is 13px. Put labels so they never overlap lines or other labels; leave margins inside the viewBox.

Edges: `<path class="e" d="...">` draws a line with an arrowhead (shared marker `#arr`).
Modifiers: `dash`, `accent`, `red`, `green`, `both` (arrowheads at both ends), `plain` (no arrowhead).
Plain lines: `class="line"` or `class="line faint"`. Dots: `class="dot"` (+ `accent`, `svc`, `db`, `cache`, `queue`).
Node colour variables for custom fills/strokes: `--d-svc`, `--d-svc-s`, `--d-db`, `--d-db-s`, `--d-cache`, `--d-cache-s`, `--d-queue`, `--d-queue-s`, `--d-ext`, `--d-ext-s`, `--d-red`, `--d-green`, `--accent`, `--surface`, `--d-text`, `--d-muted`.

Animation: overlay `<path class="flow" d="..."/>` on top of an edge to show moving traffic. Use sparingly (hot paths). Reduced-motion users get a static line automatically.

Step-through (interactive) figures:

```html
<figure class="fig" data-steps data-step="1">
<div class="fig-frame">
<svg ...>
  <g>always visible</g>
  <g data-show="1">only in step 1</g>
  <g data-show="2 3">in steps 2 and 3</g>
</svg>
<div class="fig-controls">
  <button type="button" data-step="1" aria-pressed="true">Normal</button>
  <button type="button" data-step="2" aria-pressed="false">Leader fails</button>
</div>
</div>
<figcaption>...</figcaption>
</figure>
```

Up to 6 steps are supported.

Layout tips:
- Typical viewBox widths are 680 to 760. Compute coordinates carefully; for rings, grids or charts, generate the SVG with a small Python script so geometry is exact.
- Boxes ~90-140 wide and 40-60 tall; leave at least 25px between boxes for arrows.
- Curved connectors: `M x1,y1 C cx1,cy1 cx2,cy2 x2,y2`. End arrows ~4px short of the target box edge.
- Charts must be drawn to scale, with labels showing values the chart actually reaches.
