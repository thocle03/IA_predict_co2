#!/usr/bin/env python
# coding: utf-8

# # Entraînement des Modèles d'IA : Prédiction des Émissions de CO2
# Ce notebook rassemble l'ensemble de notre pipeline de machine learning. L'objectif est de prédire les émissions totales de CO2 (variable cible) à partir de caractéristiques d'une ville ("signatures urbaines" : noeuds, arêtes, densité, rayon spectral, constante de Kreiss) et de la charge de trafic (nombre de véhicules).
# 
# Comme expliqué dans la documentation, nous comparons plusieurs modèles d'IA pour identifier le plus performant.
# 

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Préparation & Évaluation
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Modèles
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.neural_network import MLPRegressor


# In[ ]:


# --- 1. CHARGEMENT DES DONNÉES ---
# Attention : Actuellement, le jeu de données est restreint, ce script est prévu 
# pour s'adapter dynamiquement lorsque nous ajouterons plus de villes.
data_path = 'data/dataset_complet.csv'
try:
    df_raw = pd.read_csv(data_path)
    # On supprime les villes sans features spectrales (comme Amsterdam ou Cairo pour le moment)
    df = df_raw.dropna()
    print("Données brutes totales :", len(df_raw))
    print("Données valides pour entraînement :", len(df))
    print(df.head())
except Exception as e:
    print(f"Erreur lors du chargement de {data_path} : {e}")


# In[ ]:


# --- 2. PRÉPARATION DES DONNÉES (FEATURES & TARGET) ---
# Nos features (X) : les informations structurelles, spectrales et le volume de trafic
# Notre cible (y) : The total_co2_kg

# On retire les colonnes non prédictives (identifiants, cibles alternatives)
columns_to_drop = ['city', 'simulation_file', 'total_co2_kg', 'avg_speed_mps']
X = df.drop(columns=columns_to_drop)
y = df['total_co2_kg']

print("Features utilisées :", X.columns.tolist())

# Normalisation des données
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Si nous avons plus de quelques lignes, nous pouvons faire un train_test_split.
# Pour l'instant (5 lignes), ce fractionnement est symbolique ou peut échouer l'entraînement complexe.
# Nous prévoyons le code ici :
if len(df) > 10:
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
else:
    print("Attention: Jeu de données trop petit pour un split robuste. Validation sur l'ensemble complet (overfitting assumé).")
    X_train, X_test, y_train, y_test = X_scaled, X_scaled, y, y


# In[ ]:


# --- 3. DÉFINITION DES MODÈLES D'IA ---
models = {
    'Linear Regression': LinearRegression(),
    'Ridge Regression': Ridge(alpha=1.0),
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
    'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
    'Neural Network (MLP)': MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)
}


# In[ ]:


# --- 4. ENTRAÎNEMENT ET ÉVALUATION ---
results = {}

print(f"{'Modèle':<25} | {'RMSE':<10} | {'MAE':<10} | {'R2 Score':<10}")
print("-" * 65)

for name, model in models.items():
    # Entraînement
    model.fit(X_train, y_train)
    
    # Prédiction
    y_pred = model.predict(X_test)
    
    # Calcul des métriques
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    results[name] = {'RMSE': rmse, 'MAE': mae, 'R2': r2, 'Model': model}
    
    print(f"{name:<25} | {rmse:<10.2f} | {mae:<10.2f} | {r2:<10.2f}")


# In[ ]:


# --- 5. VISUALISATIONS ---
# Comparaison des R2 Scores
names = list(results.keys())
r2_scores = [results[n]['R2'] for n in names]

plt.figure(figsize=(10, 5))
plt.barh(names, r2_scores, color='skyblue')
plt.xlabel('R² Score (Plus haut = meilleur)')
plt.title('Comparaison de la performance des modèles (R²)')
plt.xlim(0, 1.1)
plt.gca().invert_yaxis()
plt.show()

# Importance des features pour le Random Forest
rf_model = results['Random Forest']['Model']
importances = rf_model.feature_importances_

feature_imp_df = pd.DataFrame({'Feature': X.columns, 'Importance': importances})
feature_imp_df = feature_imp_df.sort_values(by='Importance', ascending=False)

plt.figure(figsize=(10, 5))
sns.barplot(x='Importance', y='Feature', data=feature_imp_df, palette='viridis', hue='Feature', legend=False)
plt.title('Importance des "Signatures Urbaines" (Random Forest)')
plt.show()

