# 🚗 CarMatch AI — Voitures d'occasion au Maroc

> ⚠️ **Données de démonstration** : le fichier `annonces_demo.csv` contient **35 annonces FICTIVES**
> créées pour tester l'application. Ce ne sont **pas de vraies offres**.
> Pour utiliser de vraies annonces, importez votre propre CSV (sources autorisées uniquement).

Application web simple (Python + Streamlit + Pandas) qui aide à trouver des voitures
d'occasion au Maroc selon vos critères. **Aucune connaissance en programmation requise pour l'utiliser.**

---

## 📁 Fichiers fournis

| Fichier | Rôle |
|---|---|
| `app.py` | L'application complète |
| `requirements.txt` | La liste des outils Python à installer |
| `annonces_demo.csv` | 35 annonces fictives pour tester (DÉMO) |
| `LISEZMOI.md` | Ce guide |

### Format du CSV

Colonnes : `id, marque, modele, annee, prix_mad, kilometrage, carburant, boite_vitesses, ville, options, photo_url, lien_annonce`

- `options` : séparées par `;` — exemple : `Climatisation;GPS;Caméra de recul`
- `photo_url` et `lien_annonce` : peuvent être vides (l'application affiche « Pas de photo »).
- Lignes avec `prix` ou `kilometrage` vide : exclues dès qu'un filtre prix/km s'applique (2 lignes de démo testent ce cas : n°32 sans km, n°33 sans prix).

---

## 🖥️ Installation sur Windows (pas à pas, ~10 minutes)

### Étape 1 — Installer Python
1. Allez sur **https://www.python.org/downloads/** et cliquez **Download Python**.
2. Lancez l'installateur.
3. ⚠️ **Cochez la case « Add python.exe to PATH »** en bas de la première fenêtre, puis cliquez **Install Now**.
4. Vérifiez : ouvrez le menu Démarrer, tapez `cmd`, ouvrez **Invite de commandes**, tapez :
   ```
   python --version
   ```
   Vous devez voir `Python 3.x.x`. Sinon, réinstallez en cochant bien la case PATH.

### Étape 2 — Ouvrir le dossier de l'application
1. Ouvrez l'**Invite de commandes** (`cmd`).
2. Allez dans le dossier (adaptez le chemin) :
   ```
   cd "C:\Users\hp\Desktop\MON APP"
   ```

### Étape 3 — Installer les outils nécessaires
Dans la même fenêtre, tapez :
```
pip install -r requirements.txt
```
Patientez 2-3 minutes (téléchargement de Streamlit + Pandas, gratuits).

### Étape 4 — Lancer l'application
Toujours dans la même fenêtre :
```
streamlit run app.py
```
- Une page web s'ouvre automatiquement (adresse `http://localhost:8501`).
- Sinon, copiez cette adresse dans Chrome / Edge.
- Pour arrêter : `Ctrl + C` dans la fenêtre noire.

---

## 🧭 Comment utiliser l'application (sans programmer)

1. **Barre de gauche = vos critères obligatoires** : budget min/max (MAD), marque, modèle,
   année min/max, kilométrage max, carburant, boîte de vitesses, ville.
2. **Préférences facultatives** : cochez les options souhaitées (GPS, caméra…).
   Elles n'excluent rien, elles améliorent juste le **score /100**.
3. **Résultats** : seules les voitures qui respectent **TOUS** les critères obligatoires s'affichent,
   classées selon le tri choisi (score, prix, année, kilométrage).
4. **Cartes** : photo (ou « pas de photo »), prix, année, km, ville, carburant, boîte,
   options + bouton vers l'annonce originale.
5. **Comparaison** : en bas, sélectionnez 2 ou 3 voitures pour voir un tableau comparatif.
6. **Aucun résultat ?** Un message s'affiche avec des conseils (élargir le budget, mettre « Toutes », etc.).
7. **Importer vos annonces** : en haut de la barre latérale, « Importer un fichier CSV ».
   Votre fichier doit avoir les mêmes colonnes que `annonces_demo.csv`.

---

## 🧮 Comment ça marche ? (explication simple)

1. **Chargement** : l'application lit le CSV dans un tableau (Pandas).
2. **Nettoyage** : espaces supprimés, prix/km/année convertis en nombres,
   cases vides = « donnée manquante » (gérées, jamais de plantage).
3. **Filtre obligatoire** : on garde uniquement les lignes qui respectent chaque critère.
   Exemple : prix entre min et max **ET** année dans l'intervalle **ET** km ≤ max **ET** même ville, etc.
4. **Score facultatif /100** : pour chaque voiture gardée, on ajoute des points :
   +10 par option souhaitée trouvée (max 50), +jusqu'à 20 si prix bien sous le budget max,
   +jusqu'à 15 si faible kilométrage, +jusqu'à 15 si année récente.
   Le détail du score est affiché sous chaque carte (transparence).
5. **Tri + affichage** : on trie (prix, score…) puis on affiche des cartes + un comparateur + un bouton de téléchargement CSV des résultats.

## 🔌 Passer aux vraies annonces (sources autorisées)

- N'utilisez que des annonces que vous avez le droit d'exploiter
  (vos propres relevés, exports fournis par un partenaire, fichiers internes).
- Ne copiez jamais massivement un site sans son autorisation (conditions d'utilisation + loi).
- Concrètement : préparez un CSV avec les mêmes colonnes et importez-le via le bouton.
  L'application fonctionne à l'identique, sans changer le code.

## ✅ Vérifications effectuées

- 35 lignes de démo, colonnes conformes, 2 lignes à données manquantes volontaires (n°32, n°33) + 3 lignes sans photo (n°4, 12, 23, 31) pour tester l'affichage.
- Filtres cumulatifs (ET logique), ville/marque « Toutes » = pas de filtre, modèles dépendants de la marque.
- Message dédié si 0 résultat. Score plafonné à 100 avec détail affiché.
- Code relu : gestion des CSV importés sans colonne `id`, sans photo/lien, compatibilité Streamlit ≥ 1.32.
- ⚠️ Python n'étant pas installé sur la machine de génération, exécutez `streamlit run app.py` chez vous :
  si un message d'erreur apparaît, copiez-le pour diagnostic.
