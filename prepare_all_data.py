import os
import glob
import re
import pandas as pd

# Paths
sim_dir = 'data/simulations'
dataset_file = 'data/dataset.csv'
master_features_file = 'data/spectral_features_master.csv'
output_file = 'data/dataset_complet.csv'

print("--- LECTURE DES FEATURES EXISTANTES ---")
city_features = {}

# On charge le dataset initial qui contient les features pour 5 villes
if os.path.exists(dataset_file):
    df_existing = pd.read_csv(dataset_file)
    for _, row in df_existing.iterrows():
        city_features[row['city'].lower()] = row.to_dict()

# On charge aussi le master features pour récupérer Versailles etc.
if os.path.exists(master_features_file):
    df_master = pd.read_csv(master_features_file)
    for _, row in df_master.iterrows():
        c = row['city'].lower()
        if c not in city_features:
            nodes = row['nodes']
            city_features[c] = {
                'city': c,
                'n_nodes': nodes,
                'n_edges': row['edges'],
                'density': row['edges'] / (nodes * (nodes - 1)) if nodes > 1 else 0,
                'spectral_radius': row['rho'],
                'kreiss_constant': row['kreiss']
            }

all_data = []

print("\n--- EXTRACTION DES DONNÉES DE SIMULATION ---")
sim_files = glob.glob(os.path.join(sim_dir, "*.csv"))
for count, file in enumerate(sim_files):
    filename = os.path.basename(file)
    print(f"[{count+1}/{len(sim_files)}] Traitement de {filename}...")
    
    # regex pour parser, e.g. amsterdam5k_2026...csv ou Paris10K...
    match = re.match(r'^([a-zA-Z_-]+)(\d+)[kK]_.*\.csv$', filename)
    if not match:
        print(f"Impossible d'extraire le nom et le % de véhicules depuis {filename}")
        continue
    
    city = match.group(1).lower().replace('-', '_')
    vehicles = int(match.group(2)) * 1000
    
    # On vérifie si on a les features pour cette ville
    # Note : los_angeles dans filename (los-angeles) -> los_angeles
    if city not in city_features:
        print(f"ATTENTION: Caractéristiques spectrales indisponibles pour {city}.")
        
    try:
        # Lire uniquement CO2_g_s et speed pour économiser la RAM (certains fichiers font > 3Go !)
        # On utilise on_bad_lines='skip' car SUMO peut parfois générer des lignes corrompues
        df_sim = pd.read_csv(file, usecols=['CO2_g_s', 'speed'], on_bad_lines='skip')
        
        # Pour forcer les colonnes en numérique (au cas où il y ait des headers dans le fichier CSV ou des erreurs)
        df_sim['CO2_g_s'] = pd.to_numeric(df_sim['CO2_g_s'], errors='coerce').fillna(0)
        df_sim['speed'] = pd.to_numeric(df_sim['speed'], errors='coerce').fillna(0)
        
        total_co2_kg = df_sim['CO2_g_s'].sum() / 1000.0
        avg_speed_mps = df_sim['speed'].mean()
        
        row = {
            'city': city,
            'simulation_file': filename,
            'total_vehicles': vehicles,
            'total_co2_kg': total_co2_kg,
            'avg_speed_mps': avg_speed_mps,
        }
        
        # Ajout des features
        if city in city_features:
            for k in ['n_nodes', 'n_edges', 'density', 'spectral_radius', 'kreiss_constant']:
                row[k] = city_features[city].get(k, None)
        else:
            for k in ['n_nodes', 'n_edges', 'density', 'spectral_radius', 'kreiss_constant']:
                row[k] = None
                
        all_data.append(row)
        print(f" -> {city.capitalize()} traité : {total_co2_kg:.2f} kg CO2 | Vitesse Moy: {avg_speed_mps:.2f} m/s")
    except Exception as e:
        print(f"Erreur avec {filename}: {e}")

df_all = pd.DataFrame(all_data)
df_all.to_csv(output_file, index=False)
print(f"\n--- TERMINÉ ---")
print(f"Données consolidées enregistrées dans {output_file}")
print("Nombre de lignes :", len(df_all))
