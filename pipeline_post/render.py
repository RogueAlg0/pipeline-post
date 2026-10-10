"""Server-side HTML renderer. Produces the same vintage racing page as the
demo, with all commentary generated up front (no JavaScript needed)."""

import html

from .commentary import (
    DEFAULT_SEED,
    SeededRng,
    form_for,
    fmt_time,
    headline,
    horse_name,
    inquiry,
    race_call,
    track_line,
)

CSS = """\
  :root {
    --paper: #f7f1e3;
    --ink: #2a2419;
    --faint: #8a7d63;
    --rule: #2a2419;
    --accent: #1d5c38;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: #e8dfc9;
    color: var(--ink);
    font-family: Georgia, 'Times New Roman', serif;
    padding: 1rem;
  }
  .page {
    max-width: 720px;
    margin: 0 auto;
    background: var(--paper);
    padding: 1.5rem 1.5rem 2.5rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
  }
  .kicker {
    text-align: center;
    font-variant: small-caps;
    letter-spacing: 0.35em;
    font-size: 0.8rem;
    color: var(--faint);
  }
  h1.masthead {
    text-align: center;
    font-size: 2.6rem;
    margin: 0.2rem 0 0;
    letter-spacing: 0.02em;
  }
  .masthead .post { color: var(--accent); }
  .dateline {
    display: flex;
    justify-content: space-between;
    border-top: 3px double var(--rule);
    border-bottom: 1px solid var(--rule);
    padding: 0.4rem 0;
    margin: 0.8rem 0 1.2rem;
    font-variant: small-caps;
    letter-spacing: 0.12em;
    font-size: 0.85rem;
    color: var(--faint);
  }
  .track {
    text-align: center;
    font-style: italic;
    color: var(--faint);
    margin-bottom: 1.2rem;
  }
  h2.headline {
    font-size: 1.7rem;
    line-height: 1.2;
    margin: 0 0 0.3rem;
  }
  .byline {
    font-variant: small-caps;
    letter-spacing: 0.1em;
    color: var(--faint);
    font-size: 0.85rem;
    margin-bottom: 0.8rem;
  }
  .race-call {
    font-size: 1.02rem;
    line-height: 1.65;
    text-align: justify;
    hyphens: auto;
    text-wrap: pretty;
    margin: 0 0 1rem;
  }
  .race-call::first-letter {
    font-size: 3.2em;
    float: left;
    line-height: 0.85;
    padding-right: 0.08em;
    font-weight: bold;
  }
  h3.card-title {
    text-align: center;
    font-variant: small-caps;
    letter-spacing: 0.25em;
    border-top: 3px double var(--rule);
    border-bottom: 1px solid var(--rule);
    padding: 0.5rem 0;
    margin: 1.6rem 0 0.8rem;
  }
  table.card {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
  }
  table.card th {
    font-variant: small-caps;
    letter-spacing: 0.08em;
    text-align: left;
    border-bottom: 2px solid var(--rule);
    padding: 0.35rem 0.4rem;
    font-size: 0.8rem;
    color: var(--faint);
  }
  table.card td {
    border-bottom: 1px dotted #b9ac8d;
    padding: 0.45rem 0.4rem;
    vertical-align: top;
  }
  .horse { font-weight: bold; }
  .form { font-family: 'Courier New', monospace; letter-spacing: 0.1em; white-space: nowrap; }
  .won { color: var(--accent); font-weight: bold; }
  .lost { color: #a33b2e; font-weight: bold; }
  .note { font-style: italic; color: var(--faint); font-size: 0.85rem; }
  .stewards {
    border: 2px solid var(--rule);
    padding: 0.9rem 1rem;
    margin-top: 1.6rem;
    background: #f3ead2;
  }
  .stewards h4 {
    margin: 0 0 0.4rem;
    font-variant: small-caps;
    letter-spacing: 0.2em;
    text-align: center;
  }
  .stewards p { margin: 0.4rem 0; font-size: 0.93rem; line-height: 1.55; }
  .footer {
    margin-top: 1.8rem;
    padding-top: 0.6rem;
    border-top: 3px double var(--rule);
    text-align: center;
    font-variant: small-caps;
    letter-spacing: 0.15em;
    font-size: 0.78rem;
    color: var(--faint);
  }
  .table-wrap { overflow-x: auto; }
  /* Mobile: the race card becomes a stack of runner cards. The page
     itself never scrolls sideways. */
  @media (max-width: 600px) {
    table.card thead {
      position: absolute;
      left: -9999px;
      top: auto;
      width: 1px;
      height: 1px;
      overflow: hidden;
    }
    table.card, table.card tbody, table.card tr, table.card td {
      display: block;
      width: 100%;
    }
    table.card tr {
      border: 2px solid var(--rule);
      margin: 0 0 0.9rem;
      padding: 0.6rem 0.8rem;
    }
    table.card td {
      border-bottom: none;
      padding: 0.18rem 0;
    }
    table.card td[data-label]::before {
      content: attr(data-label);
      display: block;
      font-variant: small-caps;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
      color: var(--faint);
    }
    table.card td.cell-horse { font-size: 1.2rem; }
    table.card td.cell-horse::before { display: none; }
    table.card .note { overflow-wrap: anywhere; }
  }
  /* Desktop: let the wider canvas breathe. */
  @media (min-width: 900px) {
    .page { max-width: 800px; padding: 2rem 2.5rem 3rem; }
    h1.masthead { font-size: 3.2rem; }
  }
"""


def _card_rows(builds):
    rows = []
    for b in builds:
        ok = b["status"] == "SUCCESS"
        rows.append(
            "<tr><td data-label=\"Gate\">%s</td>"
            "<td class=\"horse cell-horse\">%s<div class=\"note\">%s</div></td>"
            "<td data-label=\"Rider\">%s</td>"
            "<td class=\"form\" data-label=\"Form\">%s</td>"
            "<td data-label=\"Time\">%s</td>"
            "<td data-label=\"Result\" class=\"%s\">%s</td></tr>"
            % (html.escape(str(b["n"])),
               html.escape(horse_name(b["branch"])),
               html.escape(b["branch"]),
               html.escape(b["author"]),
               html.escape(form_for(b["branch"], builds)),
               html.escape(fmt_time(b["secs"])),
               "won" if ok else "lost",
               "WON" if ok else "FELL")
        )
    return "\n".join(rows)


def render_page(builds, edition="Demo edition", demo=True, seed=DEFAULT_SEED):
    """Render the full page for builds (newest first)."""
    rng = SeededRng(seed)
    # Same order as the demo: race calls first, inquiries after.
    calls = "\n".join(
        "<p class=\"race-call\">%s</p>" % html.escape(race_call(b, rng))
        for b in builds[:4]
    )
    fallen = [b for b in builds if b["status"] != "SUCCESS"]
    if fallen:
        inquiries = "\n".join(
            "<p>%s</p>" % html.escape(inquiry(b, rng)) for b in fallen
        )
    else:
        inquiries = ("<p>A clean meeting. The stewards were reduced to "
                     "watching the grass grow.</p>")
    footer = ("Demo mode: fixtures only, no pipelines were harmed"
              if demo else "Printed from live pipeline data")
    return """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Pipeline Post</title>
<style>
%s</style>
</head>
<body>
<div class="page">
  <div class="kicker">All the builds that is fit to print</div>
  <h1 class="masthead">The Pipeline <span class="post">Post</span></h1>
  <div class="dateline"><span>%s</span><span>Bitbucket Pipelines turf</span></div>
  <div class="track">%s</div>
  <h2 class="headline">%s</h2>
  <div class="byline">By our track correspondent</div>
  %s
  <h3 class="card-title">Official Race Card</h3>
  <div class="table-wrap">
  <table class="card">
    <thead><tr><th>#</th><th>Runner</th><th>Rider</th><th>Form</th><th>Time</th><th>Result</th></tr></thead>
    <tbody>%s</tbody>
  </table>
  </div>
  <div class="stewards">
    <h4>Stewards' Inquiries</h4>
    %s
  </div>
  <div class="footer">%s</div>
</div>
</body>
</html>
""" % (CSS, html.escape(edition), html.escape(track_line(builds)),
       html.escape(headline(builds)), calls, _card_rows(builds),
       inquiries, footer)
