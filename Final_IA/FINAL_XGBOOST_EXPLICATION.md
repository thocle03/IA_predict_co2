# Explication Détaillée du Modèle XGBoost pour l'Estimation du CO2

Ce document a pour but de fournir une explication transparente et scientifique de l'algorithme choisi pour notre projet universitaire, en accord avec les dernières directives de la réunion de projet.

---

## 1. Choix du Modèle : Pourquoi XGBoost ?

Comme l'ont souligné les directeurs de recherche :
*   **Nombre de variables explicatives (X)** : Faible (Topologie = 6, Trafic = 5).
*   **Taille de l'échantillon** : Relativement faible (quelques dizaines de simulations massives).

Dans ce contexte, un réseau de neurones profond (Deep Learning) serait inadapté car il nécessite des millions de données pour converger sans faire de "sur-apprentissage" (apprendre par cœur).
Le modèle **XGBoost (Extreme Gradient Boosting)**, basé sur des **Arbres de Décision**, est mathématiquement parfait pour notre cas. Il crée des règles logiques compréhensibles et est très performant sur les données de type "tableur".

### Régression vs Classification

*   Dans l'exemple du dataset *Iris* (vu en réunion), l'algorithme prédit une "classe" (ex: espèce de fleur ou Efficacité="Oui"/"Non"). C'est une **Classification**.
*   Dans notre projet, l'objectif est de prédire une quantité (le grammage de CO2 émis), qui est un nombre continu. Nous utilisons donc l'algorithme de **Régression** : `XGBRegressor` au lieu de `XGBClassifier`. Mathématiquement, au lieu de chercher la classe majoritaire dans la feuille de l'arbre, il en calcule la variance et la moyenne pour estimer une valeur exacte. L'évaluation de précision (`accuracy` en pourcentages) est remplacée par le $R^2$ et le MAE (Erreur Moyenne Absolue en Kg).

---

## 2. Définition Mathématique de $X$ et $y$

Sur les bases des consignes strictes données en réunion, pour chaque simulation :

### Les variables explicatives $X$ (Ce que le modèle lit)
**Les variables topologiques ($X_{topo}$) :**
*   $n$ : `nodes` (Nombre d'intersections)
*   $m$ : `edges` (Nombre de routes)
*   **Densité** (`densite`) : Le ratio $\frac{m}{0.5 \times n \times (n-1)}$
*   **Degré Moyen** (`deg_moyen`) : Le nombre moyen de correspondances par nœud $\frac{2 \times m}{n}$
*   **Analyse spectrale** (`rho`) : Valeur propre maximale renseignant sur la connectivité du réseau.
*   **Constante de Kreiss** (`kreiss`) : Sensibilité du graphe aux perturbations (ex: effet domino d'un bouchon).

**Les variables relatives au trafic ($X_{trafic}$) :**
*   Durée de la simulation : `duree_sim_s` (en secondes)
*   Nombre total de véhicules : `nb_total_veh`
*   Détails : `nb_voitures`, `nb_camions`, `nb_bus`, `nb_motos` (Nombres absolus exacts extraits à partir du fichier)

### La variable à prédire $y$ (Ce que le modèle doit deviner)
*   $y$ : La quantité globale de CO2 générée (en Kg).

Chaque simulation SUMO se transforme donc en un Tuple complet $(y | X)$ pour l'entraînement.

---

## 3. Comment ça marche concrètement ? (Couche par Couche)

Le terme **"Boosting"** signifie qu'au lieu de créer un seul arbre géant (qui se trompe), XGBoost crée une **séquence de centaines de petits arbres de décision**. Chaque nouvel arbre est conçu spécifiquement pour corriger les erreurs mathématiques (les résidus) du précédent.

### Exemple de cheminement pas-à-pas (Aperçu interne) :

**Etape 0 : Prédiction de base ($F_0$)**
*   L'algorithme analyse toutes les simulations sans réfléchir et fait une moyenne globale : "Le CO2 moyen émis par ces villes est de $20,000$ Kg".

**Etape 1 : Le premier Arbre ($h_1$)**
*   Le modèle calcule l'erreur (le gradient résiduel) pour chaque ville : 
    * *Pour Paris (Réel = $35,000$ Kg), l'erreur est $+15,000$ Kg.*
    * *Pour Monaco (Réel = $5,000$ Kg), l'erreur est $-15,000$ Kg.*
*   Il crée un arbre $h_1$ pour essayer de **prédire cette erreur**. 
*   **L'arbre $h_1$ décide** : "*Si (Nombre de Vrai Total Veh > 8000) ET (Constante Kreiss > 40), alors la correction est de $+10,000$ Kg.*" 
*   **Mise à jour globale ($F_1$)** : Nouvelle Prédiction = $F_0 + \eta * h_1$ (où $\eta$ est le taux d'apprentissage, ex: 0.1). L'algorithme se rapproche doucement de la vérité sans être trop brutal pour éviter l'overfitting.

**Etape 2 : Le deuxième Arbre ($h_2$)**
*   L'arbre 1 a corrélé le gros du trafic, les erreurs restantes sont plus subtiles.
*   L'arbre $h_2$ cherche à corriger les nouvelles petites erreurs de $F_1$. 
*   **L'arbre $h_2$ décide** : "*Sur les villes restantes mal estimées, si (Densité < 0.05) ALORS les Camions polluent proportionnellement 20% de plus. Donc on ajoute $+500$ Kg pour la branche concernée.*"

**Etape N (Arbre final)**
*   Le modèle a répété l'opération 1000 fois.
*   La prédiction finale $y_{pred}$ est littéralement la somme des prédictions (les corrections) de tous les 1000 arbres.

### Décisions à l'intérieur d'un nœud
Quand l'algorithme "décide" de séparer une branche, il cherche mathématiquement quelle variable ($X_{densite}$, $X_{kreiss}$, $X_{nb\_camions}$...) permet de diviser les villes en deux groupes pour que la variance de l'erreur dans chaque groupe soit la plus petite possible.

### Hyperparamètres clés configurés
*   **`n_estimators`=1000** : Nous forçons le modèle à générer 1000 petits arbres.
*   **`learning_rate`=0.05** : Chaque arbre ne donne que 5% de son avis. Ceci force la robustesse.
*   **`max_depth`=6** : Aucun arbre ne peut avoir plus de 6 questions successives. Ceci est critique face au manque de données : cela empêche à l'algorithme d'isoler une seule ville pour apprendre son résultat par cœur.
*   **`colsample_bytree`=0.8** : "Randomness". Chaque arbre ne "voit" que 80% des variables au hasard (ex: parfois il ne voit pas la valeur propre, parfois il ne voit pas les camions). Cela force l'algorithme à trouver des corrélations multiples.
