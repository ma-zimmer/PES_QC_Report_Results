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
import os
import shutil

SITE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_OUT_DIR = os.path.join(SITE_DIR, '..', 'EnergyScope-Quebec', 'projects', 'pathway', 'out')

# Add each new SX_results folder name here as it gets generated.
SCENARIOS = [
    'S0_results',
]


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
    print(f'  OK   {name}')
    return True


def build_index(published):
    items = []
    for name in published:
        has_summary = os.path.exists(os.path.join(SITE_DIR, name, '0_Summary.html'))
        summary_link = (
            f' &middot; <a href="{name}/0_Summary.html">résumé</a>' if has_summary else ''
        )
        items.append(
            f'<li><a href="{name}/graphs/index.html">{name}</a>{summary_link}</li>'
        )
    items_html = '\n    '.join(items) if items else '<li><em>Aucun scénario publié pour le moment.</em></li>'

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Résultats EnergyScope-Quebec — Pathway</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 700px; margin: 3rem auto; padding: 0 1rem; color: #222; }}
  h1 {{ font-size: 1.4rem; }}
  ul {{ line-height: 2.2; font-size: 1.05rem; }}
  a {{ color: #0a5; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
  <h1>Résultats de scénarios — EnergyScope-Quebec (Pathway)</h1>
  <ul>
    {items_html}
  </ul>
</body>
</html>
"""
    with open(os.path.join(SITE_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    published = []
    for name in SCENARIOS:
        if sync_scenario(name):
            published.append(name)
    build_index(published)
    print(f'\nIndex rebuilt with {len(published)} scenario(s): {", ".join(published) if published else "(none)"}')


if __name__ == '__main__':
    main()
