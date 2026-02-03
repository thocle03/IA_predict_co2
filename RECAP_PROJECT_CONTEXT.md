# Documentation Complète du Projet Jumeau Numérique Trafic (Contexte pour IA)

Ce document résume l'intégralité du projet, de l'architecture technique aux fondements mathématiques, ainsi que la structure exacte des données de sortie. Il est destiné à fournir tout le contexte nécessaire à une autre IA pour traiter les résultats.

---

## 1. Vue d'Ensemble
Ce projet est un **Jumeau Numérique de Trafic Urbain** hybride, combinant simulation microscopique (SUMO) et analyse de données (Python/Streamlit). Il a pour but de modéliser les flux de véhicules, d'analyser les congestions et de calculer précisément les émissions polluantes (CO2, NOx, PMx).

### Stack Technique
-   **Moteur Physique** : SUMO (Simulation of Urban MObility) / C++.
-   **Interface de Contrôle** : TraCI (Traffic Control Interface) via Python.
-   **Dashboard** : Streamlit (Web UI pour lancer et analyser les simus).
-   **Langage** : Python 3.9+.
-   **Librairies Clés** : `sumolib`, `traci`, `pandas`, `scipy` (analyse spectrale), `folium`.

---

## 2. Pipeline de Simulation
Le workflow d'une simulation (`scripts/run_custom_scenario.py`) se déroule en 4 étapes séquentielles :

### Étape 1 : Analyse Mathématique Pré-Simulation (Nouveauté)
Avant de générer le moindre véhicule, le réseau (.net.xml) est analysé comme un graphe.
-   **Module** : `scripts/network/spectral_analysis.py`
-   **Métriques Calculées** :
    -   **Rayon Spectral ($\rho$)** : Indique la stabilité globale.
    -   **Constante de Kreiss ($\mathcal{K}$)** : Mesure la sensibilité aux perturbations transitoires (risque d'effet papillon / congestion explosive).
    -   **Points Critiques** : Identification des nœuds centraux (Centralité de vecteur propre).
-   **Sortie** : `output/{run_id}_spectral.json`

### Étape 2 : Génération de la Demande
-   **Algorithme** : Détection de la plus grande composante fortement connexe (SCC) pour éviter les culs-de-sac.
-   **Profils** : Probabilistes (45% voitures, 30% motos, etc.) définis par l'utilisateur.
-   **Logique** : Distribution uniforme ou "Rush Hour" (distribution bimodale).
-   **Routing** : `duarouter` calcule les plus courts chemins (Dijkstra/A*) et génère un fichier `.rou.xml`.

### Étape 3 : Exécution (2 Modes)
1.  **Mode Standard (TraCI)** : Boucle Python pas-à-pas. Permet le contrôle temps réel (MPC) mais plus lent.
2.  **Mode Fast (Mesoscopic/FCD)** : Exécution directe par le binaire C++ de SUMO. 50x à 100x plus rapide. Pas de contrôle MPC possible.

### Étape 4 : Contrôle MPC (Si activé)
-   **Module** : `scripts/control/mpc_controller.py`
-   **Logique** : Model Predictive Control. Optimisation des feux de signalisation toutes les 10s pour minimiser les files d'attente ($J = \sum x^T Q x + u^T R u$).

---

## 3. Dictionnaire des Données (CSV de Sortie)
Les simulations génèrent des fichiers CSV dans `output/`.
**Format standard** : `simulations/<nom_scenario>/output/simulation.csv` ou `output/{run_id}.csv`.

### Colonnes du fichier CSV
| Colonne | Unité | Description |
| :--- | :--- | :--- |
| `step` | s | Temps de simulation (secondes depuis le début). |
| `veh_id` | string | Identifiant unique du véhicule (ex: `veh_42`). |
| `veh_type` | string | Type du véhicule (voir liste ci-dessous). |
| `x`, `y` | m | Coordonnées spatiales (système de projection interne SUMO). |
| `speed` | m/s | Vitesse instantanée. |
| `accel` | m/s² | Accélération instantanée (calculée par diff). |
| `CO2_g_s` | g/s | Émissions de CO2 (Modèle HBEFA 3.x). Converti depuis mg/s. |
| `NOx_g_s` | g/s | Émissions d'Oxydes d'Azote. |
| `PMx_g_s` | g/s | Émissions de Particules Fines. |
| `fuel_l_s` | l/s | Consommation de carburant instantanée. |

### Types de Véhicules (`veh_type`)
Les caractéristiques physiques et classes d'émissions sont strictes :
-   `car` : Voiture standard (Essence, Euro 4). Longueur 4.5m.
-   `electric` : Voiture électrique (0 émissions locales). Accélération + élevée.
-   `motorcycle` : Moto (Euro 6). Plus agile, occupe moins de place.
-   `scooter` : Scooter urbain. Vitesse max 50km/h.
-   `truck` : Poids lourd (Diesel). Lourd, lent, très polluant.
-   `bus` : Transport en commun.

---

## 4. Métriques et Indicateurs Clés
Pour l'analyse, voici ce qui est pertinent :
1.  **Fluidité** : Vitesse moyenne du réseau vs Vitesse libre.
2.  **Densité** : Nombre de véhicules / km de voie.
3.  **Indice de Pollution** : Somme des CO2/NOx pondérée par type de zone.
4.  **Robustesse** : Corrélation entre la *Constante de Kreiss* (théorique) et la variance de la vitesse (observée).

## 5. Fichiers Auxiliaires
-   `*_meta.json` : Contient les métadonnées globales (durée réelle d'exécution, nombre de véhicules injectés vs arrivés).
-   `*_spectral.json` : Contient les résultats de l'analyse mathématique pré-simu.

---
**Note pour l'IA d'analyse** : Ce système est déterministe. Pour une même `seed`, les résultats sont identiques. Les anomalies dans les CSV (ex: téléportations de véhicules) sont gérées par SUMO et doivent être filtrées si `speed` > 200 km/h ou saut de position aberrant.
