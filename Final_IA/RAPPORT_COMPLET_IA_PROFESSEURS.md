# Rapport Complet : Architecture et Choix du Modèle d'IA (XGBoost)
Ce rapport documente les choix algorithmiques, la préparation des données et le fonctionnement mathématique du modèle prédictif final (XGBoost) développé pour l'estimation globale des émissions de CO2. Il est spécifiquement rédigé pour répondre aux questions d'architecture posées par le corps professoral.

---

## 1. Choix du Modèle d'Apprentissage : XGBoost Régresseur

### 1.1. Pourquoi XGBoost plutôt que du Deep Learning ?
Face à un jeu de données contenant un nombre restreint de simulations à l'échelle d'une ville (quelques dizaines d'exemples globaux) et une dizaine de variables explicatives (topologie et trafic), un réseau de neurones profond (Deep Learning) serait inadapté et mènerait inévitablement à un sur-apprentissage (*overfitting*). 

Le choix s'est porté sur **XGBoost (Extreme Gradient Boosting)**, basé sur des arbres de décision. Il est mathématiquement idéal pour les données tabulaires de petite dimension, créant des règles logiques interprétables.

### 1.2. Régression vs Classification
Contrairement aux exemples classiques (comme le dataset *Iris* qui classifie des espèces de fleurs), notre variable cible ($y$) est une **quantité continue** (le kilogrammage de CO2). Nous utilisons donc l'implémentation **`XGBRegressor`**. L'évaluation se fait via des métriques d'erreur quantitatives : la MAE (Erreur Moyenne Absolue en Kg) et le score $R^2$, et non via une simple précision (*accuracy*) en pourcentage.

---

## 2. Pipeline de Données : Du Microscopique au Macroscopique

Une question fondamentale concerne la granularité des données ingérées par l'Intelligence Artificielle. **L'XGBoost ne prend PAS en compte chaque seconde, chaque accélération ou chaque vitesse individuelle générée par le simulateur.**

Il existe une séparation stricte des rôles dans notre architecture, conçue pour éviter un biais systémique majeur lors de l'entraînement :

*   **1. SUMO (Le Moteur Physique Microscopique) :** SUMO calcule la physique réelle à la seconde près. Pour chaque véhicule, il évalue l'accélération, le freinage, le type de moteur à chaque *step*. C'est lui qui génère les fichiers CSV massifs recensant l'émission de CO2 instantanée (`CO2_g_s`) pour chaque véhicule à chaque seconde.
*   **2. Le Script d'Agrégation (`1_create_dataset.py`) :** Ce script agit comme un compresseur mathématique. Il lit les millions de lignes générées par SUMO et **les écrase totalement pour en faire une somme globale**. Pourquoi ne pas envoyer chaque ligne du CSV (chaque véhicule à chaque seconde) directement dans l'arbre XGBoost ? Parce que l'objectif du projet *n'est pas* de prédire si une voiture X va polluer à la seconde Y en accélérant. L'objectif est de prédire l'**émergence globale et macroscopique** d'une ville toute entière. Si l'arbre apprenait ligne par ligne, il jugerait le CO2 basé uniquement sur le type de véhicule ("C'est un camion, donc ça pollue M") sans jamais comprendre le concept de "bouchon total à l'échelle de la ville". Nous devons donc réaliser une **agrégation préalable**.
*   **3. L'XGBoost (Le Modèle Prédictif Macroscopique) :** Les millions de lignes physiques de SUMO sont transformées en **UNE SEULE ET UNIQUE LIGNE** d'entraînement pour l'IA (Ex : *Ville X, Densité: 0.05, 27000 véhicules, = 145810 Kg de CO2*). Le modèle observe ainsi uniquement les causes globales (géométrie, volume de trafic) et la conséquence définitive (CO2 total). L'arbre n'appelle donc jamais les fichiers unitaires, car ils contiennent un bruit microscopique (accélération d'un individu isolé) non pertinent pour une étude structurelle de l'infrastructure urbaine.

L'IA n'apprend donc aucune règle de cinématique fondamentale (accélération/freinage) ; elle apprend les **corrélations macroscopiques existant entre une topologie de réseau, une charge de trafic, et le résultat émergeant de la somme des émissions**.

---

## 3. Choix des Paramètres (Features) d'Entrée

Au lieu de calculer au préalable un "pourcentage de ressemblance" mathématique entre les villes (approche algorithmique de type *K-Nearest Neighbors* ou *k-NN*) pour entraîner le modèle, nous avons pris la décision stratégique de fournir directement les métriques topologiques brutes (Densité, Constante de Kreiss, Valeur Propre $\rho$) à l'XGBoost. 

Une question souvent posée est : *Pourquoi ne pas avoir calculé nous-mêmes un score "La ville A ressemble à 80% à la ville B" avant de l'envoyer à l'arbre ?*

Voici les trois raisons scientifiques majeures empêchant l'utilisation d'un pourcentage de ressemblance :

### 3.1. Gestion fondamentale de la Non-linéarité et l'Effet Papillon
L'impact de la topologie sur les émissions de CO2 n'est absolument pas linéaire. Le trafic routier répond à la théorie du chaos urbain. Deux villes peuvent partager 95% de similitude d'infrastructures (même nombre de routes, même dimension), mais une variation minime de 5% sur un goulot d'étranglement ou sur la constante de Kreiss (qui indique la vulnérabilité microscopique aux congestions) peut totalement paralyser le trafic urbain. **Un algorithme se basant sur une simple ressemblance lissée noierait ce seuil de bascule critique dans la moyenne**. Au contraire, les arbres de décision de XGBoost ne font pas de moyennes : ils coupent strictement. Ils excellent pour identifier les seuils critiques non linéaires : *"SI Trafic > X ET Kreiss > Y, ALORS saturation majeure instantanée"*.

### 3.2. Le Paradoxe du Curseur Dimensionnel (Métrique Arbitraire)
Si les chercheurs devaient calculer un pourcentage de ressemblance en amont, une faille méthodologique apparaîtrait : *comment définir mathématiquement l'importance relative d'une différence de 100 intersections face à un écart de 0.1 sur le degré moyen ?* Autrement dit, quelle formule utiliser pour définir qu'une ville ressemble à une autre sans introduire un biais humain ? 
En passant *directement* les features brutes à XGBoost au lieu d'un pourcentage prémâché, **c'est l'algorithme XGBoost qui découvre et détermine lui-même au cours de l'entraînement l'importance et le poids réel de chaque variable** pour juger si deux dynamiques de trafic sont fondamentalement similaires.

### 3.3. Exigence d'Explicabilité Scientifique (Feature Importance)
L'utilisation de features logiques et brutes permet une découverte analytique post-entraînement, vitale dans un cadre académique. L'algorithme XGBoost, par la nature de ses arbres, construit nativement un classement mathématique de l'importance des variables (la *Feature Importance*). 
*   **Si nous utilisions un pourcentage de ressemblance :** L'IA conclurait *"Dubaï pollue parce qu'elle ressemble à 75% à Paris"*. Cette conclusion est inepte scientifiquement, car elle n'apporte aucune donnée d'amélioration structurelle.
*   **En utilisant les features brutes :** Nous pouvons démontrer scientifiquement aux urbanistes *pourquoi* une topologie génère de la pollution : *"La constante de Kreiss impacte l'apparition stricte de bouchons à 15%, tandis que la densité des nœuds ne pèse qu'à 5%"*. Seules les données brutes permettent d'extraire la cause originelle de la pollution.

---

## 4. Fonctionnement Interne de l'Entraînement Algorithmique

Le principe du **Gradient Boosting** consiste à ne pas construire un seul arbre complexe, mais d'entraîner une longue séquence de petits arbres simples qui corrigent mathématiquement les erreurs des précédents.

1.  **Prédiction Initiale ($F_0$) :** Le modèle fait une moyenne de toutes les émissions de toutes les villes.
2.  **Arbres Correcteurs ($h_n$) :** Le premier arbre analyse les résidus (l'erreur entre la prédiction "naïve" et la réalité). S'il s'est trompé de +15 000 Kg sur une ville très dense, il crée une règle pour rajouter spécifiquement ce poids. Le deuxième arbre corrigera les infimes erreurs laissées par le premier arbre, et ainsi de suite.
3.  **Somme Finale :** La prédiction globale est la somme du consensus de toutes les micro-corrections des arbres.

### Configuration Strictes des Hyperparamètres pour éviter le Sur-apprentissage
Notre jeu de données étant petit en nombre de lignes, le modèle a été fortement contraint :
*   **`n_estimators=1000`** : Forcer la création de 1000 arbres.
*   **`learning_rate=0.05`** : Chaque arbre n'applique que 5% de sa trouvaille, forçant l'algorithme à avancer "à petits pas" robustes.
*   **`max_depth=6`** : Brider la complexité de chaque arbre à seulement 6 "questions", l'empêchant d'isoler une ville pour apprendre son résultat par cœur.
*   **`subsample=0.8`** et **`colsample_bytree=0.8`** : Injecter de l'aléatoire. Chaque arbre ne voit que 80% des villes et 80% des variables, le forçant à découvrir diverses corrélations plutôt que de s'ancrer aveuglément sur la variable la plus dominatrice.

---

## 5. Précisions sur les Limites Prédictives : Les Effets de Congestion

Lors de tests virtuels hors normes (par exemple, forcer 73 000 véhicules sur un réseau qui n'en possédait que 27 000 dans la base réelle de SUMO), le modèle XGBoost a parfois tendance à renvoyer des prédictions (ex: 145 000 kg) se rapprochant étonnamment de celles de trafics beaucoup plus modestes. 

Deux phénomènes mathématiques et physiques expliquent cela :

1.  **L'Effet Plafond de l'Extrapolation :** Un arbre de décision ne *"projette"* pas une ligne infinie. S'il n'a jamais croisé de simulation dépassant les 150 tonnes de CO2 dans les données d'entraînement fournies, ses feuilles terminales les plus hautes s'arrêteront à ce montant maximal. Les arbres sont d'excellents interpolateurs, mais de mauvais extrapolateurs lointains.
2.  **Apprentissage de la Congestion Absolue :** SUMO calcule qu'un moteur au régime ralenti, bloqué dans un bouchon infranchissable (vitesse = 0), peut potentiellement émettre moins à l'instant mathématique $t$ qu'un véhicule en forte accélération perpétuelle. Si l'IA conclut qu'à partir de 25 000 véhicules, la constante de Kreiss indique une *saturation réseau totale = bouchon universel*, rajouter 50 000 véhicules fantômes à l'arrêt ne fait qu'appuyer sur la même "feuille" plafonnée de l'arbre qui décrit le comportement d'une ville totalement étouffée. 

L'IA simule donc bien l'effet de congestion totale, mais reste captive de l'amplitude maximale générée en amont par le moteur SUMO lors de la session de création du dataset.


streamlit run Final_IA/app_streamlit.py