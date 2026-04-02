# Script de Test de l'Intelligence Artificielle (XGBoost)
# Ce script permet de simuler virtuellement une ville et un trafic 
# pour que l'IA prédise la quantité de CO2.

import os
import pandas as pd
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'xgb_co2_predictor.joblib')
MASTER_FEATURES = os.path.join(BASE_DIR, 'data', 'spectral_features_master.csv')

def tester_ia():
    print("=== ASSISTANT DE PRÉDICTION CO2 CHERCHEUR ===")
    
    # 1. Chargement du Modèle
    if not os.path.exists(MODEL_PATH):
        print(f"[ERREUR] Le modèle {MODEL_PATH} est introuvable. Lancez d'abord 2_train_xgboost.py")
        return
        
    model, features_list = joblib.load(MODEL_PATH)
    print("[OK] Modèle XGBoost chargé en mémoire.\n")
    
    # 2. Base de données Topologique
    feat_df = pd.read_csv(MASTER_FEATURES)
    feat_df['city'] = feat_df['city'].astype(str).str.lower().str.replace('-', '_')
    feat_df = feat_df.drop_duplicates(subset=['city'], keep='last')
    
    # Recalcul des métriques exigées
    feat_df['nodes'] = feat_df['nodes'].astype(float)
    feat_df['edges'] = feat_df['edges'].astype(float)
    feat_df['densite'] = feat_df['edges'] / (0.5 * feat_df['nodes'] * (feat_df['nodes'] - 1))
    feat_df['deg_moyen'] = (2.0 * feat_df['edges']) / feat_df['nodes']
    
    # 3. Mode Interactif : Demander la ville et le trafic
    print(f"Villes disponibles en base (pour leurs caractéristiques mathématiques) :")
    villes_dispos = sorted(feat_df['city'].tolist())
    print(", ".join(villes_dispos))
    print("-" * 50)
    
    nom_ville = input("👉 Entrez le nom de la ville à utiliser pour sa géométrie (ex: berlin) : ").strip().lower()
    
    city_data = feat_df[feat_df['city'] == nom_ville]
    if city_data.empty:
        print(f"[ERREUR] La ville '{nom_ville}' n'existe pas dans nos calculs spectraux.")
        return
        
    print(f"\n[TOPOLOGIE] Données géométriques de {nom_ville} chargées (Nœuds: {int(city_data['nodes'].values[0])}, Kreiss: {city_data['kreiss'].values[0]:.2f})")
    
    # Demander le trafic fictif
    print("\n--- CONFIGURATION DU TRAFIC POUR LA PRÉDICTION ---")
    try:
        duree = float(input("Durée de la simulation projetée (en secondes, ex: 1000) : "))
        voitures = int(input("Nombre total de VOITURES : "))
        camions = int(input("Nombre total de CAMIONS : "))
        bus = int(input("Nombre total de BUS : "))
        motos = int(input("Nombre total de MOTOS : "))
    except ValueError:
        print("[ERREUR] Veuillez entrer uniquement des nombres !")
        return
        
    total_veh = voitures + camions + bus + motos
    print(f"\n[TRAFIC] {total_veh} véhicules configurés.")
    
    # 4. Construction de la Ligne de Test (Le Tuple X)
    # L'ordre doit être EXACTEMENT le même que lors de l'entraînement
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
    
    # Transformer en tableau Pandas avec l'ordre exact demandé par le modèle
    df_new = pd.DataFrame([donnees_test], columns=features_list)
    
    # 5. La Prédiction Magnique !
    prediction = model.predict(df_new)[0]
    
    # Affichage du Résultat FInal
    print("\n" + "="*50)
    print("🌍 RÉSULTAT DE L'INTELLIGENCE ARTIFICIELLE 🌍")
    print("="*50)
    print(f"La quantité totale de CO2 estimée générée sera de :")
    print(f">>> {prediction:.1f} Kg de CO2 <<<")
    print("="*50)


if __name__ == "__main__":
    tester_ia()
