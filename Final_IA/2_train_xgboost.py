# Entraînement Final du Modèle XGBoost
# Ce script utilise les données d'entraînement générées (topologie + véhicules)
# pour prédire la quantité de CO2 avec l'algorithme des Forêts Xtrêmes et Gradient Boosting.

import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, 'data', 'xgboost_training_data.csv')
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'xgb_co2_predictor.joblib')

def train_model():
    print("--- 1. CHARGEMENT DU DATASET ---")
    df = pd.read_csv(DATASET_PATH)
    
    # === SÉPARATION X ET Y SELON LES RECOMMANDATIONS DES DIRECTEURS ===
    # Variables prédictives X 
    X = df.drop(columns=['city', 'CO2_kg'])
    
    # Variable à prédire y (Quantité de CO2)
    y = df['CO2_kg']
    
    print(f"Dataset contenant {len(df)} simulations parfaites.")
    print(f"Variables X utilisées : {list(X.columns)}")
    print(f"Variable y à prédire : CO2_kg")
    
    # Création du jeu d'entraînement (80%) et de test (20%) comme l'exemple 'iris'
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\n--- 2. ENTRAÎNEMENT DE L'XGBOOST ---")
    print(f"Taille ensemble d'entraînement : {len(X_train)}")
    print(f"Taille ensemble de test : {len(X_test)}")
    
    # Création du modèle. 
    # NOTE: On utilise XGBRegressor (Régression continue) et NON XGBClassifier (Catégories/Classes) 
    # car le CO2 est une valeur numérique continue (un nombre de kilogrammes).
    model = xgb.XGBRegressor(
        n_estimators=1000,      # Nombre d'arbres
        learning_rate=0.05,     # Taux d'apprentissage
        max_depth=6,            # Profondeur de chaque arbre
        subsample=0.8,          # Fraction de données à utiliser par arbre (contre l'overfitting)
        colsample_bytree=0.8,   # Fraction de colonnes par arbre
        random_state=42         # Pour des résultats répétables
    )
    
    # On entraine le modèle (apprentissage !)
    model.fit(X_train, y_train)
    
    print("\n--- 3. ÉVALUTION DES RÉSULTATS ---")
    # On teste le modèle
    y_pred = model.predict(X_test)
    
    # On évalue la qualité du modèle (Remplace le accuracy_score car données continues)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Erreur Moyenne Absolue (MAE) : {mae:.2f} kg (Moyenne d'erreur sur chaque prédiction)")
    print(f"Racine de l'Erreur Quadratique Moyenne (RMSE) : {rmse:.2f} kg")
    print(f"Score R2 (Précision globale) : {r2 * 100:.2f}%")
    
    # Sauvegarder le modèle !
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump((model, list(X.columns)), MODEL_PATH)
    print(f"\n[OK] Modèle complet (XGBoost et liste des colonnes) sauvegardé sous :\n{MODEL_PATH}")
    
    # --- BONUS : IMPORTANCE DES VARIABLES ---
    # XGBoost permet de savoir exactement l'importance qu'il donne à chaque variable !
    importance = model.feature_importances_
    features = list(X.columns)
    importance_df = pd.DataFrame({'Variable': features, 'Impact': importance}).sort_values('Impact', ascending=False)
    
    print("\n--- 4. CLASSEMENT DES VARIABLES LES PLUS IMPORTANTES (CE QUE L'IA A APPRIS) ---")
    for idx, row in importance_df.iterrows():
        print(f" - {row['Variable']:<15} : {row['Impact']*100:.1f}% d'influence")

if __name__ == "__main__":
    train_model()
