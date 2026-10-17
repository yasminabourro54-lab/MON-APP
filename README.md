# MON-APP — CarMatch AI 🚗

Recherche intelligente de voitures d'occasion au Maroc (Streamlit + Pandas + Altair).

> ⚠️ `annonces_demo.csv` = données FICTIVES de démonstration.

## Fichiers
- `app.py` : application complète (recherche + score /100 + tableau de bord graphique + comparateur)
- `annonces_demo.csv` : 35 annonces fictives pour tester
- `requirements.txt` : dépendances pour Streamlit Cloud
- `LISEZMOI.md` : guide détaillé en français

## Lancer en local
```
python -m streamlit run app.py --browser.gatherUsageStats false
```
Puis ouvrir http://localhost:8501

## Déploiement Streamlit Cloud
1. Pousser ce dossier sur GitHub
2. Aller sur https://share.streamlit.io → New app
3. Repo : `MON-APP`, Branch : `main`, File : `app.py` → Deploy
