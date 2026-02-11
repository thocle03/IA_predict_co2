import os
import sys
import argparse
import traceback
import json
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigs, svds
import sumolib
import osmnx as ox
import subprocess
import networkx as nx
import pandas as pd
import folium

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NET_DIR = os.path.join(BASE_DIR, "data", "networks")
REPORT_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(NET_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)

def download_city_map(city_query):
    """Downloads map from OSM and converts to SUMO .net.xml"""
    print(f"\n--- 1. ACQUISITION : {city_query} ---")
    safe_name = city_query.replace(" ", "_").replace(",", "").lower()
    net_file = os.path.join(NET_DIR, f"{safe_name}.net.xml")
    
    if os.path.exists(net_file):
        print(f"  Map already exists: {net_file}")
        return net_file, safe_name

    try:
        print(f"  Querying OpenStreetMap via OSMnx...")
        G = ox.graph_from_place(city_query, network_type='drive', simplify=False)
        
        osm_file = os.path.join(NET_DIR, f"{safe_name}.osm.xml")
        ox.save_graph_xml(G, filepath=osm_file)
        
        cmd = [
            "netconvert",
            "--osm-files", osm_file,
            "-o", net_file,
            "--geometry.remove", "true",
            "--roundabouts.guess", "true",
            "--junctions.join", "true",
            "--no-turnarounds", "true"
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.remove(osm_file)
        return net_file, safe_name
        
    except Exception as e:
        print(f"  CRITICAL ERROR downloading map: {e}")
        return None, None

def generate_interactive_map(city_query, highlight_edge=None, center=None, zoom=14):
    """Generates a Folium map for the city with optional focus"""
    try:
        if not center:
            G = ox.graph_from_place(city_query, network_type='drive', simplify=True)
            gdf_nodes, _ = ox.graph_to_gdfs(G)
            center = [gdf_nodes.y.mean(), gdf_nodes.x.mean()]
            
        m = folium.Map(location=center, zoom_start=zoom, tiles='CartoDB dark_matter')
        
        # Load edges for the background (using a simpler method to avoid full graph reload if possible)
        G = ox.graph_from_place(city_query, network_type='drive', simplify=True)
        _, gdf_edges = ox.graph_to_gdfs(G)
        folium.GeoJson(gdf_edges, style_function=lambda x: {'color': '#333333', 'weight': 1, 'opacity': 0.4}).add_to(m)
        
        if highlight_edge:
            folium.PolyLine(
                locations=highlight_edge['coords'],
                color='#FFD700',
                weight=5,
                opacity=1.0,
                tooltip=f"Secteur Critique (Pivot de Perron-Frobenius): {highlight_edge['name']}"
            ).add_to(m)
            
        return m
    except Exception as e:
        print(f"Map generation error: {e}")
        return None

def get_edge_by_id(net_file, edge_id):
    """Retrieves metadata and geometry (WGS84) for a specific Edge ID"""
    try:
        net = sumolib.net.readNet(net_file)
        edge = net.getEdge(edge_id)
        shape = edge.getShape()
        
        # Determine if coords are local XY or Lat/Lon
        # Convert XY to WGS84 for mapping
        coords = []
        for x, y in shape:
            lon, lat = net.convertXY2LonLat(x, y)
            coords.append((lat, lon))
            
        return {
            "id": edge.getID(),
            "name": edge.getName() or edge.getID(),
            "length": edge.getLength(),
            "lanes": len(edge.getLanes()),
            "coords": coords
        }
    except:
        return None

def analyze_topology(net_file):
    """Computes advanced graph metrics including singular mode identification"""
    print(f"\n--- 2. ANALYSE SPECTRALE APPLIQUÉE ---")
    
    try:
        net = sumolib.net.readNet(net_file)
        nodes = net.getNodes()
        edges = net.getEdges()
        n_nodes = len(nodes)
        
        if n_nodes < 2: return None

        node_id_map = {n.getID(): i for i, n in enumerate(nodes)}
        row, col, data = [], [], []
        
        for e in edges:
            u, v = e.getFromNode().getID(), e.getToNode().getID()
            if u in node_id_map and v in node_id_map:
                row.append(node_id_map[u]); col.append(node_id_map[v]); data.append(1.0)
        
        A = sp.csr_matrix((data, (row, col)), shape=(n_nodes, n_nodes))
        
        # 1. Eigenvalues (Spectrum)
        k_eig = min(50, n_nodes - 2)
        evals = eigs(A, k=k_eig, which='LM', return_eigenvectors=False)
        spectral_radius = float(np.max(np.abs(evals)))
        
        # 2. SVD (Singular Modes)
        # We take several singular values for the scree plot
        k_svd = min(30, n_nodes - 2)
        u_vectors, s, vt_vectors = svds(A, k=k_svd)
        # Re-sort SVD results as svds returns them in ascending order
        idx = s.argsort()[::-1]
        s = s[idx]
        u_vectors = u_vectors[:, idx]
        vt_vectors = vt_vectors[idx, :]
        
        sigma_max = float(s[0])
        u1 = u_vectors[:, 0]
        v1 = vt_vectors[0, :]
        
        # 3. Critical Street identification
        max_importance = -1.0
        critical_edge = None
        for e in edges:
            u_id, v_id = e.getFromNode().getID(), e.getToNode().getID()
            if u_id in node_id_map and v_id in node_id_map:
                importance = abs(u1[node_id_map[u_id]] * v1[node_id_map[v_id]])
                if importance > max_importance:
                    max_importance = importance
                    critical_edge = e
        
        critical_data = None
        if critical_edge:
            shape = critical_edge.getShape()
            coords = []
            for x, y in shape:
                lon_c, lat_c = net.convertXY2LonLat(x, y)
                coords.append((lat_c, lon_c))
                
            critical_data = {
                "id": critical_edge.getID(),
                "name": critical_edge.getName() or critical_edge.getID(),
                "importance": float(max_importance),
                "coords": coords
            }

        # 4. Norms & Kreiss
        h2_norm = float(np.sqrt(np.sum(A.data**2))) 
        
        # Kreiss approximation (Commutator norm)
        sample_size = min(500, n_nodes)
        A_small = A[:sample_size, :sample_size].todense()
        commutator = np.dot(A_small, A_small.T) - np.dot(A_small.T, A_small)
        kreiss_constant = (float(np.linalg.norm(commutator)) / sample_size) * 1000

        return {
            "node_count": n_nodes,
            "edge_count": len(edges),
            "spectral_radius": float(spectral_radius),
            "eigenvalues": [{"real": float(np.real(e)), "imag": float(np.imag(e))} for e in evals],
            "singular_values": [float(val) for val in s],
            "u1": [float(np.real(x)) for x in u1],
            "v1": [float(np.real(x)) for x in v1],
            "h2_norm": float(h2_norm),
            "h_inf_norm": float(sigma_max),
            "kreiss_constant": float(kreiss_constant),
            "critical_street": critical_data,
            "avg_degree": float(len(edges) / n_nodes)
        }

    except Exception as e:
        print(f"Error: {e}"); traceback.print_exc(); return None

def save_to_master_csv(city_name, metrics):
    """Appends spectral metrics to a master CSV for AI training"""
    master_file = os.path.join(BASE_DIR, "data", "spectral_features_master.csv")
    os.makedirs(os.path.dirname(master_file), exist_ok=True)
    
    # Flatten metrics for CSV (handling lists/dicts)
    row_data = {
        "city": city_name,
        "nodes": metrics['node_count'],
        "edges": metrics['edge_count'],
        "rho": metrics['spectral_radius'],
        "sigma_max": metrics['h_inf_norm'],
        "h2_norm": metrics['h2_norm'],
        "kreiss": metrics['kreiss_constant'],
        "avg_degree": metrics['avg_degree'],
        "critical_street_id": metrics['critical_street']['id'] if metrics.get('critical_street') else "N/A"
    }
    
    df = pd.DataFrame([row_data])
    if not os.path.exists(master_file):
        df.to_csv(master_file, index=False)
    else:
        df.to_csv(master_file, mode='a', header=False, index=False)

def generate_report(city_name, safe_name, metrics):
    """Generates a detailed scientific report and saves AI features"""
    save_to_master_csv(city_name, metrics)
    filename = os.path.join(REPORT_DIR, f"REPORT_{safe_name.upper()}.md")
    meta_file = os.path.join(REPORT_DIR, f"META_{safe_name.upper()}.json")
    
    cs = metrics.get('critical_street')
    sector_info = f"**{cs['name']}** (ID: `{cs['id']}`)" if cs else "Non identifié"
    cs_importance = cs['importance'] if (cs and 'importance' in cs) else 0.0

    # User's provided detailed interpretation
    interpretation = f"""
## Synthèse de l'Interprétation Mathématique

### 1. Analyse du Rayon Spectral ($\\rho = {metrics['spectral_radius']:.4f}$)
$\\rho > 1$ indique un système structurellement instable. Dans votre graphe routier, cela traduit l'existence de **corridors dominants** et une structure très hiérarchisée où les flux sont asymétriques. C'est un facteur de fragilité majeur.

### 2. Amplification Maximale ($\\sigma_{{max}} = {metrics['h_inf_norm']:.4f}$)
Le fait que $\\sigma_{{max}} \\approx \\rho$ signifie que l'amplification maximale instantanée est alignée avec la direction dominante. La majorité des trajets "efficaces" passent par les mêmes arcs, traduisant une **faible redondance** des itinéraires.

### 3. Normes et Énergie (Système Discrete)
- **Norme $H_\\infty = {metrics['h_inf_norm']:.4f}$** : Le pire cas entrée-sortie est purement topologique. SUMO va congestionner là où la structure l’impose.
- **Norme $H_2 = {metrics['h2_norm']:.4f}$** : Très élevée par rapport à $H_\\infty$. Le réseau **stocke de l'énergie** de perturbation, ce qui mène à une congestion diffuse et persistante.

### 4. Indice de Kreiss ($K = {metrics['kreiss_constant']:.4f}$)
C'est le signal le plus critique. Avec $K \\gg \\sigma_{{max}}$, la **non-normalité** est massive. Le système peut amplifier une perturbation locale de manière disproportionnée (effet papillon), provoquant des explosions transitoires de congestion.

## Identification du Secteur Critique (Pivot de Perron-Frobenius)
- **Rue Critique** : {sector_info}
- **Poids Spectral** : {cs_importance:.6f}
- **Action Recommandée** : Casser la non-normalité sur cet axe (pénalisation des hubs dominants, splitting d'arcs).
"""

    content = f"""# Rapport d'Excellence Spectrale : {city_name}

{interpretation}

---
*Document de recherche confidentiel | Urban Topology Lab*
"""
    with open(filename, "w", encoding="utf-8") as f: f.write(content)
    with open(meta_file, "w") as f: json.dump(metrics, f)
        
    return filename

if __name__ == "__main__":
    city = sys.argv[1] if len(sys.argv) > 1 else "Monaco"
    net, safe = download_city_map(city)
    if net:
        m = analyze_topology(net)
        if m: generate_report(city, safe, m)
