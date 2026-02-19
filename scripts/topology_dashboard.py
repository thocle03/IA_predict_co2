import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import glob
import json
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium
import pydeck as pdk

# Add scripts to path to import analyzer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    import analyze_city_structure as analyzer
except ImportError:
    st.error("Module 'analyze_city_structure' not found.")

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Urban Topology Research Lab",
    page_icon="city",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    h1, h2, h3, h4 { color: #f0f2f6; font-family: 'Inter', sans-serif; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 8px; border-left: 5px solid #FFD700; }
    .stAlert { border-radius: 8px; }
    .academic-card { background-color: #1e2130; padding: 20px; border-radius: 10px; border: 1px solid #3d4455; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'analysis_results' not in st.session_state: st.session_state.analysis_results = None
if 'current_city' not in st.session_state: st.session_state.current_city = None
if 'show_home' not in st.session_state: st.session_state.show_home = True
if 'city_results' not in st.session_state: st.session_state.city_results = []

# --- HEADER ---
st.title("Urban Topology Research Lab")
st.markdown("### *Spectral & Dynamic Stability Platform*")
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Configuration")
    city_input = st.text_input("Ville à analyser", value="Monaco")
    
    # NEW: Verification Step
    if st.button("Vérifier la ville", use_container_width=True):
        with st.spinner("Recherche..."):
            st.session_state.city_results = analyzer.search_potential_cities(city_input)
    
    final_city_query = None
    if st.session_state.city_results:
        city_options = [f"{c['display_name']} (CP: {c['postcode']})" for c in st.session_state.city_results]
        selected_option = st.selectbox("Sélectionnez l'emplacement exact", city_options)
        # Map back to full display name
        idx = city_options.index(selected_option)
        final_city_query = st.session_state.city_results[idx]['display_name']
        st.success(f"Ville prête : {st.session_state.city_results[idx]['city']}")
    
    view_mode = st.radio("Mode de Visualisation", ["2D (Analytique)", "3D (Perspective)"])
    run_btn = st.button("Lancer l'Analyse Spectrale", use_container_width=True, disabled=(final_city_query is None))
    
    if st.button("Retour à l'accueil", use_container_width=True):
        st.session_state.analysis_results = None; st.session_state.show_home = True; st.rerun()

    st.markdown("---")
    st.header(" Archives / Historique")
    report_files = glob.glob(os.path.join(analyzer.REPORT_DIR, "REPORT_*.md"))
    report_files.sort(key=os.path.getmtime, reverse=True)
    selected_report = st.selectbox("Charger un rapport", ["-- Sélectionner --"] + [os.path.basename(f) for f in report_files])

# --- VISUALIZATION HELPERS ---

def plot_eigenvalues(evals):
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    
    # Unit circle
    circle = plt.Circle((0, 0), 1, color='#3d4455', fill=False, linestyle='--', alpha=0.5)
    ax.add_artist(circle)
    
    real_parts = [e['real'] if isinstance(e, dict) else np.real(e) for e in evals]
    imag_parts = [e['imag'] if isinstance(e, dict) else np.imag(e) for e in evals]
    
    ax.scatter(real_parts, imag_parts, color='#ff4b4b', alpha=0.8, edgecolors='white', s=40)
    ax.set_title("Spectre (Plan Complexe)", color='white', fontsize=10)
    ax.axhline(0, color='white', linewidth=0.5, alpha=0.3)
    ax.axvline(0, color='white', linewidth=0.5, alpha=0.3)
    ax.tick_params(colors='white', labelsize=8)
    for spine in ax.spines.values(): spine.set_color('#3d4455')
    return fig

def plot_svd_scree(s_vals):
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    ax.plot(range(1, len(s_vals) + 1), s_vals, 'o-', color='#4da6ff', linewidth=1.5, markersize=5)
    ax.set_title("Valeurs Singulières (Scree Plot)", color='white', fontsize=10)
    ax.set_xlabel("Indice k", color='white', fontsize=8)
    ax.set_ylabel("Valeur σ_k", color='white', fontsize=8)
    ax.grid(True, alpha=0.1, color='white')
    ax.tick_params(colors='white', labelsize=8)
    for spine in ax.spines.values(): spine.set_color('#3d4455')
    return fig

def plot_singular_vectors(u1, v1):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 3))
    fig.patch.set_facecolor('#0e1117')
    for ax, data, title, color in zip([ax1, ax2], [u1, v1], ["Influence (u1)", "Source (v1)"], ["#ff4b4b", "#4da6ff"]):
        ax.set_facecolor('#0e1117')
        ax.hist(data, bins=30, color=color, alpha=0.6)
        ax.set_title(title, color='white', fontsize=9)
        ax.tick_params(colors='white', labelsize=7)
        for spine in ax.spines.values(): spine.set_color('#3d4455')
    plt.tight_layout()
    return fig

def display_map_3d(city_name, highlight_edge=None, center=None, zoom=14, show_spectral=False):
    """3D Map with bulletproof coordinate handling"""
    try:
        import osmnx as ox
        
        def to_float(v):
            try:
                f = float(v)
                return f if np.isfinite(f) else None
            except: return None

        # 1. Robust Centering
        final_lat, final_lon = 0.0, 0.0
        center_valid = False
        
        if center and len(center) >= 2:
            lat, lon = to_float(center[0]), to_float(center[1])
            if lat is not None and lon is not None:
                final_lat, final_lon = lat, lon
                center_valid = True
        
        # 2. Get Background Network
        try:
            G = ox.graph_from_place(city_name, network_type='drive', simplify=True)
            gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
            
            # Fallback center if needed
            if not center_valid and not gdf_nodes.empty:
                avg_lat, avg_lon = to_float(gdf_nodes.y.mean()), to_float(gdf_nodes.x.mean())
                if avg_lat is not None and avg_lon is not None:
                    final_lat, final_lon = avg_lat, avg_lon
        except:
            gdf_edges = pd.DataFrame()

        # 3. Build Layers
        layers = []
        if not gdf_edges.empty:
            layers.append(pdk.Layer("PathLayer", gdf_edges, get_path="geometry.coordinates", get_width=2, get_color=[255, 120, 0, 150], pickable=True))
        
        if show_spectral and highlight_edge and 'coords' in highlight_edge:
            raw_path = highlight_edge['coords']
            valid_path = []
            for i, c in enumerate(raw_path):
                if len(c) >= 2:
                    lat, lon = to_float(c[0]), to_float(c[1])
                    if lat is not None and lon is not None:
                        valid_path.append([lon, lat])
            
            if len(valid_path) >= 2:
                layers.append(pdk.Layer(
                    "PathLayer",
                    [{"path": valid_path, "name": f"CRITIQUE: {highlight_edge['name']}"}],
                    get_path="path", get_width=15, get_color=[255, 215, 0, 255], pickable=True
                ))
                
                lats = [p[1] for p in valid_path]
                lons = [p[0] for p in valid_path]
                cp_lat, cp_lon = float(np.mean(lats)), float(np.mean(lons))
                
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    pd.DataFrame([{"lon": cp_lon, "lat": cp_lat}]),
                    get_position=["lon", "lat"], get_fill_color=[255, 215, 0, 200], get_radius=25, pickable=True
                ))

        # 4. Final View State Check
        if not np.isfinite(final_lat) or not np.isfinite(final_lon):
             final_lat, final_lon = 0.0, 0.0

        st.pydeck_chart(pdk.Deck(
            layers=layers, 
            initial_view_state=pdk.ViewState(latitude=final_lat, longitude=final_lon, zoom=zoom, pitch=45, bearing=0),
            map_style="mapbox://styles/mapbox/dark-v9", 
            tooltip={"text": "{name}"}
        ))
            
    except Exception as e: 
        st.error(f"Erreur 3D Critique: {e}")

# --- MAIN LOGIC ---

if run_btn and final_city_query:
    st.session_state.show_home = False
    st.session_state.current_city = final_city_query
    with st.status("Calculs spectraux en cours...") as status:
        net_file, safe_name = analyzer.download_city_map(final_city_query)
        metrics = analyzer.analyze_topology(net_file)
        if metrics:
            report_path = analyzer.generate_report(city_input, safe_name, metrics)
            with open(report_path, "r", encoding="utf-8") as f: report_content = f.read()
            st.session_state.analysis_results = {"metrics": metrics, "report": report_content, "net_file": net_file}
            status.update(label="Analyse terminée", state="complete")

if selected_report and selected_report != "-- Sélectionner --":
    st.session_state.show_home = False
    safe_id = selected_report.replace("REPORT_", "").replace(".md", "")
    meta_path = os.path.join(analyzer.REPORT_DIR, f"META_{safe_id}.json")
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f: m_data = json.load(f)
        with open(os.path.join(analyzer.REPORT_DIR, selected_report), "r", encoding="utf-8") as f: r_content = f.read()
        st.session_state.analysis_results = {"metrics": m_data, "report": r_content}
        st.session_state.current_city = safe_id.replace("_", " ").title()
    else:
        st.warning("Métadonnées non trouvées. Chargement du texte seul.")
        with open(os.path.join(analyzer.REPORT_DIR, selected_report), "r", encoding="utf-8") as f: st.markdown(f.read())

# --- DASHBOARD DISPLAY ---

if st.session_state.analysis_results and not st.session_state.show_home:
    res = st.session_state.analysis_results
    m = res['metrics']
    city = st.session_state.current_city
    cs = m.get('critical_street')

    # Row 1: KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Rayon Spectral ρ", f"{m['spectral_radius']:.4f}")
    c2.metric("Gain Système σₘₐₓ", f"{m['h_inf_norm']:.4f}")
    c3.metric("Indice de Kreiss", f"{m['kreiss_constant']:.2f}")
    c4.metric("Norme H₂", f"{m['h2_norm']:.2f}")
    if cs: c5.metric("Rue Critique", cs['name'][:15], delta="BOTTLE_NECK")

    st.markdown("---")

    # Row 2: Observation (Interface intacte, juste clean)
    st.subheader(f"Observation Globale : {city}")
    if view_mode == "2D (Analytique)":
        st_folium(analyzer.generate_interactive_map(city), width="100%", height=500, key=f"main_map_2d_{city}")
    else:
        display_map_3d(city, show_spectral=False)
    
    st.markdown("---")

    # Row 3: All Visualizations (Spectrum, Scree, Vectors)
    st.markdown("#### Laboratoire Spectral")
    lab_container = st.container()
    with lab_container:
        v1, v2, v3 = st.columns([1, 1, 2])
        try:
            with v1: 
                fig1 = plot_eigenvalues(m['eigenvalues'])
                if fig1: st.pyplot(fig1)
                else: st.warning("Visualisation du spectre indisponible.")
            with v2:
                fig2 = plot_svd_scree(m['singular_values'])
                if fig2: st.pyplot(fig2)
                else: st.warning("Visualisation SVD indisponible.")
            with v3:
                fig3 = plot_singular_vectors(m['u1'], m['v1'])
                if fig3: st.pyplot(fig3)
                else: st.warning("Visualisation des vecteurs indisponible.")
        except Exception as e:
            st.error(f"⚠️ Le Laboratoire Spectral rencontre des difficultés de rendu sur ce jeu de données volumineux. Les calculs sont complexes mais l'analyse peut se poursuivre ci-dessous.")
            st.info("💡 Conseil : Consultez le rapport complet en bas de page pour les valeurs numériques.")

    st.markdown("---")
    
    # NEW: DEDICATED SECTION FOR CRITICAL AREA
    st.markdown("### 🎯 Analyse du Secteur Critique (Pivot de Perron-Frobenius)")
    
    col_critical_map, col_critical_info = st.columns([2, 1])
    
    with col_critical_map:
        focus_center, focus_zoom = None, 14
        
        # Robust focus center calc for the critical street ONLY
        if cs and 'coords' in cs:
            coords = cs['coords']
            if coords:
                # Filter out garbage coords (NaN, Inf, or empty)
                valid_coords = [c for c in coords if len(c) >= 2 and np.isfinite(c[0]) and np.isfinite(c[1])]
                if valid_coords:
                    lats = [float(c[0]) for c in valid_coords]
                    lons = [float(c[1]) for c in valid_coords]
                    focus_center = [sum(lats)/len(lats), sum(lons)/len(lons)]
                    focus_zoom = 19 if cs.get('length', 0) < 15 else 17
            
        if view_mode == "2D (Analytique)":
            m_focus = analyzer.generate_interactive_map(city, center=focus_center, zoom=focus_zoom)
            if cs and 'coords' in cs:
                folium.PolyLine(cs['coords'], color='#FFD700', weight=12, opacity=0.9).add_to(m_focus)
                folium.CircleMarker(cs['coords'][0], radius=15, color='#FFD700', fill=True).add_to(m_focus)
            st_folium(m_focus, width="100%", height=500, key=f"focus_map_2d_{city}")
        else:
            display_map_3d(city, highlight_edge=cs, center=focus_center, zoom=focus_zoom, show_spectral=True)

    with col_critical_info:
        st.markdown("#### Données du Secteur")
        if cs:
            st.warning(f"**Goulot Spectral : {cs['name']}**")
            st.markdown(f"- Importance: {cs['importance']:.6f}\n- ID SUMO: `{cs['id']}`")
        
        st.divider()
        st.markdown("#### Statut de Stabilité")
        st.info(f"""
        - Instabilité : { "🔴 Critique" if m['kreiss_constant'] > 10 else "🟢 Modérée" }
        - Robustesse : { "🔴 Faible" if abs(m['h_inf_norm'] - m['spectral_radius']) < 0.1 else "🟢 Élevée" }
        """)

    st.markdown("---")
    with st.expander("Consulter le Rapport Scientifique Complet"):
        st.markdown(res['report'])

elif st.session_state.show_home:
    st.markdown("## Plateforme d'Analyse de la Topologie Urbaine et de la Stabilité des Réseaux")
    st.markdown("Cette interface est dédiée à l'étude structurelle des réseaux routiers urbains.")
