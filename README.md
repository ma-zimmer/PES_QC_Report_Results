# PES_QC_Report_Results

Résultats détaillés (graphiques interactifs) des scénarios du modèle pathway
EnergyScope-Quebec, publiés pour accompagner le rapport.

Site : https://ma-zimmer.github.io/PES_QC_Report_Results/

## Ajouter un nouveau scénario

1. Générer le scénario avec `run_main.py` dans le dépôt `EnergyScope-Quebec`
   (crée `projects/pathway/out/<nom>/`).
2. Ajouter `<nom>` à la liste `SCENARIOS` dans `sync_results.py`.
3. Lancer :
   ```
   python sync_results.py
   ```
4. Commit et push :
   ```
   git add -A
   git commit -m "Add <nom> results"
   git push
   ```
