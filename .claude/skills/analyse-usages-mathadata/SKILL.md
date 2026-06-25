---
name: analyse-usages-mathadata
description: Répondre aux questions d'analyse sur les usages MathAData dans enquete_usages_2026, y compris URLR/Basthon, les croisements site–Capytale et les demandes nominatives internes. Utiliser cette skill dès qu'une demande mentionne des profs, usages, activités, classes, formations, canaux, retours, cohortes, données Payload/Capytale/URLR, noms ou e-mails.
---

# Analyse des usages MathAData

## But

Produire une réponse reproductible sans inventer de catégorie, sans mélanger les grains et sans
faire sortir de données personnelles du périmètre local autorisé.

## Ordre de lecture obligatoire

1. Lire `enquete_usages_2026/transverse/GLOSSAIRE.md`.
2. Lire `CLAUDE.md` §10-11.
3. Lire [references/clarification.md](references/clarification.md).
4. Pour une demande nominative ou un croisement individuel, lire aussi
   [references/mode-nominatif-local.md](references/mode-nominatif-local.md).

## Disponibilité des données dans un clone

- **Sans PII, déjà versionné** (répondre directement, ne pas exiger de snapshot) : les tables
  canoniques `transverse/data/profiles_teacher*.csv`, `usage-capytale/data/{usages_enriched,sessions,
  teachers}.csv`, l'appariement pseudonymisé `site-vers-classe/data/match_candidates.csv`, l'entrée
  brute `public/data/capytale_fresh_*.csv` (schéma : `enquete_usages_2026/DONNEES_BRUTES_CAPYTALE.md`),
  les extractions URLR `public/data/urlr_{links,daily,hourly,bursts}_*.csv`, la table canonique
  `usage-urlr/data/sessions.csv` et tous les `facts_*.json`. La plupart des questions Capytale,
  URLR, canal, formation, profondeur et rétention se répondent **sans** le snapshot
  (canal/formation sont **pré-calculés** dans `profiles_teacher.csv`).
- **Avec PII, strictement local** : le snapshot Payload (noms/prénoms/e-mails) n'est **pas** dans le
  clone. Toute question nominative (noms, e-mails) ou tout nouveau croisement individuel l'exige.
  S'il est absent, ne pas inventer : indiquer qu'il manque et renvoyer à
  [`enquete_usages_2026/MISE_A_JOUR_DONNEES.md`](../../../enquete_usages_2026/MISE_A_JOUR_DONNEES.md)
  (récupération via le dépôt voisin `mathadata-website`, variable `MATHADATA_SNAPSHOT`).
  **Ne pas relancer tout le pipeline pour une simple demande nominative** :
  - question portant uniquement sur le site → lire directement
    `$MATHADATA_SNAPSHOT/users.json` ;
  - noms/e-mails à rattacher aux profils Capytale existants → exécuter seulement
    `python3 enquete_usages_2026/site-vers-classe/match_individuals.py --local-only`, puis lire
    `_local/match_nominatif.csv`.
  `rebuild_all.sh` ne sert que si l'utilisateur demande d'actualiser ou recalculer les analyses.

## Workflow

1. Reformuler l'interprétation opérationnelle : population, période, événement, seuil, grain,
   dénominateur et sensibilité de la sortie.
2. Appliquer le protocole de clarification. Ne poser une question que si plusieurs interprétations
   plausibles changent matériellement le résultat.
3. Chercher le résultat dans les `facts_*.json`, puis dans les tables canoniques. Ne pas recalculer
   un fait existant.
4. Si un calcul ad hoc est nécessaire, le faire dans `/tmp` ou `enquete_usages_2026/_local/`.
   Une variable durable de profil doit être ajoutée à `transverse/build_profiles.py`.
5. Contrôler les exclusions, le grain et les bornes temporelles. Tout lien site–Capytale est
   estimé ; donner la couverture et la confiance utilisées.
6. Répondre avec quatre blocs courts : **Interprétation**, **Résultat**, **Base et méthode**,
   **Limites**. Pour une liste nominative, ajouter **Destination et confidentialité**.

## Listes nominatives : règle stricte

- `formation_source=proxy_etab` est une attribution écologique utile aux agrégats, **jamais une
  identité nominative**. Ne pas transformer le compte formé d'un établissement en candidat nominal
  pour chacun des profils Capytale de cet établissement.
- Le nombre de profils marqués `formation_statut=forme` ne doit pas être présenté comme un nombre
  de contacts identifiés. Toujours séparer :
  1. profils formés au sens agrégé ;
  2. profils avec appariement individuel A/B ;
  3. personnes nominatives uniques effectivement attribuables.
- Une liste de noms/e-mails issue d'un croisement site–Capytale contient par défaut uniquement les
  appariements individuels A/B. Les proxies établissement sont signalés comme **non identifiables**
  et ne sont pas développés en hypothèses nominatives, sauf demande explicite d'une enquête manuelle
  exploratoire.
- Avant d'inclure même un appariement A/B dans une liste ciblée par comportement, contrôler les
  conflits visibles : activités cliquées contre activités déployées, ordre clic→déploiement,
  proximité temporelle, meilleur profil concurrent au même établissement et comptes site multiples
  d'une même personne. En cas de meilleur concurrent ou de contradiction avec le comportement
  demandé, exclure la personne de la liste principale et documenter le cas comme ambigu.

## Règles de décision

- Si les mots de l'utilisateur correspondent sans ambiguïté au glossaire, annoncer cette lecture
  et calculer.
- Si une expression est proche d'un terme canonique mais différente, ne pas les assimiler.
  Exemple : « plusieurs activités différentes » n'est pas automatiquement « usage multiple »,
  qui autorise plusieurs occasions de la même activité.
- Si la catégorie demandée n'existe pas, proposer soit la catégorie canonique la plus proche, soit
  une catégorie exploratoire explicitement nommée. Ne pas modifier le glossaire sans demande.
- Si les données nécessaires sont absentes du clone, l'indiquer précisément. Ne pas remplacer une
  absence par une hypothèse silencieuse.
- Ne jamais présenter un appariement nominatif site–Capytale comme certain. Séparer les résultats
  mesurés sur le site des résultats issus d'un appariement A/B.
- Pour URLR, lire en priorité `usage-urlr/data/facts_urlr*.json`, jamais recalculer les visiteurs
  uniques en sommant les heures ou les jours. Une taille URLR se nomme
  `n_visiteurs_uniques_urlr`, jamais `n_eleves`. L'API ne documente pas sa clé d'unicité et URLR
  traite les statistiques avec des IP anonymisées : une IP/NAT d'établissement peut sous-compter
  un groupe. Lire les seuils de taille comme des détections conservatrices. Le nombre de clics par
  salve peut servir de proxy collectif exploratoire si les réouvertures sont rares ; il ne devient
  jamais `n_eleves` et doit rester séparé des seuils canoniques fondés sur les uniques.
- Les modes historiques `compatible_remplacement` et `compatible_depannage` sont des indices
  temporels nationaux, jamais une attribution certaine à une classe. La sensibilité ±1 h reste
  séparée de la classification stricte, comme la sensibilité fondée sur les clics.
- Un clic Payload « accès Basthon direct » peut fournir un candidat nominatif historique, jamais
  l'auteur attribué d'une salve URLR : ce geste prouve une consultation/test, pas une copie.
- Une attribution prospective URLR au niveau professeur exige une copie candidate unique et un
  appariement individuel site–Capytale A/B. Ne jamais utiliser `proxy_etab`.
- Ne jamais produire une liste de noms à partir de `proxy_etab`. Un proxy peut soutenir un chiffre
  agrégé, pas identifier le collègue concerné.

## Interdictions

- Ne jamais écrire nom, prénom, e-mail ou identifiant Payload dans un fichier suivi par Git, un
  dashboard, un rapport publiable, un log versionné ou une sortie de CI.
- Ne jamais publier une table nominative, même pseudonymisée si la table permet une réidentification
  raisonnable par croisement.
- Ne jamais utiliser `n_teacher_clones` comme nombre de profs.
- Ne jamais mélanger réutilisation intra-annuelle et retour interannuel.
- Ne jamais appeler « absence de trace site » une preuve certaine d'arrivée directe par Capytale.
