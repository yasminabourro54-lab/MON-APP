"""CarMatch AI — Recherche intelligente de voitures d'occasion au Maroc.
Application Streamlit + Pandas + Altair (graphiques inclus).
IMPORTANT : annonces_demo.csv contient des DONNEES FICTIVES DE DEMONSTRATION.
Ne jamais les présenter comme de vraies offres.
"""

import pandas as pd
import streamlit as st
import altair as alt

# ---------- Configuration ----------
st.set_page_config(
    page_title="CarMatch AI — Occasions Maroc",
    page_icon="🚗",
    layout="wide",
)

FICHIER_DEMO = "annonces_demo.csv"

COLONNES_ATTENDUES = [
    "id", "marque", "modele", "annee", "prix_mad", "kilometrage",
    "carburant", "boite_vitesses", "ville", "options",
    "photo_url", "lien_annonce",
]


# ---------- Chargement / nettoyage ----------
@st.cache_data
def charger_csv_depuis_chemin(chemin: str) -> pd.DataFrame:
    df = pd.read_csv(chemin)
    return nettoyer_donnees(df)


def nettoyer_donnees(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLONNES_ATTENDUES:
        if col not in df.columns:
            df[col] = pd.NA

    for col in ["marque", "modele", "carburant", "boite_vitesses", "ville"]:
        df[col] = df[col].astype("string").str.strip()
    for col in ["options", "photo_url", "lien_annonce"]:
        df[col] = df[col].astype("string").str.strip()

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    if df["id"].isna().all():
        df["id"] = range(1, len(df) + 1)
    else:
        df["id"] = df["id"].fillna(pd.Series(range(1, len(df) + 1), index=df.index))
        df["id"] = df["id"].astype(int)
    df["prix_mad"] = pd.to_numeric(df["prix_mad"], errors="coerce")
    df["kilometrage"] = pd.to_numeric(df["kilometrage"], errors="coerce")
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")

    df["carburant"] = df["carburant"].str.lower().str.strip()
    df["boite_vitesses"] = df["boite_vitesses"].str.lower().str.strip()

    df["options_liste"] = df["options"].fillna("").str.split(";")
    df["options_liste"] = df["options_liste"].apply(
        lambda lst: [str(x).strip() for x in lst if str(x).strip() != ""]
    )
    # Champ texte global pour la recherche intelligente
    df["texte_global"] = (
        df["marque"].fillna("") + " " + df["modele"].fillna("") + " "
        + df["ville"].fillna("") + " " + df["carburant"].fillna("") + " "
        + df["boite_vitesses"].fillna("") + " " + df["options"].fillna("")
    ).str.lower()
    return df


def charger_csv_importe(fichier) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(fichier)
        return nettoyer_donnees(df)
    except Exception as e:
        st.error(f"Impossible de lire ce fichier CSV : {e}")
        return None


# ---------- Filtres ----------
def appliquer_filtres_obligatoires(df: pd.DataFrame, c: dict) -> pd.DataFrame:
    res = df.copy()
    res = res[res["prix_mad"].notna()]
    res = res[(res["prix_mad"] >= c["budget_min"]) & (res["prix_mad"] <= c["budget_max"])]

    if c["marque"] != "Toutes":
        res = res[res["marque"].fillna("").str.lower() == c["marque"].lower()]
    if c["modele"] != "Tous":
        res = res[res["modele"].fillna("").str.lower() == c["modele"].lower()]

    res = res[res["annee"].notna()]
    res = res[(res["annee"] >= c["annee_min"]) & (res["annee"] <= c["annee_max"])]

    res = res[res["kilometrage"].notna()]
    res = res[res["kilometrage"] <= c["km_max"]]

    if c["carburant"] != "Tous":
        res = res[res["carburant"].fillna("") == c["carburant"].lower()]
    if c["boite"] != "Toutes":
        res = res[res["boite_vitesses"].fillna("") == c["boite"].lower()]
    if c["ville"] != "Toutes":
        res = res[res["ville"].fillna("").str.lower() == c["ville"].lower()]
    return res


# ---------- Score intelligent ----------
def calculer_score(ligne: pd.Series, options_preferees: list, budget_max: float,
                   mots_libres: list) -> tuple[float, str]:
    """Score /100 : options (+10 max 50) + prix attractif (max 20)
    + faible km (max 15) + année récente (max 15) + bonus recherche libre (max 10, plafonné à 100).
    """
    score = 0.0
    details = []

    if options_preferees:
        opts_annonce = [o.lower() for o in (ligne["options_liste"] or [])]
        trouvees = [o for o in options_preferees
                    if o.lower() in [x.lower() for x in opts_annonce]
                    or any(o.lower() in x.lower() for x in opts_annonce)]
        pts = min(len(trouvees) * 10, 50)
        score += pts
        if trouvees:
            details.append(f"Options: {', '.join(trouvees)} (+{pts})")

    if pd.notna(ligne["prix_mad"]) and budget_max > 0:
        ratio = 1 - (ligne["prix_mad"] / budget_max)
        pts = round(max(0, min(ratio, 1)) * 20, 1)
        score += pts
        details.append(f"Prix attractif (+{pts})")

    if pd.notna(ligne["kilometrage"]):
        pts = round(max(0, min(1 - (ligne["kilometrage"] / 200000), 1)) * 15, 1)
        score += pts
        details.append(f"Kilométrage (+{pts})")

    if pd.notna(ligne["annee"]):
        pts = round(max(0, min((int(ligne["annee"]) - 2005) / 20, 1)) * 15, 1)
        score += pts
        details.append(f"Année récente (+{pts})")

    # Bonus recherche libre : +5 par mot-clé trouvé (max 10)
    if mots_libres:
        texte = str(ligne.get("texte_global", "")).lower()
        nb = sum(1 for m in mots_libres if m in texte)
        if nb:
            pts = min(nb * 5, 10)
            score += pts
            details.append(f"Recherche «{' '.join(mots_libres)}» (+{pts})")

    return round(min(score, 100), 1), " · ".join(details) if details else "Aucun bonus"


def badge_prix(ligne: pd.Series, medianes_modele: dict, mediane_globale: float) -> str:
    """Badge bonne affaire vs médiane du même modèle (ou globale)."""
    if pd.isna(ligne["prix_mad"]):
        return ""
    key = (str(ligne["marque"]).lower(), str(ligne["modele"]).lower())
    ref = medianes_modele.get(key, mediane_globale)
    if pd.isna(ref) or ref == 0:
        return ""
    ratio = ligne["prix_mad"] / ref
    if ratio <= 0.8:
        return "💎 Excellent prix"
    if ratio <= 0.9:
        return "🔥 Bonne affaire"
    if ratio >= 1.2:
        return "⚠️ Au-dessus du marché"
    return "✅ Prix correct"


# ---------- Interface ----------
st.title("🚗 CarMatch AI — Voitures d'occasion au Maroc")
st.warning(
    "⚠️ **Données de démonstration** : les annonces par défaut sont "
    "FICTIVES (`annonces_demo.csv`). Importez votre propre CSV pour de vraies annonces."
)

# --- Source ---
st.sidebar.header("📂 Source des annonces")
fichier_importe = st.sidebar.file_uploader(
    "Importer un CSV (optionnel)",
    type=["csv"],
    help="Colonnes : " + ", ".join(COLONNES_ATTENDUES),
)

if fichier_importe is not None:
    df_brut = charger_csv_importe(fichier_importe)
    if df_brut is None:
        st.stop()
    source_label = "fichier importé"
else:
    try:
        df_brut = charger_csv_depuis_chemin(FICHIER_DEMO)
        source_label = "annonces_demo.csv (DÉMO FICTIVE)"
    except FileNotFoundError:
        st.error(f"Fichier {FICHIER_DEMO} introuvable. Importez un CSV.")
        st.stop()

st.caption(f"📊 {len(df_brut)} annonce(s) chargée(s) depuis : {source_label}")

nb_sans_prix = int(df_brut["prix_mad"].isna().sum())
nb_sans_km = int(df_brut["kilometrage"].isna().sum())
if nb_sans_prix or nb_sans_km:
    st.info(
        f"ℹ️ {nb_sans_prix} sans prix, {nb_sans_km} sans kilométrage : "
        "exclues dès qu'un filtre prix/km s'applique."
    )

# --- Menus ---
marques = ["Toutes"] + sorted(df_brut["marque"].dropna().unique().tolist())
villes = ["Toutes"] + sorted(df_brut["ville"].dropna().unique().tolist())
carburants = ["Tous"] + sorted(df_brut["carburant"].dropna().str.title().unique().tolist())
boites = ["Toutes"] + sorted(df_brut["boite_vitesses"].dropna().str.title().unique().tolist())
toutes_options = sorted({o for lst in df_brut["options_liste"] for o in lst if o})

# --- Sidebar : critères ---
st.sidebar.header("🔍 Vos critères obligatoires")
prix_min_data = int(df_brut["prix_mad"].min(skipna=True) or 0)
prix_max_data = int(df_brut["prix_mad"].max(skipna=True) or 600000)
budget_min, budget_max = st.sidebar.slider(
    "Budget (MAD)", min_value=0, max_value=max(prix_max_data, 600000),
    value=(0, max(prix_max_data, 600000)), step=5000,
)
marque_choisie = st.sidebar.selectbox("Marque", marques)
if marque_choisie == "Toutes":
    modeles = ["Tous"] + sorted(df_brut["modele"].dropna().unique().tolist())
else:
    modeles = ["Tous"] + sorted(
        df_brut[df_brut["marque"].fillna("").str.lower() == marque_choisie.lower()]["modele"]
        .dropna().unique().tolist()
    )
modele_choisi = st.sidebar.selectbox("Modèle", modeles)

annee_min_data = int(df_brut["annee"].min(skipna=True) or 2005)
annee_max_data = int(df_brut["annee"].max(skipna=True) or 2026)
annee_min, annee_max = st.sidebar.slider(
    "Année", min_value=annee_min_data, max_value=annee_max_data,
    value=(annee_min_data, annee_max_data),
)
km_max = st.sidebar.number_input(
    "Kilométrage maximal (km)", min_value=0, max_value=500000,
    value=200000, step=5000,
)
carburant_choisi = st.sidebar.selectbox("Carburant", carburants)
boite_choisie = st.sidebar.selectbox("Boîte de vitesses", boites)
ville_choisie = st.sidebar.selectbox("Ville", villes)

st.sidebar.header("🧠 Recherche intelligente")
recherche_libre = st.sidebar.text_input(
    "Mot-clés (ex : GPS cuir automatique SUV)",
    placeholder="Tapez des mots-clés…",
    help="Bonus de score si trouvés dans marque, modèle, options, ville, carburant.",
)
mots_libres = [m.lower() for m in recherche_libre.split() if len(m) >= 2]

st.sidebar.header("✨ Préférences (score)")
options_preferees = st.sidebar.multiselect(
    "Options souhaitées (bonus, n'excluent rien)", toutes_options,
)

st.sidebar.header("↕️ Tri")
tri = st.sidebar.selectbox(
    "Trier par",
    ["Score décroissant", "Prix croissant", "Prix décroissant", "Année récente", "Faible kilométrage"],
)

criteres = {
    "budget_min": budget_min, "budget_max": budget_max,
    "marque": marque_choisie, "modele": modele_choisi,
    "annee_min": annee_min, "annee_max": annee_max,
    "km_max": km_max, "carburant": carburant_choisi,
    "boite": boite_choisie, "ville": ville_choisie,
}

# --- Filtrage + score ---
resultats = appliquer_filtres_obligatoires(df_brut, criteres).copy()

# Médianes pour badges "bonne affaire" (calculées sur tout le jeu chargé)
mediane_globale = df_brut["prix_mad"].median(skipna=True)
medianes_modele = (
    df_brut.dropna(subset=["prix_mad"])
    .groupby([df_brut["marque"].fillna("").str.lower(),
              df_brut["modele"].fillna("").str.lower()])["prix_mad"]
    .median().to_dict()
)

if resultats.empty:
    st.error(
        "😕 **Aucune annonce ne correspond exactement.** "
        "Élargissez le budget / kilométrage, ou choisissez « Toutes »."
    )
    # Suggestions intelligentes : relâchements
    st.subheader("💡 Suggestions automatiques")
    col_a, col_b, col_c = st.columns(3)
    sans_ville = appliquer_filtres_obligatoires(df_brut, {**criteres, "ville": "Toutes"})
    with col_a:
        st.metric("Sans filtre ville", f"{len(sans_ville)} résultat(s)")
    large_km = appliquer_filtres_obligatoires(df_brut, {**criteres, "km_max": criteres["km_max"] + 100000})
    with col_b:
        st.metric("Km max +100 000", f"{len(large_km)} résultat(s)")
    large_budget = appliquer_filtres_obligatoires(
        df_brut, {**criteres, "budget_max": int(criteres["budget_max"] * 1.2) + 10000})
    with col_c:
        st.metric("Budget +20 %", f"{len(large_budget)} résultat(s)")
    st.info("Astuce : retirez un filtre à la fois dans la barre de gauche pour voir ce qui bloque.")
    st.stop()

scores, explications = [], []
for _, lig in resultats.iterrows():
    s, e = calculer_score(lig, options_preferees, budget_max if budget_max > 0 else 1, mots_libres)
    scores.append(s)
    explications.append(e)
resultats["score"] = scores
resultats["detail_score"] = explications
resultats["badge"] = resultats.apply(
    lambda r: badge_prix(r, medianes_modele, mediane_globale), axis=1)

if tri == "Score décroissant":
    resultats = resultats.sort_values("score", ascending=False)
elif tri == "Prix croissant":
    resultats = resultats.sort_values("prix_mad", ascending=True)
elif tri == "Prix décroissant":
    resultats = resultats.sort_values("prix_mad", ascending=False)
elif tri == "Année récente":
    resultats = resultats.sort_values("annee", ascending=False)
else:
    resultats = resultats.sort_values("kilometrage", ascending=True)

st.success(f"✅ **{len(resultats)} voiture(s)** correspondent. Tri : {tri}.")

# --- Recommandations IA (top 3) ---
st.subheader("🤖 Recommandations intelligentes (Top 3)")
top3 = resultats.head(3)
cols = st.columns(3)
for i, (_, r) in enumerate(top3.iterrows()):
    with cols[i]:
        with st.container(border=True):
            st.markdown(f"**#{int(r['id'])} {r['marque']} {r['modele']}**")
            st.markdown(f"⭐ **{r['score']}/100** {r['badge']}")
            prix_txt = f"{int(r['prix_mad']):,} MAD".replace(",", " ") if pd.notna(r["prix_mad"]) else "?"
            annee_txt2 = str(int(r["annee"])) if pd.notna(r["annee"]) else "?"
            km_txt = f"{int(r['kilometrage']):,} km".replace(",", " ") if pd.notna(r["kilometrage"]) else "?"
            st.caption(f"💰 {prix_txt} · 📅 {annee_txt2} · 🛣️ {km_txt}")

# --- Onglets : résultats / dashboard / comparateur ---
onglet_res, onglet_dash, onglet_comp = st.tabs(
    ["🔍 Résultats", "📊 Tableau de bord graphique", "⚖️ Comparateur"]
)

with onglet_res:
    def afficher_carte(ligne: pd.Series):
        annee_txt = int(ligne["annee"]) if pd.notna(ligne["annee"]) else "Année ?"
        titre = f"{ligne['marque']} {ligne['modele']} — {annee_txt}"
        with st.container(border=True):
            st.subheader(f"⭐ {ligne['score']}/100 — {titre} {ligne['badge']}")
            col_img, col_info = st.columns([1, 1])
            with col_img:
                if pd.notna(ligne["photo_url"]) and str(ligne["photo_url"]).strip() != "":
                    st.image(str(ligne["photo_url"]), width='stretch')
                else:
                    st.info("📷 Pas de photo disponible.")
            with col_info:
                prix = f"{int(ligne['prix_mad']):,} MAD".replace(",", " ") if pd.notna(ligne["prix_mad"]) else "Non renseigné"
                km = f"{int(ligne['kilometrage']):,} km".replace(",", " ") if pd.notna(ligne["kilometrage"]) else "Non renseigné"
                st.write(f"💰 **Prix :** {prix}")
                st.write(f"📅 **Année :** {int(ligne['annee']) if pd.notna(ligne['annee']) else 'Non renseignée'}")
                st.write(f"🛣️ **Kilométrage :** {km}")
                st.write(f"📍 **Ville :** {ligne['ville'] if pd.notna(ligne['ville']) else 'Non renseignée'}")
                st.write(f"⛽ **Carburant :** {str(ligne['carburant']).title() if pd.notna(ligne['carburant']) else '?'}")
                st.write(f"⚙️ **Boîte :** {str(ligne['boite_vitesses']).title() if pd.notna(ligne['boite_vitesses']) else '?'}")
                opts = ", ".join(ligne["options_liste"]) if ligne["options_liste"] else "Aucune"
                st.write(f"🧩 **Options :** {opts}")
                st.caption(f"ℹ️ Score : {ligne['detail_score']}")
                if pd.notna(ligne["lien_annonce"]) and str(ligne["lien_annonce"]).strip() != "":
                    st.link_button("🔗 Voir l'annonce originale", str(ligne["lien_annonce"]))

    for _, lig in resultats.iterrows():
        afficher_carte(lig)

with onglet_dash:
    st.header("📊 Tableau de bord — illustrations graphiques")
    st.caption("Graphiques calculés sur les **résultats filtrés** (ce que vous voyez dans l'onglet Résultats).")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🚗 Voitures", len(resultats))
    k2.metric("💰 Prix médian", f"{int(resultats['prix_mad'].median()):,} MAD".replace(",", " "))
    k3.metric("💰 Prix moyen", f"{int(resultats['prix_mad'].mean()):,} MAD".replace(",", " "))
    k4.metric("🛣️ Km médian", f"{int(resultats['kilometrage'].median()):,} km".replace(",", " "))

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("💰 Prix moyen par marque")
        prix_marque = resultats.dropna(subset=["prix_mad"]).groupby("marque")["prix_mad"].mean().sort_values()
        st.bar_chart(prix_marque)

        st.subheader("⛽ Répartition par carburant")
        rep_carb = resultats["carburant"].dropna().str.title().value_counts()
        st.bar_chart(rep_carb)
        # Camembert Altair
        if not rep_carb.empty:
            df_pie = rep_carb.reset_index()
            df_pie.columns = ["carburant", "nombre"]
            pie = alt.Chart(df_pie).mark_arc(innerRadius=40).encode(
                theta="nombre", color="carburant",
                tooltip=["carburant", "nombre"],
            ).properties(height=280)
            st.altair_chart(pie, width='stretch')

        st.subheader("📍 Annonces par ville (Top 10)")
        par_ville = resultats["ville"].dropna().value_counts().head(10)
        st.bar_chart(par_ville)

    with c2:
        st.subheader("🛣️ Prix vs Kilométrage")
        df_sc = resultats.dropna(subset=["kilometrage", "prix_mad"])
        if not df_sc.empty:
            st.scatter_chart(df_sc, x="kilometrage", y="prix_mad", color="marque")
        else:
            st.info("Pas assez de données prix/km.")

        st.subheader("📈 Prix médian par année")
        prix_annee = resultats.dropna(subset=["annee"]).groupby("annee")["prix_mad"].median().sort_index()
        st.line_chart(prix_annee)

        st.subheader("📊 Distribution des prix")
        try:
            bins = pd.cut(resultats["prix_mad"], bins=10)
            hist = resultats.groupby(bins, observed=True).size()
            hist.index = hist.index.astype(str)
            st.bar_chart(hist)
        except Exception:
            st.info("Distribution indisponible.")

        st.subheader("🏆 Top 5 scores")
        top5 = resultats.nlargest(5, "score")[["marque", "modele", "score"]].copy()
        top5["voiture"] = top5["marque"] + " " + top5["modele"]
        st.bar_chart(top5.set_index("voiture")["score"])

    st.divider()
    st.subheader("🧾 Données filtrées")
    st.dataframe(
        resultats[["id", "marque", "modele", "annee", "prix_mad",
                   "kilometrage", "carburant", "boite_vitesses", "ville", "score", "badge"]],
        width='stretch',
    )

with onglet_comp:
    st.header("⚖️ Comparer plusieurs voitures")
    choix = st.multiselect(
        "Sélectionnez 2 ou 3 voitures",
        resultats.apply(
            lambda r: f"#{int(r['id'])} — {r['marque']} {r['modele']} "
                      f"({int(r['annee']) if pd.notna(r['annee']) else '?'})", axis=1
        ).tolist(),
    )
    if len(choix) > 3:
        st.warning("3 voitures maximum.")
        choix = choix[:3]
    if len(choix) >= 2:
        ids = [int(x.split(" — ")[0].replace("#", "")) for x in choix]
        comp = resultats[resultats["id"].isin(ids)][
            ["marque", "modele", "annee", "prix_mad", "kilometrage",
             "carburant", "boite_vitesses", "ville", "score"]
        ].rename(columns={
            "marque": "Marque", "modele": "Modèle", "annee": "Année",
            "prix_mad": "Prix (MAD)", "kilometrage": "Km",
            "carburant": "Carburant", "boite_vitesses": "Boîte",
            "ville": "Ville", "score": "Score /100",
        })
        st.dataframe(
            comp.set_index([[f"Voiture {i+1}" for i in range(len(comp))]]),
            width='stretch',
        )
        # Graphique comparatif des prix
        st.subheader("💰 Comparaison visuelle des prix")
        comp_prix = resultats[resultats["id"].isin(ids)].copy()
        comp_prix["label"] = comp_prix["marque"] + " " + comp_prix["modele"]
        st.bar_chart(comp_prix.set_index("label")["prix_mad"])
    elif choix:
        st.info("Sélectionnez au moins 2 voitures.")

    st.divider()
    csv_resultats = resultats.drop(columns=["options_liste", "texte_global"]).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger les résultats (CSV)", csv_resultats,
                       "resultats_carmatch.csv", "text/csv")

st.caption("CarMatch AI — Démo pédagogique. Annonces par défaut fictives. Vérifiez toujours une annonce réelle avant paiement ou déplacement.")
