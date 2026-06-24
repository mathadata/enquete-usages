# Enquêtes usages MathAData

Ce dépôt public contient les analyses reproductibles des usages MathAData, leurs définitions
canoniques, données pseudonymisées, rapports et pages GitHub Pages.

- [Enquête usages 2026](enquete_usages_2026/README.md)
- [Glossaire canonique](enquete_usages_2026/transverse/GLOSSAIRE.md)
- [Guide de prise en main](POUR_DEMARRER.md)
- [Pages publiées](https://mathadata.github.io/enquete-usages/)

## Vérifier ou reconstruire

```bash
python3 -m pip install -r requirements.txt
git config core.hooksPath enquete_usages_2026/hooks
python3 enquete_usages_2026/transverse/check_contracts.py
bash enquete_usages_2026/rebuild_all.sh
```

Les étapes nécessitant des données nominatives utilisent uniquement un snapshot Payload local,
jamais versionné. Voir
[`enquete_usages_2026/MISE_A_JOUR_DONNEES.md`](enquete_usages_2026/MISE_A_JOUR_DONNEES.md).

## Dépôts liés

- Dashboard interactif Next.js : [`akimx98/mathadata-dashboard-next`](https://github.com/akimx98/mathadata-dashboard-next)
- Pipeline institutionnel ETL/dbt : `mathadata/mathadata-analytics` (privé)
- Site MathAData : `mathadata/mathadata-website` (privé)

Les calculs historiques du dashboard Next.js ne constituent pas la source de vérité de cette
enquête. Leur alignement avec le glossaire canonique est un chantier distinct.
