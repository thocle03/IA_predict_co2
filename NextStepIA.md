## 1. Concept de « Signature Urbaine » : vers un ADN mathématique des villes

Dans la continuité de mon travail, je formalise l’hypothèse centrale suivante : **chaque ville possède une signature mathématique propre**, que j’appelle sa *signature urbaine*. Cette signature repose sur deux niveaux complémentaires de description.

### a) Variables topologiques classiques – la structure physique

Je considère d’abord les descripteurs structurels du graphe urbain :

* nombre de carrefours ( n ),
* nombre de routes ( m ),
* densité du graphe,
* degré moyen,
* autres indicateurs classiques de connectivité.

Ces variables décrivent la **morphologie physique** du réseau viaire. Elles renseignent sur l’architecture statique de la ville, indépendamment des flux.

### b) Variables spectrales – la structure dynamique (apport principal)

Mon apport principal réside dans l’introduction de **descripteurs spectraux** issus de l’analyse matricielle du graphe :

* rayon spectral,
* indice de Kreiss,
* valeurs singulières dominantes,
* métriques dérivées du spectre de la matrice d’adjacence ou des opérateurs associés.

Ces variables ne décrivent pas seulement la structure, mais le **comportement dynamique du réseau face aux flux**.

Par exemple, un indice de Kreiss élevé suggère une forte sensibilité transitoire : une perturbation locale (accident, ralentissement) peut générer un effet domino et provoquer une congestion à grande échelle. Autrement dit, ces métriques traduisent la *stabilité dynamique* du système urbain.

### c) Intérêt pour l’intelligence artificielle

Dans le cadre d’un modèle d’apprentissage automatique, ces quantités jouent le rôle de **descripteurs (features)**.

Elles permettent :

* de comparer deux villes dans un espace mathématique commun,
* d’abstraire complètement la représentation visuelle (carte, image satellite),
* de transformer un réseau urbain en un vecteur numérique exploitable par un algorithme.

Ainsi, la « signature urbaine » constitue l’interface formelle entre la théorie spectrale et l’apprentissage supervisé.

---

## 2. Pipeline d’entraînement : transformer les simulations en base d’apprentissage

Je dispose actuellement d’un ensemble d’environ dix simulations issues de SUMO, correspondant à différentes villes (Amsterdam, Berlin, Hanoi, etc.). L’objectif est de transformer ces simulations en données d’apprentissage structurées.

### a) Extraction des variables cibles (Ground Truth)

Pour chaque ville simulée, j’extrais les indicateurs globaux depuis les fichiers CSV :

* ( CO2_{total} ) : somme de la colonne CO2 sur toute la durée de la simulation,
* vitesse moyenne : moyenne temporelle de la colonne speed,
* éventuellement : temps de trajet moyen, densité moyenne, etc.

Ces valeurs constituent les **variables cibles (targets)** que le modèle devra apprendre à prédire.

### b) Association avec les métriques spectrales

Pour chaque ville, je calcule en parallèle les métriques issues de mon tableau de bord spectral :

* rayon spectral,
* indice de Kreiss,
* valeurs singulières,
* paramètres structurels (n, m, densité),
* nombre de véhicules injectés dans la simulation.

Je réalise ensuite une jointure entre :

* les indicateurs dynamiques extraits de SUMO,
* les descripteurs spectraux calculés à partir du graphe.

### c) Construction de la matrice d’apprentissage

On obtient alors une matrice structurée de type :

| Ville  | Rayon spectral | Indice de Kreiss | Nb véhicules | … | CO₂ total (Target) |
| ------ | -------------- | ---------------- | ------------ | - | ------------------ |
| Berlin | 1.45           | 12.4             | 5000         | … | 450 kg             |
| Hanoi  | 2.10           | 45.2             | 5000         | … | 890 kg             |
| …      | …              | …                | …            | … | …                  |

Cette matrice constitue la base d’entraînement supervisé :
les métriques spectrales sont les entrées,
les sorties de simulation sont les réponses à apprendre.

---

## 3. Phase de reconnaissance et comparaison structurelle

Avant même la prédiction des émissions, j’introduis une phase de **comparaison structurelle** entre villes.

L’idée est d’utiliser les vecteurs spectraux pour effectuer une analyse de similarité :

* Pour une nouvelle ville ( X ), je calcule sa signature spectrale.
* Je compare ce vecteur à ceux des villes déjà simulées.
* Je mesure une distance ou un taux de similarité (cosinus, distance euclidienne normalisée, etc.).

L’IA peut alors formuler une hypothèse du type :

> « La ville X présente une similarité structurelle élevée avec Paris ; son comportement dynamique face au trafic devrait être comparable. »

Cette étape joue un double rôle :

* validation scientifique de la cohérence des signatures,
* amélioration potentielle des prédictions par transfert implicite de comportement.

---

## 4. L’IA comme substitut partiel à SUMO : objectif scientifique final

L’objectif à long terme de mon travail est ambitieux :
**approcher, voire remplacer partiellement, les simulations lourdes de SUMO par un modèle prédictif instantané.**

### a) Limites de la simulation classique

Une simulation SUMO complète est :

* longue à paramétrer,
* coûteuse en ressources CPU,
* parfois instable pour des réseaux de grande taille,
* difficilement scalable à grande échelle.

Pour une grande ville, une simulation peut nécessiter plusieurs dizaines de minutes.

### b) Avantage du modèle d’IA

Une fois entraîné, un modèle d’apprentissage supervisé :

* produit une prédiction en quelques millisecondes,
* ne nécessite pas de recalcul dynamique complet,
* permet d’explorer rapidement différents scénarios.

### c) Protocole envisagé

Le protocole final que je souhaite mettre en place est le suivant :

1. Fournir à l’IA la carte d’une nouvelle ville (jamais simulée dans SUMO).
2. Extraire automatiquement ses métriques spectrales via mon pipeline d’analyse.
3. Positionner sa signature dans l’espace appris.
4. Produire une prédiction des émissions (ou autres indicateurs) que SUMO aurait calculées.

En résumé :

* Les données issues du laboratoire spectral constituent les **entrées**.
* Les résultats de simulation constituent les **sorties à apprendre**.
* Le modèle devient un estimateur rapide du comportement dynamique urbain.

---

## Conclusion et prochaine étape

La prochaine étape méthodologique consiste à :

* automatiser la fusion des fichiers CSV de simulation,
* les associer proprement aux métriques spectrales calculées,
* générer une base d’apprentissage consolidée et exploitable.

Cette étape est déterminante, car elle transforme un ensemble de simulations isolées en un corpus scientifique structuré permettant l’apprentissage statistique.
