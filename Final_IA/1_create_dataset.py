# Extraction Finale des Données pour le Modèle XGBoost
# Ce script lit toutes les simulations et les structures mathématiques (spectre), 
# calcule la densité du graphe, le degré moyen, extrait la durée de simulation 
# et les montants exacts de chaque type de véhicule pour préparer un Dataset parfait X/y.

import os
import glob
import pandas as pd
import numpy as np
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM_DIR = os.path.join(BASE_DIR, 'data', 'simulations')
MASTER_FEATURES = os.path.join(BASE_DIR, 'data', 'spectral_features_master.csv')
OUTPUT_DATASET = os.path.join(BASE_DIR, 'data', 'xgboost_training_data.csv')

def process_simulations():
    print("--- 1. CHARGEMENT DES DONNÉES MATHÉMATIQUES (X) ---")
    feat_df = pd.read_csv(MASTER_FEATURES)
    # Rendre les noms de villes standard
    feat_df['city'] = feat_df['city'].astype(str).str.lower().str.replace('-', '_')
    feat_df = feat_df.drop_duplicates(subset=['city'], keep='last')
    
    # Calcul des variables imposées lors de la réunion
    # - Densité : ratio m sur nombre d'arêtes max 0.5*n*(n-1)
    # - Degré moyen : 2*m / n
    feat_df['nodes'] = feat_df['nodes'].astype(float)
    feat_df['edges'] = feat_df['edges'].astype(float)
    feat_df['densite'] = feat_df['edges'] / (0.5 * feat_df['nodes'] * (feat_df['nodes'] - 1))
    feat_df['deg_moyen'] = (2.0 * feat_df['edges']) / feat_df['nodes']
    
    sim_files = glob.glob(os.path.join(SIM_DIR, "*.csv"))
    
    dataset_rows = []
    
    print("\n--- 2. LECTURE DES SIMULATIONS (X et y) / CELA PEUT PRENDRE QUELQUES MINUTES ---")
    for file in sim_files:
        filename = os.path.basename(file)
        # Nom du fichier du type "paris10K_..."
        city_sub = filename.split('10K')[0].split('5K')[0].split('15k')[0].split('20k')[0].split('30k')[0]
        city_name = city_sub.lower().replace('-', '_')
        
        # Trouver la ville dans nos features
        city_feat = feat_df[feat_df['city'] == city_name]
        if city_feat.empty:
            print(f"  [IGNORE] Ville non trouvée dans l'analyse spectrale : {city_name}")
            continue
            
        print(f"  [LECTURE] Traitement de {filename} pour extraire : CO2, durée, véhicules...")
        start_t = time.time()
        
        # Variables pour accumuler lors de la lecture par morceaux (chunk) pour ne pas exploser la RAM
        total_co2_kg = 0.0
        max_step = 0
        veh_types_sets = {} # Dictionnaire pour stocker les IDs uniques par type
        
        try:
            chunk_iter = pd.read_csv(file, usecols=['step', 'veh_id', 'veh_type', 'CO2_g_s'], chunksize=500000)
            for chunk in chunk_iter:
                # Accumuler le CO2 (y)
                total_co2_kg += chunk['CO2_g_s'].sum() / 1000.0
                
                # Chercher la durée de la simulation (X)
                current_max = chunk['step'].max()
                if current_max > max_step:
                    max_step = current_max
                    
                # Compter les véhicules uniques par type (X)
                unique_types = chunk['veh_type'].unique()
                for vt in unique_types:
                    if vt not in veh_types_sets:
                        veh_types_sets[vt] = set()
                    # Ajouter les IDs de ce type
                    vt_ids = chunk.loc[chunk['veh_type'] == vt, 'veh_id'].unique()
                    veh_types_sets[vt].update(vt_ids)
            
            # Assemblage de la ligne du dataset pour XGBoost
            row = {
                'city': city_name,
                # Variables Topologiques X
                'nodes': city_feat['nodes'].values[0],
                'edges': city_feat['edges'].values[0],
                'densite': city_feat['densite'].values[0],
                'deg_moyen': city_feat['deg_moyen'].values[0],
                'rho': city_feat['rho'].values[0],             # Valeur propre max
                'kreiss': city_feat['kreiss'].values[0],       # Constante de Kreiss
                
                # Variables relatives au Trafic X
                'duree_sim_s': max_step,
                'nb_total_veh': sum(len(ids) for ids in veh_types_sets.values()),
                'nb_voitures': len(veh_types_sets.get('car', set())) + len(veh_types_sets.get('passenger', set())),
                'nb_camions': len(veh_types_sets.get('truck', set())) + len(veh_types_sets.get('trailer', set())),
                'nb_bus': len(veh_types_sets.get('bus', set())) + len(veh_types_sets.get('coach', set())),
                'nb_motos': len(veh_types_sets.get('motorcycle', set())) + len(veh_types_sets.get('moped', set())),
                
                # Variable à Prédire y
                'CO2_kg': total_co2_kg
            }
            
            dataset_rows.append(row)
            print(f"    -> OK en {time.time()-start_t:.1f}s | {row['nb_total_veh']} véh, CO2 = {total_co2_kg:.1f} kg")

        except Exception as e:
            print(f"    [ERR] Problème avec {filename}: {e}")
            
    # Sauvegarde du nouveau jeu de données propre
    final_df = pd.DataFrame(dataset_rows)
    final_df.to_csv(OUTPUT_DATASET, index=False)
    print(f"\n--- TERMINÉ --- Dataset XGBoost sauvegardé : {OUTPUT_DATASET}")
    
if __name__ == "__main__":
    process_simulations()
