# Documentation : Modèles d'Intelligence Artificielle de Prédiction des Émissions

Ce document détaille l'approche de Machine Learning adoptée pour la prédiction des émissions de CO2 des réseaux routiers à partir de leurs caractéristiques et données spectrales (la **Signature Urbaine**).

## 1. Contexte & Objectif

Conformément au document `NextStepIA.md` et à nos notes techniques, l'objectif principal de cette IA est de **remplacer partiellement SUMO par un modèle de prédiction instantané**. 
L'IA doit être capable d'estimer, en un temps de calcul minime (quelques millisecondes), les émissions globales de CO2 d'une ville sans avoir à exécuter de simulation complète coûteuse en ressources.

## 2. Le Pipeline des Données (Features & Targets)

Puisque les simulations lourdes de SUMO pèsent très lourd (jusqu'à 3 Gigaoctets par fichier CSV), le système est divisé en **un pipeline de traitement asynchrone** permettant d'économiser la RAM.

### 2.1 Extraction et Calcul des Caractéristiques Spectrales
Grâce au laboratoire spectral, nous récupérons les données mathématiques de réseau pour chaque ville :
- `n_nodes`, `n_edges`, `density` : Topologie physique.
- `spectral_radius` ($\rho$) & `kreiss_constant` ($K$) : Notre *Signature Urbaine*, expliquant la fragilité mathématique de la ville.

*Ces constantes sont acquises et stockées de manière persistante dans `data/spectral_features_master.csv` (grâce au script `process_missing_cities.py` qui va lui même utiliser `scripts/analyze_city_structure.py`).*

### 2.2 Compilation de la Banque d'Entraînement (`prepare_all_data.py`)
Avant l'entraînement, un script python compile la base de données. Il lit toutes les métriques de simulation lourdes situées dans le dossier `data/simulations` pour récupérer la performance (Ground Truth) et les fusionne avec les signatures spectrales :
- `total_vehicles` : Cible de trafic
- `total_co2_kg` : Variable cible à apprendre (Target).
- `avg_speed_mps` : Seconde métrique (indicateur de congestion).

Tout ceci génère **le jeu de données consolidé : `data/dataset_complet.csv`**.

## 3. Guide d'Exécution : De la Carte à la Prédiction

Désormais, tout le pipeline d'intelligence artificielle est fluide et modulaire. Si vous souhaitez ré-entrainer ou analyser vos modèles avec de nouvelles villes, voici l'ordre d'exécution précis (le "Workflow") :

### Étape 1 : Remplir la Base de Simulations
Placer toutes vos nouvelles simulations de trafic (fichiers au format CSV extraits de SUMO, par exemple `madrid10K_2026.csv`) dans le dossier : `data/simulations/`.

### Étape 2 (Facultative) : Assurer la Topologie Spectrale
Si vous avez de nouvelles villes pour lesquelles **l'analyse spectrale (Kreiss, Rayon) n'a jamais été faite**, lancez l'extraction.
Ouvrez un terminal et ajoutez vos villes dans le fichier :
```bash
python process_missing_cities.py
```
*(Ceci téléchargera la map de la ville et mettra à jour le fichier maître `data/spectral_features_master.csv`).*

### Étape 3 : Compiler le Jeu de Données Machine Learning
Assemblez toutes ces métriques et allégez les fichiers pour l'IA en fusionnant les données :
```bash
python prepare_all_data.py
```
*(Ceci génèrera `data/dataset_complet.csv` de manière optimisée sans saturer la RAM, en sautant intelligemment les lignes avec des caractéristiques manquantes).*

### Étape 4 : Lancer le Hub d'Intelligence Artificielle
Vous pouvez désormais lancer l'entraînement pour évaluer la prédiction du CO2. Deux solutions s'offrent à vous :
- **Si vous voulez modifier ou voir le code interagir** :
  ```bash
  jupyter notebook entrainement_modeles_prediction.ipynb
  ```
  *(Ouvrez le fichier localement dans votre navigateur pour manipuler les données et explorer les graphiques de performances).*
- **Si vous préférez un rapport rapide en terminal** :
  ```bash
  python entrainement_modeles_prediction.py
  ```

---
## 4. Modèles Sélectionnés pour la Prédiction

La phase finale (Étape 4) benchmark plusieurs modèles sur `dataset_complet.csv` :
1. **Régression Linéaire & Ridge** : Vérification si les graphes ont une morphologie linéaire et pondération des poids.
2. **Random Forest & Gradient Boosting (XGBoost/LightGBM)** : L'état de l'art pour capturer l'importance de nos variables spectrales sur la prédiction (arbres de décisions).
3. **Perceptron Multicouche (Réseaux de Neurones / MLP)** : Outil de "Deep Learning" essayant de capter des motifs complexes dans la signature spectrale d'une ville.
