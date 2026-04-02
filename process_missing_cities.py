import os
import subprocess
import sys
import osmnx as ox
import pandas as pd

# Update sys.path to import analyze_city_structure
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import analyze_city_structure as analyzer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NET_DIR = os.path.join(BASE_DIR, "data", "networks")
MASTER_CSV = os.path.join(BASE_DIR, "data", "spectral_features_master.csv")

MISSING_CITIES = {
    "amsterdam": (52.3702, 4.8952),
    "buenos_aires": (-34.6037, -58.3816),
    "cairo": (30.0444, 31.2357),
    "dubai": (25.2048, 55.2708)
}

def process_missing_city(city_key, center_point):
    print(f"\n--- Traitement de {city_key.upper()} ---")
    
    net_file = os.path.join(NET_DIR, f"{city_key}.net.xml")
    osm_file = os.path.join(NET_DIR, f"{city_key}.osm.xml")
    
    # 1. Download Graph using a radius to prevent OOM
    if not os.path.exists(net_file):
        try:
            print(f"  Téléchargement OSM pour {city_key} (rayon 3000m)...")
            G = ox.graph_from_point(center_point, dist=3000, network_type='drive', simplify=False)
            ox.save_graph_xml(G, filepath=osm_file)
            print(f"  Graphe OSM sauvegardé.")
            
            print(f"  Conversion vers SUMO (.net.xml)...")
            cmd = [
                "netconvert",
                "--osm-files", osm_file,
                "-o", net_file,
                "--geometry.remove", "true",
                "--roundabouts.guess", "true",
                "--ramps.guess", "true",
                "--junctions.join", "true",
                "--tls.guess", "true",
                "--tls.discard-simple", "true",
                "--tls.join", "true",
                "--no-turnarounds", "true"
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            os.remove(osm_file)
            print(f"  Réseau SUMO généré: {net_file}")
            
        except Exception as e:
            print(f"  ERREUR lors de la génération du réseau pour {city_key}: {e}")
            return
    else:
        print(f"  Réseau {net_file} déjà existant.")
        
    # 2. Extract Spectral Features
    print(f"  Analyse spectrale en cours pour {city_key}...")
    metrics = analyzer.analyze_topology(net_file)
    if not metrics:
        print(f"  Échec de l'analyse spectrale pour {city_key}.")
        return
        
    # 3. Save to master features
    # Format matches save_to_master_csv in analyze_city_structure.py
    print(f"  Sauvegarde des caractéristiques spectrales...")
    row_data = {
        "city": city_key,
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
    if not os.path.exists(MASTER_CSV):
        df.to_csv(MASTER_CSV, index=False)
    else:
        df.to_csv(MASTER_CSV, mode='a', header=False, index=False)
        
    # Enregistrer le rapport
    analyzer.generate_report(city_key, city_key, metrics)
    print(f"  {city_key.upper()} terminé avec succès !")

if __name__ == "__main__":
    import traceback
    for city, coords in MISSING_CITIES.items():
        try:
            process_missing_city(city, coords)
        except Exception as e:
            print(f"Erreur inattendue pour {city}: {e}")
            traceback.print_exc()
