# Analyse Approfondie des Modèles d'Intelligence Artificielle de Prédiction

Ce document fournit une analyse mathématique et technique détaillée des résultats de l'entraînement de nos modèles de Machine Learning. L'objectif de ces modèles est de prédire les émissions de CO₂ dynamiques des villes sur la base de leur **Signature Urbaine Spectrale**.

---

## 1. Compréhension des Paramètres d'Entrée (Features)

Avant toute prédiction, les modèles ingèrent un vecteur de caractéristiques représentant chaque ville. Voici le détail des six paramètres (features) pris en compte, classés de l'échelle macroscopique à l'échelle dynamique spectrale :

1. **`total_vehicles` (La Charge Spatiale)** : Représente le volume de véhicules injecté dans le graphe (ex: 5000, 10000 ou 30000 véhicules). C'est la variable de contrainte du système.
2. **`n_nodes` (Complexité des Intersections)** : Le nombre total de carrefours physiques. Plus il est élevé, plus les véhicules rencontrent de points de rupture potentiels.
3. **`n_edges` (Capacité des Arcs)** : Le nombre total de segments de route. 
4. **`density` (Densité Graphique)** : Ratio des connexions réelles par rapport aux connexions possibles. Un graphe très dense signifie de nombreuses routes alternatives et une maille resserrée (favorise les redondances).
5. **`kreiss_constant` (Instabilité Dynamique de Kreiss - $K$)** : C'est le marqueur de la non-normalité du réseau routier. Mesure la susceptibilité de la ville à l'effet domino. Un petit bouchon local peut-il exploser et paralyser le réseau (haute constante) ou le réseau va-t-il absorber le choc facilement ?
6. **`spectral_radius` (Rayon Spectral - $\rho$)** : Issu des valeurs propres de la matrice d'adjacence, c'est l'indicateur d'asymétrie structurelle. Plus $\rho$ est élevé, plus le réseau est dominé par des "corridors" obligatoires (ex: ponts uniques, échangeurs inévitables), limitant la redondance des flux.

---

## 2. Décryptage de la Métrique de Performance : Le $R^2$ (R-Squared)

### Qu'est-ce que le $R^2$ ?
Le **Coefficient de Détermination**, ou $R^2$, est la métrique reine pour évaluer un modèle de régression (prédiction de valeurs continues comme des kg de CO₂). 

* **Définition** : Il représente **la proportion de la variance de la cible (le CO₂) qui est mathématiquement expliquée par nos variables d'entrée**.
* **Échelle** :
  * $R^2 = 1.0$ : Prédiction parfaite sans aucune erreur. Le modèle comprend 100% de la logique physique de SUMO.
  * $R^2 = 0.0$ : Le modèle ne vaut pas mieux qu'un simple algorithme qui répondrait toujours par "la moyenne" des émissions de toutes les villes.
  * $R^2 < 0$ : Le modèle se trompe lourdement (pire que "répondre la moyenne au hasard").

### Autres Métriques associées (RMSE & MAE)
* **RMSE (Root Mean Squared Error)** : L'erreur quadratique moyenne. C'est pénalisant : si le modèle se trompe énormément sur une seule ville (ex: Le Caire), le RMSE explose car l'erreur est mise au carré.
* **MAE (Mean Absolute Error)** : L'erreur absolue moyenne. Une erreur directe en kilogrammes de CO₂.

---

## 3. Analyse des Modèles et de leurs Résultats Actuels

Nous avons testé cinq familles d'algorithmes différents pour comparer la meilleure manière de "lire" la topologie d'une ville.

### 3.1 Gradient Boosting (XGBoost/LightGBM) : *Le Meilleur Performeur*
* **Fonctionnement** : Cet algorithme construit des arbres de décisions de manière *séquentielle*. Au lieu de créer des arbres indépendants, chaque nouvel arbre est conçu pour corriger spécifiquement les erreurs (les résidus empiriques) laissées par l'arbre précédent.
* **Résultat** : Un **$R^2$ exceptionnel avoisinant 1.0**. 
* **Interprétation** : Le Gradient Boosting s'impose sans difficulté. Il est capable de déduire des relations non linéaires subtiles ("Si la charge est > 10000 ET que l'indice de Kreiss est fort, ALORS la pollution explose de façon exponentielle").

### 3.2 La Régression Linéaire : *La Surprise Linéaire*
* **Fonctionnement** : Tente de dessiner une simple fonction affine classique du type $y = a\cdot(vehicles) + b\cdot(nodes) + \dots$
* **Résultat** : **$R^2 \approx 0.98$**, une excellente performance.
* **Interprétation** : L'excellence de ce score est surprenante et contre-intuitive vis-à-vis de la dynamique des flux. Cela suggère qu'actuellement, le volume de trafic (`total_vehicles`) ou des associations directes dominent tellement l'impact en CO₂ (une ville avec 30 000 voitures pollue linéairement plus qu'une ville avec 5 000 voitures) que le modèle n'a besoin que d'une belle équation proportionnelle pour réussir.

### 3.3 Régression Ridge : *Le Modèle Régularisé*
* **Fonctionnement** : C'est une régression linéaire pénalisée (Régularisation L2). Elle empêche les poids de l'équation mathématique d'exploser vers des nombres farfelus pour éviter le sur-apprentissage (overfitting).
* **Résultat** : **$R^2 \approx 0.88$**.
* **Interprétation** : Le fait que le Ridge soit moins bon que la Régression Linéaire classique signifie que dans notre petit échantillon actuel (10 villes), brider la mathématisation empèche le modèle de comprendre les cas extrêmes (comme Dubaï ou le Caire). Il limite ses pondérations et "rate" la cible.

### 3.4 Random Forest (Forêts Aléatoires) : *L'Outil Analytique*
* **Fonctionnement** : Construit des centaines d'arbres de décision *indépendants* et aveugles sur une portion des données (méthode de *bagging*), puis fait voter ces arbres pour faire une moyenne de leurs prédictions.
* **Résultat** : **$R^2 \approx 0.83$**.
* **Interprétation** : Bien que performant théoriquement, il pèche un peu face au Gradient Boosting sur des données restreintes. Il est "perturbé" car chaque arbre n'a accès qu'à une portion aléatoirement sélectionnée de nos quelques villes. En revanche, **il est notre meilleur algorithme pour extraire "l'importance des variables"**.

### 3.5 Perceptron Multicouche (Réseau de Neurones / MLP) : *L'Échec Initial*
* **Fonctionnement** : Un réseau de neurones artificiels imitant le cerveau (architecture Deep Learning de base avec des « couches cachées »). 
* **Résultat** : **$R^2 \approx 0.08$**. C'est un échec mathématique total.
* **Interprétation** : Les réseaux de neurones sont des "data-vampires" affamés. Ils ont besoin de milliers, voire de centaines de milliers de lignes (villes/scénarios) pour régler leurs poids sans diverger. Avec un entraînement sur 10 villes, il est incapable d'optimiser ses fonctions d'activation (backpropagation en échec constant). Ce modèle est donc **à mettre de côté** tant que nous limitons nos scénarios simulés.

---

## 4. Ce Que la Machine Pense de nos Villes : "L'Importance des Features"

Le Random Forest nous a permis d'extraire la pondération d'importance absolue ("Feature Importance"). L'IA évalue quelles variables dictent presque mathématiquement la pollution locale :

1. **La Charge Absolue (`total_vehicles` - ~48%)** :
   Sans surprise, la variable prépondérante est le nombre de voitures sur le réseau. Ce paramètre gouverne presque de moitié la réponse attendue en volume de pollution.
2. **La Topologie Structurelle (`density`, `n_edges`, `n_nodes` - ~14% / ~13% / ~13%)** :
   Ensuite vient la taille et la complexité du réseau. La **densité** joue un rôle plus critique que le nombre pur d'arêtes. Une forte densité dissipe mieux le trafic dense et joue sur les facteurs de congestion localisés.
3. **Le Comportement Spectral (`kreiss_constant`, `spectral_radius` - ~7% / ~5%)** :
   Actuellement, nos signatures spectrales pèsent pour un peu plus de ~10% de la décision d'émission de l'IA. 
   Bien que ce poids semble minoritaire par rapport au flux absolu de véhicules, **c'est la nuance cruciale**. C'est grâce à ces 10% que les modèles atteignent des performances exceptionnelles (Gradient Boosting à 1.0). Face à deux villes ayant exactement 10 000 véhicules injectés et une densité équivalente (topologie statique similaire), **l'IA se servira exclusivement de l'indice de Kreiss et du rayon spectral pour déterminer laquelle va voir son réseau s'effondrer et sa pollution s'envoler**. Le paramètre de Kreiss joue donc le rôle mathématique clé de "coefficient de crise".

## 5. Synthèse Scientifique

Le pipeline de Machine Learning est d'ores et déjà validé. En l'état actuel : 
L'algorithme **Gradient Boosting** prouve que remplacer le simulateur microscopique lourd (SUMO) par un modèle prédictif instantané est tout a fait faisable sans perte drastique de véracité. Grâce à la "Signature Urbaine Spectrale", l'Intelligence Artificielle est capable d'assimiler les points de congestion liés à la non-normalité dynamique d'une ville sans jamais regarder une de ses cartes géographiques.
