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
import sys
from datetime import datetime, timezone

import pandas as pd

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_REPO_DIR = os.path.join(SITE_DIR, '..', 'EnergyScope-Quebec')
SOURCE_OUT_DIR = os.path.join(SOURCE_REPO_DIR, 'projects', 'pathway', 'out')
SOURCE_SRC_DIR = os.path.join(SOURCE_REPO_DIR, 'projects', 'pathway', 'src')

# transition_cost_by_phase_category is the canonical system-cost breakdown
# (CAPEX net of salvage, hors 2015_2020, + OPEX incl. the standalone
# YEAR_2020 term) — same convention as the 0b_Transition_cost.html dashboard
# plot. Deliberately NOT the model's own 'Transition_cost' output, which
# mixes in the CRF-annuity formulation (C_tot_capex) and reads far higher.
sys.path.insert(0, SOURCE_SRC_DIR)
from plot_results import load_results, transition_cost_by_phase_category  # noqa: E402

# Published scenarios. S0 was a preliminary run (not published). S8 (the full
# combination) now includes all five of S3-S7's modifications, public
# mobility included.
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


# Lightning-bolt glyph used as the browser-tab icon — consistent branding, no
# extra asset file. Injected right after <head> in the pages a reader lands on
# directly (the landing page itself, each scenario's dashboard, and its
# quick-summary chart); the ~230 individual chart pages per scenario are only
# ever seen inside an iframe, so their tab icon never shows.
_FAVICON_LINK = (
    '<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' '
    'viewBox=\'0 0 24 24\'%3E%3Cpath d=\'M13 2 3 14h7l-1 8 11-14h-7z\' fill=\'%23ffd166\' '
    'stroke=\'%23101820\' stroke-width=\'1.3\' stroke-linejoin=\'round\'/%3E%3C/svg%3E">'
)
_HEAD_RE = re.compile(r'<head[^>]*>', re.IGNORECASE)


def _inject_favicon(path):
    with open(path, encoding='utf-8') as f:
        html = f.read()
    if 'rel="icon"' in html:
        return
    new_html, n = _HEAD_RE.subn(lambda m: m.group(0) + _FAVICON_LINK, html, count=1)
    if n == 0:
        print(f'  WARN {path}: <head> not found, favicon not injected')
        return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_html)


# ---------------------------------------------------------------------------
# KPI extraction — minimal subset of generate_report.py's extract_scenario(),
# just the two numbers shown on each landing-page card.
# ---------------------------------------------------------------------------

def _extract_kpis(name):
    kpi = {'transition_cost': None, 'cum_gwp': None}
    pkl_path = os.path.join(SOURCE_OUT_DIR, name, '_Results.pkl')
    if not os.path.exists(pkl_path):
        return kpi
    try:
        results = load_results(name)  # applies _drop_excluded_techs, same as every other dashboard/report script
    except Exception as e:
        print(f'  WARN {name}: could not read _Results.pkl for KPIs ({e})')
        return kpi

    cost = transition_cost_by_phase_category(results)
    if cost is not None and not cost.empty:
        kpi['transition_cost'] = float(cost[['CAPEX', 'OPEX']].sum().sum())  # already B$

    tg = results.get('TotalGwp')
    if tg is not None and not tg.empty:
        df = tg.reset_index()
        year_col = df.columns[0]
        val_col = 'TotalGWP' if 'TotalGWP' in df.columns else df.columns[1]
        df['yr'] = df[year_col].astype(str).str.replace('YEAR_', '').astype(int)
        df['val'] = pd.to_numeric(df[val_col], errors='coerce') / 1e3  # kt -> Mt
        gwp = {int(y): v for y, v in zip(df['yr'], df['val']) if pd.notna(v)}
        yrs = sorted(gwp)
        if len(yrs) >= 2:
            cum = 0.0
            for y0, y1 in zip(yrs[:-1], yrs[1:]):
                cum += (y1 - y0) * (gwp[y0] + gwp[y1]) / 2.0
            kpi['cum_gwp'] = cum
    return kpi


def _fmt_kpi(val):
    return f'{val:,.0f}' if val is not None else '–'


def sync_scenario(name):
    src = os.path.join(SOURCE_OUT_DIR, name)
    dst = os.path.join(SITE_DIR, name)
    src_graphs = os.path.join(src, 'graphs')
    if not os.path.isdir(src_graphs):
        print(f'  SKIP {name}: no graphs/ folder found at {src_graphs}')
        return False, {}
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
        _inject_favicon(dashboard)
    summary = os.path.join(dst, '0_Summary.html')
    if os.path.exists(summary):
        _inject_favicon(summary)
    print(f'  OK   {name}')
    return True, _extract_kpis(name)


# ---------------------------------------------------------------------------
# Landing page — one flat, grouped list: S1-S2 (baseline), S3-S7 (one
# modification at a time, independently), S8 (all five combined). Content is
# bespoke (not templated from SCENARIOS) since the narrative structure —
# which scenario builds on which — is fixed.
# ---------------------------------------------------------------------------

_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scenario Results — EnergyScope-Québec</title>
<meta property="og:type" content="website">
<meta property="og:url" content="https://ma-zimmer.github.io/PES_QC_Report_Results/">
<meta property="og:title" content="Scenario Results — EnergyScope-Québec">
<meta property="og:description" content="Interactive dashboards for the EnergyScope-Québec Pathway transition scenarios (S1-S8), published to accompany the report.">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="Scenario Results — EnergyScope-Québec">
<meta name="twitter:description" content="Interactive dashboards for the EnergyScope-Québec Pathway transition scenarios (S1-S8), published to accompany the report.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M13 2 3 14h7l-1 8 11-14h-7z' fill='%23ffd166' stroke='%23101820' stroke-width='1.3' stroke-linejoin='round'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #FAFAF9; --ink: #1C1C1A; --ink-soft: #6B6A64; --ink-faint: #9A998F;
    --line: #E4E3DE; --accent: #0B6E5B;
  }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) {
      --bg: #121210; --ink: #ECEBE6; --ink-soft: #A7A69D; --ink-faint: #75746B;
      --line: #2A2A25; --accent: #5FCBAC;
    }
  }
  :root[data-theme="dark"] {
    --bg: #121210; --ink: #ECEBE6; --ink-soft: #A7A69D; --ink-faint: #75746B;
    --line: #2A2A25; --accent: #5FCBAC;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: "IBM Plex Sans", system-ui, -apple-system, sans-serif;
    font-size: 16px; line-height: 1.55; -webkit-font-smoothing: antialiased;
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .num { font-variant-numeric: tabular-nums; }

  .wrap { max-width: 720px; margin: 0 auto; padding: 5.5rem 1.75rem 6rem; }

  /* Deep-link targets: id="s1".."s8" on each row, so the report can link
     straight to e.g. #s3. scroll-margin-top keeps the row clear of the
     viewport edge; the :target rule highlights the linked scenario's name. */
  [id^="s"] { scroll-margin-top: 2rem; }
  [id^="s"]:target .name { color: var(--accent); }

  header.hero { margin-bottom: 4.5rem; }
  .eyebrow {
    font-size: 0.78rem; letter-spacing: 0.1em; text-transform: uppercase;
    color: var(--ink-faint); margin: 0 0 1rem; font-weight: 500;
  }
  h1 {
    font-family: "Newsreader", Georgia, serif; font-weight: 500;
    font-size: clamp(1.9rem, 1.5rem + 1.6vw, 2.4rem); line-height: 1.2;
    margin: 0 0 1.3rem; text-wrap: balance; color: var(--ink);
  }
  .lede { font-size: 1.02rem; line-height: 1.65; color: var(--ink-soft); margin: 0; max-width: 56ch; }
  .lede strong { color: var(--ink); font-weight: 600; }

  .grouplabel {
    font-size: 0.78rem; letter-spacing: 0.08em; text-transform: uppercase;
    color: var(--ink-faint); font-weight: 500; margin: 3.2rem 0 0.4rem;
  }
  .grouplabel:first-of-type { margin-top: 0; }

  .row {
    display: flex; justify-content: space-between; align-items: baseline; gap: 2rem;
    padding: 1.4rem 0; border-top: 1px solid var(--line);
  }
  .row-main { max-width: 38ch; }
  .row .name { font-size: 1.05rem; font-weight: 600; color: var(--ink); }
  .row .name .tag { color: var(--ink-faint); font-weight: 400; margin-right: 0.5rem; }
  .row .desc { color: var(--ink-soft); font-size: 0.92rem; margin: 0.35rem 0 0; line-height: 1.5; }
  .row-side { flex-shrink: 0; text-align: right; }
  .row .metrics { color: var(--ink); font-size: 0.9rem; white-space: nowrap; }
  .row .metrics .unit { color: var(--ink-faint); }
  .row .links { margin-top: 0.4rem; font-size: 0.85rem; white-space: nowrap; }
  .row .links a + a { margin-left: 0.9rem; }

  footer {
    margin-top: 3.5rem; padding-top: 1.5rem; border-top: 1px solid var(--line);
    color: var(--ink-faint); font-size: 0.82rem;
    display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap;
  }
  footer a { color: var(--ink-faint); }
  footer a:hover { color: var(--accent); }

  @media (max-width: 560px) {
    .wrap { padding: 3.5rem 1.25rem 4rem; }
    .row { flex-direction: column; gap: 0.6rem; align-items: flex-start; }
    .row-side { text-align: left; }
  }
</style>
</head>
<body>
<div class="wrap">

  <header class="hero">
    <p class="eyebrow">EnergyScope-Québec &middot; Pathway model</p>
    <h1>Transition scenario results</h1>
    <p class="lede">This site accompanies the report and gives access to the interactive dashboard for each simulated scenario. <strong>S1</strong> and <strong>S2</strong> build a common baseline; <strong>S3&ndash;S7</strong> each test one modification in isolation; <strong>S8</strong> combines all five.</p>
  </header>

  <p class="grouplabel">Baseline</p>

  <div class="row" id="s1">
    <div class="row-main">
      <div class="name"><span class="tag">S1</span>Base case</div>
      <p class="desc">Only the emissions constraints are active: a 2035 emissions cap and carbon neutrality by 2050.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S1_COST__ <span class="unit">B$</span> &middot; __S1_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S1_results/graphs/index.html">Dashboard</a><a href="S1_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <div class="row" id="s2">
    <div class="row-main">
      <div class="name"><span class="tag">S2</span>Initial stock spreading</div>
      <p class="desc">Adds a constraint that spreads the replacement of the initial technology stock over time.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S2_COST__ <span class="unit">B$</span> &middot; __S2_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S2_results/graphs/index.html">Dashboard</a><a href="S2_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <p class="grouplabel">One change at a time</p>

  <div class="row" id="s3">
    <div class="row-main">
      <div class="name"><span class="tag">S3</span>Carbon budget</div>
      <p class="desc">Adds a cumulative carbon budget over 2020&ndash;2050.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S3_COST__ <span class="unit">B$</span> &middot; __S3_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S3_results/graphs/index.html">Dashboard</a><a href="S3_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <div class="row" id="s4">
    <div class="row-main">
      <div class="name"><span class="tag">S4</span>Limited change rate</div>
      <p class="desc">Adds a constraint limiting how fast technologies can be deployed from one phase to the next.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S4_COST__ <span class="unit">B$</span> &middot; __S4_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S4_results/graphs/index.html">Dashboard</a><a href="S4_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <div class="row" id="s5">
    <div class="row-main">
      <div class="name"><span class="tag">S5</span>Distributed investment</div>
      <p class="desc">Adds a constraint spreading investment over time rather than concentrating it in a single phase.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S5_COST__ <span class="unit">B$</span> &middot; __S5_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S5_results/graphs/index.html">Dashboard</a><a href="S5_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <div class="row" id="s6">
    <div class="row-main">
      <div class="name"><span class="tag">S6</span>Carbon capture limit</div>
      <p class="desc">Adds a limit on the available carbon capture (CC) capacity.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S6_COST__ <span class="unit">B$</span> &middot; __S6_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S6_results/graphs/index.html">Dashboard</a><a href="S6_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <div class="row" id="s7">
    <div class="row-main">
      <div class="name"><span class="tag">S7</span>Public mobility</div>
      <p class="desc">Linearly increases the short-distance (SD) public mobility share from 11.87% in 2025 to 64.6% in 2050, and removes 2064.7 Mpkm/y from public aviation (LD).</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S7_COST__ <span class="unit">B$</span> &middot; __S7_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S7_results/graphs/index.html">Dashboard</a><a href="S7_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <p class="grouplabel">Combined</p>

  <div class="row" id="s8">
    <div class="row-main">
      <div class="name"><span class="tag">S8</span>Full combination</div>
      <p class="desc">S1 + S2 baseline, with the five modifications from S3 to S7 applied together in a single scenario.</p>
    </div>
    <div class="row-side">
      <div class="num metrics">__S8_COST__ <span class="unit">B$</span> &middot; __S8_GWP__ <span class="unit">Mt</span></div>
      <div class="links"><a href="S8_results/graphs/index.html">Dashboard</a><a href="S8_results/0_Summary.html">Summary</a></div>
    </div>
  </div>

  <footer>
    <span>EnergyScope-Qu&eacute;bec &mdash; Pathway &middot; results generated automatically &middot; last updated __UPDATED__</span>
    <a href="https://github.com/ma-zimmer/PES_QC_Report_Results">github.com/ma-zimmer/PES_QC_Report_Results</a>
  </footer>

</div>
</body>
</html>
"""


def build_index(kpis):
    html = _PAGE_TEMPLATE
    for name in SCENARIOS:
        token = name.replace('_results', '').upper()  # 'S1_results' -> 'S1'
        k = kpis.get(name, {})
        html = html.replace(f'__{token}_COST__', _fmt_kpi(k.get('transition_cost')))
        html = html.replace(f'__{token}_GWP__', _fmt_kpi(k.get('cum_gwp')))
    updated = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    html = html.replace('__UPDATED__', updated)
    path = os.path.join(SITE_DIR, 'index.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    published = []
    kpis = {}
    for name in SCENARIOS:
        ok, kpi = sync_scenario(name)
        if ok:
            published.append(name)
            kpis[name] = kpi
    build_index(kpis)
    print(f'\nIndex rebuilt. Scenario(s) synced: {", ".join(published) if published else "(none)"}')


if __name__ == '__main__':
    main()
