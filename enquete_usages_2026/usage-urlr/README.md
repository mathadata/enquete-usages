# Usage URLR — activités sans compte

Cette analyse reconstruit des séances Basthon estimées à partir des statistiques anonymes agrégées
URLR, puis les compare à Capytale et aux événements disponibles sur le site.

Les graphiques respectent le grain de la source :

- un **clic URLR** n'est ni une personne, ni un professeur, ni un élève, ni une séance ;
- `unique_visits` est recalculé par URLR sur chaque fenêtre complète de séance et n'est jamais
  obtenu en sommant les uniques horaires ou quotidiens ;
- les uniques de plusieurs liens ne sont pas dédupliqués entre eux ;
- le nombre de clics par salve est publié comme proxy collectif exploratoire, probablement plus
  informatif derrière un NAT, mais jamais comme nombre d'élèves mesuré ;
- une séance URLR est un proxy de salve de navigateurs, pas une classe certaine ;
- les modes remplacement/dépannage sont des compatibilités temporelles, pas des attributions.

## Régénération

Depuis la racine du dépôt :

```bash
python3 enquete_usages_2026/usage-urlr/make_charts.py
```

La reconstruction canonique est lancée par `rebuild_all.sh`. Le fetch réseau reste indépendant :

```bash
python3 enquete_usages_2026/fetch_urlr.py
```

Les faits à lire plutôt que recalculer sont dans `data/facts_urlr*.json`. La méthode et les résultats
sont synthétisés dans [`RAPPORT_USAGE_URLR.md`](RAPPORT_USAGE_URLR.md).

Page web autonome :

```bash
python3 enquete_usages_2026/usage-urlr/build_dashboard.py
```

Source : `dashboard_urlr.html` · publication canonique : `/urlr.html`.

## Graphiques

1. `charts/01_clics_quotidiens.png` — volume journalier et moyenne mobile sur 7 jours ;
2. `charts/02_calendrier_des_clics.png` — calendrier des jours actifs et des principaux pics ;
3. `charts/03_clics_mensuels_par_activite.png` — composition mensuelle par activité ;
4. `charts/04_volume_et_portee_par_activite.png` — clics et visites uniques par lien.
5. `charts/05_seances_urlr_vs_capytale.png` — Capytale vs seuils URLR en uniques et en clics ;
6. `charts/06_modes_remplacement_depannage.png` — classification stricte, ±1 h et sensibilité clics ;
7. `charts/07_funnel_site_urlr.png` — points observables du site jusqu'aux séances URLR.

Source et schéma : [`../DONNEES_BRUTES_URLR.md`](../DONNEES_BRUTES_URLR.md).
