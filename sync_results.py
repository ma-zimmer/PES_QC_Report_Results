"""
Copies selected EnergyScope-Quebec pathway scenario result folders into this
site repo and rebuilds the landing index.html, ready to commit and push.

Usage:
    1. Generate a new scenario with run_main.py (creates
       projects/pathway/out/<name>/ in the EnergyScope-Quebec repo).
    2. Add its folder name to SCENARIOS below.
    3. Run: python sync_results.py
    4. git add -A && git commit -m "Add <name> results" && git push
"""
import json
import os
import re
import shutil

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_OUT_DIR = os.path.join(SITE_DIR, '..', 'EnergyScope-Quebec', 'projects', 'pathway', 'out')

# Published scenarios. S0 was a preliminary run (not published). S8 (the full
# combination) predates S7 and does not include its public-mobility constraint.
SCENARIOS = [
    'S1_results',
    'S2_results',
    'S3_results',
    'S4_results',
    'S5_results',
    'S6_results',
    'S7_results',
    'S8_results',
]

# plot_results.py's dashboard embeds a "switch run" / "compare with" case list
# built from whatever sibling folders exist in the LOCAL out/ directory at
# generation time — every experimental run on the author's machine, not just
# the ones published here. Rewrite that embedded list to only the scenarios
# this site actually publishes, so the dropdown on the live site can't offer
# (or link to) a run that doesn't exist there.
_CASES_RE = re.compile(r'const CASES = \[.*?\];', re.DOTALL)


def _restrict_cases(dashboard_path, current_name):
    with open(dashboard_path, encoding='utf-8') as f:
        html = f.read()
    published_siblings = [s for s in SCENARIOS if s != current_name]
    new_html, n = _CASES_RE.subn(
        f'const CASES = {json.dumps(published_siblings)};', html, count=1)
    if n == 0:
        print(f'  WARN {current_name}: CASES array not found, dashboard left as-is')
        return
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(new_html)


def sync_scenario(name):
    src = os.path.join(SOURCE_OUT_DIR, name)
    dst = os.path.join(SITE_DIR, name)
    src_graphs = os.path.join(src, 'graphs')
    if not os.path.isdir(src_graphs):
        print(f'  SKIP {name}: no graphs/ folder found at {src_graphs}')
        return False
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src_graphs, os.path.join(dst, 'graphs'))
    for extra in ('0_Summary.html', 'plotly.min.js'):
        extra_src = os.path.join(src, extra)
        if os.path.exists(extra_src):
            shutil.copy2(extra_src, dst)
    dashboard = os.path.join(dst, 'graphs', 'index.html')
    if os.path.exists(dashboard):
        _restrict_cases(dashboard, name)
    print(f'  OK   {name}')
    return True


# ---------------------------------------------------------------------------
# Landing page — a single connected spine (git-graph style): S1 -> S2 build a
# shared baseline, a split marker fans out into five modifications tested in
# isolation (S3-S7), and a merge marker brings four of them (S3-S6) back
# together into S8 — S8 predates S7, so it does not include the public-mobility
# constraint. Content is bespoke (not templated from SCENARIOS) since the
# narrative structure — which scenario builds on which — is fixed.
# ---------------------------------------------------------------------------

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scenario Results — EnergyScope-Québec</title>
<style>
  @media (prefers-color-scheme: dark) {
    :root {
      --page: #0f171d; --surface: #16212a; --surface-2: #1c2932;
      --ink: #e8eef1; --ink-soft: #9fb0b8; --line: #2a3944;
      --accent: #6cc3e6; --accent-strong: #9adcf5; --accent-ink: #06222c;
      --rail: #33454f; --rail-done: #4f7d92; --rail-branch: #3a5c6c;
      --ghost-bg: #141d24; --ghost-line: #354652;
    }
  }
  :root {
    --page: #eef3f3; --surface: #ffffff; --surface-2: #f4f8f8;
    --ink: #101820; --ink-soft: #52646c; --line: #d7e0e1;
    --accent: #0e6e8c; --accent-strong: #0a4f66; --accent-ink: #ffffff;
    --rail: #c7d4d5; --rail-done: #0e6e8c; --rail-branch: #8fb9c7;
    --ghost-bg: #e7edee; --ghost-line: #b9c8ca;
  }
  :root[data-theme="dark"] {
    --page: #0f171d; --surface: #16212a; --surface-2: #1c2932;
    --ink: #e8eef1; --ink-soft: #9fb0b8; --line: #2a3944;
    --accent: #6cc3e6; --accent-strong: #9adcf5; --accent-ink: #06222c;
    --rail: #33454f; --rail-done: #4f7d92; --rail-branch: #3a5c6c;
    --ghost-bg: #141d24; --ghost-line: #354652;
  }
  :root[data-theme="light"] {
    --page: #eef3f3; --surface: #ffffff; --surface-2: #f4f8f8;
    --ink: #101820; --ink-soft: #52646c; --line: #d7e0e1;
    --accent: #0e6e8c; --accent-strong: #0a4f66; --accent-ink: #ffffff;
    --rail: #c7d4d5; --rail-done: #0e6e8c; --rail-branch: #8fb9c7;
    --ghost-bg: #e7edee; --ghost-line: #b9c8ca;
  }

  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; background: var(--page); color: var(--ink);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 16px; line-height: 1.5;
    cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='22' height='22' viewBox='0 0 24 24'%3E%3Cpath d='M13 2 3 14h7l-1 8 11-14h-7z' fill='%23ffd166' stroke='%23101820' stroke-width='1.3' stroke-linejoin='round'/%3E%3C/svg%3E") 2 2, auto;
  }
  .wrap { max-width: 760px; margin: 0 auto; padding: 4.5rem 1.5rem 6rem; }

  /* Deep-link targets: id="s1".."s8" on each scenario's outer container, so
     the report can link straight to e.g. #s3. scroll-margin-top keeps the
     card from landing flush against the viewport edge; the :target rule
     gives a brief highlight so it's obvious which card was linked to. */
  [id^="s"] { scroll-margin-top: 1.75rem; }
  [id^="s"]:target .card { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }
  @media (prefers-reduced-motion: no-preference) {
    [id^="s"]:target .card { animation: target-flash 2.2s ease-out; }
    @keyframes target-flash {
      0% { box-shadow: 0 0 0 4px var(--accent); }
      100% { box-shadow: 0 0 0 2px var(--accent); }
    }
  }

  header.hero { margin-bottom: 3rem; }
  .eyebrow {
    font-family: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace;
    font-size: 0.78rem; letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--accent); margin: 0 0 0.9rem;
  }
  h1 {
    font-family: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, Cambria, "Times New Roman", serif;
    font-size: clamp(1.9rem, 1.4rem + 1.8vw, 2.7rem);
    line-height: 1.15; font-weight: 600; margin: 0 0 1.1rem;
    text-wrap: balance; color: var(--ink);
  }
  .lede { max-width: 62ch; color: var(--ink-soft); font-size: 1.05rem; margin: 0 0 0.6rem; }
  .lede + .lede { margin-top: 0.9rem; }
  .lede b { color: var(--ink); font-weight: 600; }

  .node {
    z-index: 1; flex-shrink: 0; border-radius: 999px; background: var(--surface);
    display: flex; align-items: center; justify-content: center;
    font-family: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace;
    font-weight: 600; color: var(--accent-strong);
  }
  .card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; }
  .cardhead { display: flex; align-items: baseline; justify-content: space-between; gap: 0.7rem; flex-wrap: wrap; }
  .cardtitle { font-weight: 700; margin: 0; color: var(--ink); }
  .tag {
    font-family: ui-monospace, "SF Mono", "Cascadia Code", Consolas, monospace;
    font-size: 0.7rem; letter-spacing: 0.06em; color: var(--ink-soft);
  }
  .desc { color: var(--ink-soft); margin: 0; }
  .chips { display: flex; flex-wrap: wrap; gap: 0.35rem; }
  .chip {
    font-size: 0.7rem; padding: 0.2rem 0.55rem; border-radius: 999px;
    border: 1px solid var(--line); color: var(--ink-soft); background: var(--surface-2);
    white-space: nowrap;
  }
  .chip.base { border-color: var(--rail-done); color: var(--accent-strong); font-weight: 600; }
  .chip.new { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); font-weight: 600; }
  .actions { display: flex; flex-wrap: wrap; gap: 0.55rem; }
  .btn {
    display: inline-flex; align-items: center; gap: 0.4rem;
    font-weight: 600; text-decoration: none; border-radius: 7px; border: 1px solid transparent;
  }
  .btn.primary { background: var(--accent); color: var(--accent-ink); }
  .btn.primary:hover { background: var(--accent-strong); }
  .btn.ghost { border-color: var(--line); color: var(--ink); }
  .btn.ghost:hover { border-color: var(--accent); color: var(--accent-strong); }

  .trunkline { position: relative; display: grid; grid-template-columns: 2.6rem 1fr; column-gap: 1.1rem; }
  .trunkline .railcol { position: relative; display: flex; justify-content: center; }
  .trunkline .railcol::before {
    content: ""; position: absolute; top: 2.6rem; bottom: -1.6rem; width: 2px; background: var(--rail-done);
  }
  .trunkline .node { width: 2.6rem; height: 2.6rem; font-size: 0.82rem; }
  .trunkline .card { padding: 1.15rem 1.3rem 1.25rem; margin-bottom: 1.6rem; }
  .trunkline .cardtitle { font-size: 1.08rem; margin-bottom: 0.3rem; }
  .trunkline .desc { font-size: 0.92rem; max-width: 52ch; margin-bottom: 0.8rem; }
  .trunkline .chips { margin-bottom: 0.9rem; }
  .trunkline .btn { font-size: 0.87rem; padding: 0.48rem 0.8rem; }

  .marker { position: relative; display: grid; grid-template-columns: 2.6rem 1fr; column-gap: 1.1rem; margin-bottom: 0.4rem; }
  .marker .railcol { position: relative; display: flex; justify-content: center; }
  .marker .railcol::before { content: ""; position: absolute; top: 0; bottom: 0; width: 2px; background: var(--rail-done); }
  .marker .diamond {
    z-index: 1; width: 0.7rem; height: 0.7rem; background: var(--surface);
    border: 2px solid var(--rail-done); transform: rotate(45deg); margin-top: 1rem;
  }
  .marker .note { align-self: center; font-size: 0.86rem; color: var(--ink-soft); padding-top: 0.5rem; }
  .marker .note b { color: var(--ink); }

  .branchzone { display: grid; grid-template-columns: 2.6rem 1fr; column-gap: 1.1rem; }
  .branchzone .spinecol { position: relative; display: flex; justify-content: center; }
  .branchzone .spinecol::before {
    content: ""; position: absolute; top: 0; bottom: 0.9rem; width: 2px;
    background: repeating-linear-gradient(to bottom, var(--rail-branch) 0 5px, transparent 5px 10px);
  }
  .substep { position: relative; padding-bottom: 1.15rem; }
  .substep:last-child { padding-bottom: 0; }
  .substepgrid { display: grid; grid-template-columns: 2.6rem 1fr; column-gap: 1.1rem; }
  .tick { position: relative; height: 2.4rem; display: flex; align-items: center; justify-content: center; }
  .tick::before {
    content: ""; position: absolute; left: 50%; top: 50%; width: 1.1rem; height: 2px;
    background: var(--rail-branch); transform: translate(-1.6rem, -50%);
  }
  .subnode { width: 2.1rem; height: 2.1rem; font-size: 0.72rem; border: 2px solid var(--rail-branch); color: var(--accent-strong); position: relative; margin-left: 0.5rem; }
  .subcard { padding: 0.85rem 1rem 0.95rem; }
  .subcard .cardtitle { font-size: 0.96rem; margin-bottom: 0.2rem; }
  .subcard .desc { font-size: 0.85rem; margin-bottom: 0.6rem; }
  .subcard .chips { margin-bottom: 0.75rem; }
  .subcard .btn { font-size: 0.8rem; padding: 0.38rem 0.65rem; }

  .substep.ghost .subcard { background: var(--ghost-bg); border-style: dashed; border-color: var(--ghost-line); }
  .substep.ghost .subnode { border-style: dashed; border-color: var(--ghost-line); color: var(--ink-soft); }
  .substep.ghost .tick::before { background: repeating-linear-gradient(to right, var(--ghost-line) 0 3px, transparent 3px 6px); }
  .substep.ghost .cardtitle, .substep.ghost .desc { color: var(--ink-soft); }
  .pending {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.03em; color: var(--ink-soft);
    border: 1px dashed var(--ghost-line); border-radius: 999px; padding: 0.2rem 0.5rem; white-space: nowrap;
  }
  .notmerged { font-size: 0.76rem; color: var(--ink-soft); font-style: italic; margin-top: 0.5rem; }

  .trunkline.endpoint .node { background: var(--accent); color: var(--accent-ink); border-color: var(--accent); }
  .trunkline.endpoint .card { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; margin-bottom: 0; }
  .chip.all { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); font-weight: 600; }

  footer {
    margin-top: 3.4rem; padding-top: 1.3rem; border-top: 1px solid var(--line);
    color: var(--ink-soft); font-size: 0.85rem; display: flex; justify-content: space-between;
    gap: 1rem; flex-wrap: wrap;
  }
  footer a { color: var(--ink-soft); }
  footer a:hover { color: var(--accent-strong); }

  @media (max-width: 480px) {
    .wrap { padding: 3rem 1.1rem 4rem; }
    .trunkline, .marker, .branchzone, .substepgrid { grid-template-columns: 2.1rem 1fr; column-gap: 0.7rem; }
    .trunkline .node { width: 2.1rem; height: 2.1rem; font-size: 0.72rem; }
    .trunkline .railcol::before { top: 2.1rem; }
  }
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <p class="eyebrow">EnergyScope-Québec &middot; Pathway model</p>
    <h1>Transition scenario results</h1>
    <p class="lede">This site accompanies the report and gives access to the interactive dashboard for each simulated scenario.</p>
    <p class="lede"><b>S1</b> and <b>S2</b> build a common baseline. From there, <b>S3&ndash;S7</b> each test <b>one</b> modification in isolation &mdash; not on top of one another &mdash; and <b>S8</b> combines the four that were tested.</p>
  </header>

  <div class="trunkline" id="s1">
    <div class="railcol"><div class="node">S1</div></div>
    <div class="card">
      <div class="cardhead"><h3 class="cardtitle">Base case</h3><span class="tag">S1_results</span></div>
      <p class="desc">Only the emissions constraints are active: a 2035 emissions cap and carbon neutrality by 2050.</p>
      <div class="chips">
        <span class="chip base">2035 emissions cap</span>
        <span class="chip base">2050 carbon neutrality</span>
      </div>
      <div class="actions">
        <a class="btn primary" href="S1_results/graphs/index.html">Explore the dashboard &rarr;</a>
        <a class="btn ghost" href="S1_results/0_Summary.html">Quick summary</a>
      </div>
    </div>
  </div>

  <div class="trunkline" id="s2">
    <div class="railcol"><div class="node">S2</div></div>
    <div class="card">
      <div class="cardhead"><h3 class="cardtitle">Initial stock spreading</h3><span class="tag">S2_results</span></div>
      <p class="desc">Adds a constraint that spreads the replacement of the initial technology stock over time.</p>
      <div class="chips">
        <span class="chip">&check; 2035 emissions cap</span>
        <span class="chip">&check; 2050 carbon neutrality</span>
        <span class="chip new">+ Initial stock spreading</span>
      </div>
      <div class="actions">
        <a class="btn primary" href="S2_results/graphs/index.html">Explore the dashboard &rarr;</a>
        <a class="btn ghost" href="S2_results/0_Summary.html">Quick summary</a>
      </div>
    </div>
  </div>

  <div class="marker">
    <div class="railcol"><div class="diamond"></div></div>
    <div class="note">Baseline locked in &mdash; <b>2035 emissions cap &middot; 2050 carbon neutrality &middot; initial stock spreading</b>. Each branch below tests one further modification on top of it, independently:</div>
  </div>

  <div class="branchzone">
    <div class="spinecol"></div>
    <div class="substeps">

      <div class="substep" id="s3">
        <div class="substepgrid">
          <div class="tick"><div class="node subnode">S3</div></div>
          <div class="card subcard">
            <div class="cardhead"><h3 class="cardtitle">Carbon budget</h3></div>
            <p class="desc">Adds a cumulative carbon budget over 2020&ndash;2050.</p>
            <div class="chips"><span class="chip new">+ Carbon budget</span></div>
            <div class="actions">
              <a class="btn primary" href="S3_results/graphs/index.html">Dashboard &rarr;</a>
              <a class="btn ghost" href="S3_results/0_Summary.html">Summary</a>
            </div>
          </div>
        </div>
      </div>

      <div class="substep" id="s4">
        <div class="substepgrid">
          <div class="tick"><div class="node subnode">S4</div></div>
          <div class="card subcard">
            <div class="cardhead"><h3 class="cardtitle">Limited change rate</h3></div>
            <p class="desc">Adds a constraint limiting how fast technologies can be deployed from one phase to the next.</p>
            <div class="chips"><span class="chip new">+ Limited change rate</span></div>
            <div class="actions">
              <a class="btn primary" href="S4_results/graphs/index.html">Dashboard &rarr;</a>
              <a class="btn ghost" href="S4_results/0_Summary.html">Summary</a>
            </div>
          </div>
        </div>
      </div>

      <div class="substep" id="s5">
        <div class="substepgrid">
          <div class="tick"><div class="node subnode">S5</div></div>
          <div class="card subcard">
            <div class="cardhead"><h3 class="cardtitle">Distributed investment</h3></div>
            <p class="desc">Adds a constraint spreading investment over time rather than concentrating it in a single phase.</p>
            <div class="chips"><span class="chip new">+ Distributed investment</span></div>
            <div class="actions">
              <a class="btn primary" href="S5_results/graphs/index.html">Dashboard &rarr;</a>
              <a class="btn ghost" href="S5_results/0_Summary.html">Summary</a>
            </div>
          </div>
        </div>
      </div>

      <div class="substep" id="s6">
        <div class="substepgrid">
          <div class="tick"><div class="node subnode">S6</div></div>
          <div class="card subcard">
            <div class="cardhead"><h3 class="cardtitle">Carbon capture limit</h3></div>
            <p class="desc">Adds a limit on the available carbon capture (CC) capacity.</p>
            <div class="chips"><span class="chip new">+ Carbon capture limit</span></div>
            <div class="actions">
              <a class="btn primary" href="S6_results/graphs/index.html">Dashboard &rarr;</a>
              <a class="btn ghost" href="S6_results/0_Summary.html">Summary</a>
            </div>
          </div>
        </div>
      </div>

      <div class="substep" id="s7">
        <div class="substepgrid">
          <div class="tick"><div class="node subnode">S7</div></div>
          <div class="card subcard">
            <div class="cardhead"><h3 class="cardtitle">Public mobility</h3></div>
            <p class="desc">Linearly increases the short-distance (SD) public mobility share from 11.87% in 2025 to 64.6% in 2050, and removes 2064.7 Mpkm/y from public aviation (LD).</p>
            <div class="chips"><span class="chip new">+ Public mobility</span></div>
            <p class="notmerged">Not included in the S8 combination below &mdash; S8 predates this scenario.</p>
            <div class="actions">
              <a class="btn primary" href="S7_results/graphs/index.html">Dashboard &rarr;</a>
              <a class="btn ghost" href="S7_results/0_Summary.html">Summary</a>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>

  <div class="marker">
    <div class="railcol"><div class="diamond"></div></div>
    <div class="note">S8 combines the <b>four</b> branches above (carbon budget, change rate, distributed investment, carbon capture) into one scenario.</div>
  </div>

  <div class="trunkline endpoint" id="s8">
    <div class="railcol"><div class="node">S8</div></div>
    <div class="card">
      <div class="cardhead"><h3 class="cardtitle">Full combination</h3><span class="tag">S8_results</span></div>
      <p class="desc">S1 + S2 baseline, with the four modifications from S3 to S6 applied together in a single scenario.</p>
      <div class="chips">
        <span class="chip base">&check; 2035 emissions cap</span>
        <span class="chip base">&check; 2050 carbon neutrality</span>
        <span class="chip base">&check; Initial stock spreading</span>
        <span class="chip all">&check; Carbon budget</span>
        <span class="chip all">&check; Limited change rate</span>
        <span class="chip all">&check; Distributed investment</span>
        <span class="chip all">&check; Carbon capture limit</span>
      </div>
      <div class="actions">
        <a class="btn primary" href="S8_results/graphs/index.html">Explore the dashboard &rarr;</a>
        <a class="btn ghost" href="S8_results/0_Summary.html">Quick summary</a>
      </div>
    </div>
  </div>

  <footer>
    <span>EnergyScope-Qu&eacute;bec &mdash; Pathway &middot; results generated automatically</span>
    <a href="https://github.com/ma-zimmer/PES_QC_Report_Results">github.com/ma-zimmer/PES_QC_Report_Results</a>
  </footer>

</div>
</body>
</html>
"""


def build_index():
    with open(os.path.join(SITE_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(_PAGE_TEMPLATE)


def main():
    published = []
    for name in SCENARIOS:
        if sync_scenario(name):
            published.append(name)
    build_index()
    print(f'\nIndex rebuilt. Scenario(s) synced: {", ".join(published) if published else "(none)"}')


if __name__ == '__main__':
    main()
