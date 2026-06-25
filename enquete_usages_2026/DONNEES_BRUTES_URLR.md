# Données URLR — schéma & provenance

Source d'usage **anonyme et agrégée** des liens courts qui ouvrent les activités MathAData sans
compte ENT. Dans l'extraction actuelle, ces liens redirigent vers les notebooks Basthon équivalents
aux activités proposées sur Capytale.

- **Fichiers de référence versionnés** :
  - `public/data/urlr_links_20260625.csv` — 1 ligne par lien, métadonnées utiles et totaux ;
  - `public/data/urlr_daily_20260625.csv` — 1 ligne par lien × jour de Paris avec activité non nulle.
  - `public/data/urlr_hourly_20260625.csv` — 1 ligne par lien × heure de Paris avec activité non nulle.
  - `public/data/urlr_bursts_20260625.csv` — 1 ligne par salve reconstruite, avec les uniques
    recalculés par URLR sur sa fenêtre complète.
- **PII** : aucune dans les fichiers. L'API renvoie un champ `user` contenant l'e-mail du créateur ;
  le script l'exclut, ainsi que `workspace_id` et `folder_id`.
- **Couverture actuelle** : 6 liens créés le 25 décembre 2025. URLR ne fournit ici aucune identité de
  visiteur ni événement individuel.

## Schémas

### `urlr_links_*` — 1 ligne = 1 lien court

| Colonne | Sens |
|---|---|
| `link_id` | UUID technique URLR du lien |
| `short_url`, `code`, `label` | lien court public et libellé |
| `mathadata_id`, `mathadata_title` | activité canonique commune aux statistiques URLR et Capytale |
| `resource_slug` | portion du libellé après le préfixe `basthon:` |
| `destination_url` | URL Basthon complète |
| `notebook_source_url` | notebook public extrait du paramètre `from` de l'URL Basthon |
| `created_at`, `updated_at` | dates ISO-8601 renvoyées par URLR |
| `window_start`, `window_end` | fenêtre exacte utilisée pour les statistiques |
| `visits`, `unique_visits`, `clicks`, `scans` | métriques agrégées renvoyées par l'API URLR |
| `extracted_at` | coupure figée au début de l'extraction |

### `urlr_daily_*` — 1 ligne = 1 lien × 1 jour de Paris non nul

Les fenêtres sont des journées civiles en `Europe/Paris`, avec une dernière journée éventuellement
partielle arrêtée à `extracted_at`. Une ligne absente signifie zéro `visit`, `click` et `scan`.
`unique_visits` est calculé par URLR **dans chaque fenêtre** : il ne faut pas sommer cette colonne
pour obtenir le nombre d'un mois ou de toute la période.

### `urlr_hourly_*` — 1 ligne = 1 lien × 1 heure de Paris non nulle

C'est la granularité temporelle maximale documentée par URLR. `hour_start` et `hour_end` incluent
l'offset UTC, ce qui distingue correctement les heures répétées lors du passage à l'heure d'hiver.
Comme pour le quotidien, `unique_visits` est propre à chaque fenêtre et non additionnable.

### `urlr_bursts_*` — 1 ligne = 1 séance Basthon estimée

Les heures actives d'un même lien sont fusionnées tant que les débuts successifs sont espacés de
moins de 3 h. Le script requête ensuite URLR sur la fenêtre complète obtenue : la colonne
`unique_visits` n'est donc jamais une somme d'uniques horaires. `burst_id` est un identifiant
technique stable dans l'extraction ; `active_hours` compte les heures actives fusionnées.

La table canonique dérivée `usage-urlr/data/sessions.csv` ajoute le chevauchement Capytale strict,
la sensibilité ±1 h et les modes `compatible_remplacement`, `compatible_depannage` ou
`indetermine`. Ces modes sont des indices temporels agrégés nationaux, pas des attributions.

## Mapping vers les activités MathAData/Capytale

Le mapping versionné [`urlr_activity_mapping.csv`](urlr_activity_mapping.csv) relie chacun des six
codes URLR au `mathadata_id` et au titre canonique Capytale. Le fetch refuse de produire une
extraction si un nouveau lien URLR n'a pas encore été rattaché ou si son libellé a changé.

Les quatre tables produites répètent `mathadata_id` et `mathadata_title` : les analyses parlent donc
le même langage que Capytale et n'ont pas à joindre sur un libellé approximatif.

## Pourquoi il n'existe pas de table « une ligne = un clic »

Les API publiques URLR v1 et v2 ne renvoient qu'un compteur sur une fenêtre temporelle. Elles
n'exposent aucun journal événementiel, aucune IP, aucun timestamp individuel, aucun navigateur,
OS, référent ou pays par clic.

URLR indique par ailleurs que les IP utilisées pour les statistiques sont anonymisées. Son produit
affiche des ventilations agrégées de localisation, navigateur, OS et référent, et certains
abonnements permettent un export CSV analytique depuis l'interface. En revanche, l'export granulaire
« une ligne par clic » est encore une demande de fonctionnalité publique marquée « In Review ».
La clé API seule ne permet donc pas de récupérer ces dimensions.

Références officielles vérifiées le 25 juin 2026 :

- [API v2 — endpoint agrégé `GET /statistics`](https://docs.urlr.me/api-reference/v2/) ;
- [API v1 — endpoint agrégé `POST /statistics`](https://docs.urlr.me/en/api-reference/v1/) ;
- [statistiques disponibles dans le produit](https://urlr.me/en/features/statistics) ;
- [IP anonymisées et absence de ciblage](https://urlr.me/en/gdpr-compliance) ;
- [exports CSV selon l'abonnement](https://urlr.me/en/plans/pricing) ;
- [demande d'export granulaire par clic — statut “In Review”](https://feedback.urlr.me/p/granular-statistic-data-export).

## Provenance & rafraîchissement

- API officielle : `https://urlr.me/api/v2`
- Authentification : en-tête `X-API-KEY`
- Documentation : <https://docs.urlr.me/api-reference/v2/>
- Script canonique : [`fetch_urlr.py`](fetch_urlr.py)

La clé se nomme `URLR_API_KEY` et vit dans `.env.local` à la racine du dépôt, fichier ignoré par Git.

```bash
python3 enquete_usages_2026/fetch_urlr.py
```

Le script :

1. pagine tous les liens par lots de 50 ;
2. fixe une coupure temporelle unique au début de l'extraction ;
3. récupère les totaux et les fenêtres quotidiennes en heure de Paris ;
4. détaille chaque jour actif par heure ;
5. contrôle que les métriques additives horaires et quotidiennes (`visits`, `clicks`, `scans`)
   égalent les totaux de la même fenêtre ;
6. fusionne les heures en salves et recalcule leurs visiteurs uniques sur la fenêtre complète ;
7. écrit les quatre CSV datés sans écraser une extraction existante.

Cette source décrit un **volume d'ouverture par activité**, pas des professeurs ni des classes.
Historiquement, seul un rapprochement temporel national est possible. Après déploiement du tracking
de copie côté site, une attribution restera inférée et limitée aux copies candidates uniques et aux
appariements individuels site–Capytale A/B existants.
