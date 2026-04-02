import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import time
import subprocess
import joblib
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Configuration de la page stricte et scientifique
st.set_page_config(page_title="IA Pollution - Modélisation des Émissions", layout="wide")

# Masquer le bouton de déploiement, le menu (les 3 points) et le header de Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
.stAppDeployButton {display:none;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Chemins absolus
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'xgb_co2_predictor.joblib')
MASTER_FEATURES = os.path.join(BASE_DIR, 'data', 'spectral_features_master.csv')
NET_DIR = os.path.join(BASE_DIR, "data", "networks")

# Import du module local d'analyse spectrale
sys.path.append(os.path.join(BASE_DIR, "scripts"))
try:
    import analyze_city_structure as analyzer
    import osmnx as ox
    MODULES_OK = True
except ImportError:
    MODULES_OK = False


# Fonction pour chercher les vraies villes
@st.cache_data(show_spinner=False)
def search_city(query):
    if not query:
        return []
    try:
        geolocator = Nominatim(user_agent="academic_pollution_research")
        locations = geolocator.geocode(query, exactly_one=False, featuretype='city', limit=5)
        if locations:
            # Nettoyage pour n'afficher que le nom principal et le pays
            results = []
            for loc in locations:
                address = loc.address
                parts = address.split(', ')
                # Construction d'un nom affichable "Ville, Pays"
                name = f"{parts[0]}, {parts[-1]}"
                # Formater le nom pour la base CSV (ex: "Paris, France" -> "paris")
                raw_name = parts[0].lower().replace(' ', '_').replace('-', '_')
                results.append({
                    "display": name, 
                    "raw": raw_name,
                    "lat": loc.latitude,
                    "lon": loc.longitude
                })
            return results
        return []
    except GeocoderTimedOut:
        return []

# Fonctions de chargement
@st.cache_data
def load_data():
    if os.path.exists(MASTER_FEATURES):
        df = pd.read_csv(MASTER_FEATURES)
        df['city'] = df['city'].astype(str).str.lower().str.replace('-', '_')
        df = df.drop_duplicates(subset=['city'], keep='last')
        # Recalcul des colonnes
        df['nodes'] = df['nodes'].astype(float)
        df['edges'] = df['edges'].astype(float)
        df['densite'] = df['edges'] / (0.5 * df['nodes'] * (df['nodes'] - 1))
        df['deg_moyen'] = (2.0 * df['edges']) / df['nodes']
        return df
    return pd.DataFrame()

@st.cache_resource
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None, None

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Modules :", ["Présentation du Projet", "Prédiction par Intelligence Artificielle"])

st.sidebar.markdown("---")
st.sidebar.info("By Thomas Clerc")

if page == "Présentation du Projet":
    st.title("Modélisation Topologique et Prédiction des Émissions de CO2")
    
    st.markdown("### 1. Contexte Académique")
    st.write(
        "Ce projet est dans le cadre d'un mémoire de fin d'étude pour l'école Hexagone en 2026, dont le but est de pouvoir prédire les émission de Co2 de n'importe quelle ville. "
        
    )
    
    st.markdown("### 2. Architecture Technique")
    st.write(
        "L'architecture repose sur une agrégation stricte des données pour éviter les biais microscopiques :"
    )
    st.markdown("""
    * **Simulation du trafic (SUMO) :** Calcul seconde par seconde des mouvements de chaque véhicule (accélération, freinage).
    * **Regroupement des données :** Transformation de ces millions d'informations individuelles en résultats globaux pour toute la ville.
    * **Modèle Algorithmique (XGBoost Régresseur) :** Apprentissage non linéaire basé sur des arbres de décision. Il détecte les seuils de basculement critiques liés aux variables purement topologiques (Densité, Constante de Kreiss, Valeurs propres).
    """)

    st.markdown("### 3. Raisonnement Méthodologique")
    st.write(
        "Au lieu de traiter la similarité entre infrastructures routières par des modèles de distance lissée (K-Nearest Neighbors), "
        "qui noieraient l'effet papillon inhérent au comportement du trafic, le modèle ingère des métriques structurelles brutes. "
        "Ceci garantit l'explicabilité de la 'Feature Importance', permettant d'isoler mathématiquement le poids d'un goulot d'étranglement ou de la connexité globale dans la genèse de la congestion."
    )

elif page == "Prédiction par Intelligence Artificielle":
    st.title("Module de Simulation et Prédiction")
    
    # Chargement des données
    feat_df = load_data()
    model, features_list = load_model()
    
    st.markdown("### Configuration du Réseau et de la Charge")
    
    # Étape 1 : Recherche de la ville
    query = st.text_input("Rechercher une infrastructure urbaine (Ville) :", placeholder="ex: Versailles")
    
    if query:
        results = search_city(query)
        if results:
            options = {r['display']: r for r in results}
            selected_display = st.selectbox("Valider la localisation certifiée :", list(options.keys()))
            selected_city_data = options[selected_display]
            selected_raw = selected_city_data['raw']
            selected_lat = selected_city_data['lat']
            selected_lon = selected_city_data['lon']
        else:
            st.warning("Localisation non trouvée dans les registres géographiques.")
            selected_raw = None
    else:
        selected_raw = None

    # Étape 2 : Paramètres de Trafic
    st.markdown("#### Paramètres de Flux Cinématique")
    col1, col2 = st.columns(2)
    with col1:
        duree = st.number_input("Durée de projection (secondes)", min_value=1, value=3600)
        voitures = st.number_input("Volume : Véhicules Légers (Voitures)", min_value=0, value=10000)
        motos = st.number_input("Volume : Deux Roues (Motos)", min_value=0, value=5000)
    with col2:
        total_veh_display = st.empty()
        camions = st.number_input("Volume : Poids Lourds (Camions)", min_value=0, value=2500)
        bus = st.number_input("Volume : Transport en Commun (Bus)", min_value=0, value=2500)
        
    total_veh = voitures + camions + bus + motos
    st.info(f"Simulation pour {duree} secondes et {total_veh} vehicules")

    # Étape 3 : Exécution
    if st.button("Lancer l'Algorithme de Prédiction", type="primary"):
        if not selected_raw:
            st.error("Veuillez sélectionner une ville valide.")
        elif model is None:
            st.error("L'algorithme XGBoost n'est pas compilé. Exécutez le script d'entraînement.")
        else:
            # Vérifier si la ville existe dans la base spectrale
            city_data = feat_df[feat_df['city'] == selected_raw]
            
            if city_data.empty:
                st.warning(f"L'infrastructure '{selected_raw}' est absente de la matrice pré-calculée. Lancement de la procédure d'extraction physique en direct.")
                
                if not MODULES_OK:
                    st.error("Les modules avancés (OSMnx ou le script local d'analyse) sont introuvables. Mode extraction indisponible.")
                else:
                    success = False
                    with st.status("Génération Topologique en Temps Réel...", expanded=True) as status:
                        try:
                            net_file = os.path.join(NET_DIR, f"{selected_raw}.net.xml")
                            osm_file = os.path.join(NET_DIR, f"{selected_raw}.osm.xml")
                            
                            st.write(f"[1/4] Téléchargement du réseau routier ({selected_lat:.4f}, {selected_lon:.4f}) via OSM...")
                            os.makedirs(NET_DIR, exist_ok=True)
                            
                            if not os.path.exists(net_file):
                                G = ox.graph_from_point((selected_lat, selected_lon), dist=3000, network_type='drive', simplify=False)
                                ox.save_graph_xml(G, filepath=osm_file)
                                
                                st.write(f"[2/4] Conversion du graphe en matrice SUMO (netconvert)...")
                                cmd = [
                                    "netconvert", "--osm-files", osm_file, "-o", net_file,
                                    "--geometry.remove", "true", "--roundabouts.guess", "true",
                                    "--ramps.guess", "true", "--junctions.join", "true",
                                    "--tls.guess", "true", "--tls.discard-simple", "true",
                                    "--tls.join", "true", "--no-turnarounds", "true"
                                ]
                                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                                if os.path.exists(osm_file):
                                    os.remove(osm_file)
                            else:
                                st.write(f"[2/4] Le réseau binaire existe déjà localement ")
                                
                            st.write(f"[3/4] Extraction des matrices d'adjacence et calculs spectraux lourds (Kreiss, Valeurs Propres)...")
                            metrics = analyzer.analyze_topology(net_file)
                            
                            if metrics:
                                st.write(f"[4/4] Sauvegarde des caractéristiques de la ville dans la base de données de l'IA...")
                                row_data = {
                                    "city": selected_raw, "nodes": metrics['node_count'], "edges": metrics['edge_count'],
                                    "rho": metrics['spectral_radius'], "sigma_max": metrics['h_inf_norm'],
                                    "h2_norm": metrics['h2_norm'], "kreiss": metrics['kreiss_constant'],
                                    "avg_degree": metrics['avg_degree'],
                                    "critical_street_id": metrics['critical_street']['id'] if metrics.get('critical_street') else "N/A"
                                }
                                df_new_city = pd.DataFrame([row_data])
                                if not os.path.exists(MASTER_FEATURES):
                                    df_new_city.to_csv(MASTER_FEATURES, index=False)
                                else:
                                    df_new_city.to_csv(MASTER_FEATURES, mode='a', header=False, index=False)
                                
                                # Forcer le rechargement du DataFrame en mémoire pour récupérer ces nouvelles données
                                load_data.clear()
                                feat_df = load_data()
                                city_data = feat_df[feat_df['city'] == selected_raw]
                                
                                status.update(label="Topologie mathématique acquise et validée !", state="complete", expanded=False)
                                success = True
                            else:
                                status.update(label="Échec mathématique lors de l'extraction", state="error")
                        except Exception as e:
                            status.update(label=f"Erreur d'infrastructure : {e}", state="error")
                    
                    if not success:
                        st.stop()
            
            if not city_data.empty:
                # La ville existe (ou vient d'être générée avec succès), on procède à la prédiction
                st.success(f"Paramètres topologiques de {selected_display} chargés avec intégrité.")
                
                donnees_test = {
                    'nodes': city_data['nodes'].values[0],
                    'edges': city_data['edges'].values[0],
                    'densite': city_data['densite'].values[0],
                    'deg_moyen': city_data['deg_moyen'].values[0],
                    'rho': city_data['rho'].values[0],
                    'kreiss': city_data['kreiss'].values[0],
                    'duree_sim_s': duree,
                    'nb_total_veh': total_veh,
                    'nb_voitures': voitures,
                    'nb_camions': camions,
                    'nb_bus': bus,
                    'nb_motos': motos
                }
                
                df_new = pd.DataFrame([donnees_test], columns=features_list)
                
                with st.spinner("Exécution des arbres de régression..."):
                    time.sleep(1) # Petit effet pour montrer que ça calcule
                    prediction = model.predict(df_new)[0]
                
                st.markdown("---")
                st.subheader("Bilan Macro-Environnemental")
                st.metric(label="Émissions Quantifiées Totalisées", value=f"{prediction:,.1f} Kg CO₂")
                
                st.caption(f"Note technique : Projection calculée sur une topologie de {int(city_data['nodes'].values[0])} nœuds avec une constante d'étouffement (Kreiss) de {city_data['kreiss'].values[0]:.2f}.")
