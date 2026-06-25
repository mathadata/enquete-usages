# Publication des dashboards — process & registre

Les dashboards de l'enquête sont diffusés à **un seul endroit** : **GitHub Pages**
(branche `gh-pages`, lien public partageable). Une seule règle :

> **Source de vérité = les fichiers HTML du repo.**
> On n'édite **jamais** une copie publiée (gh-pages) directement.
> On édite la source, puis on **régénère** avec `publish_pages.sh`.

> ℹ️ **Les anciens Artifacts Claude sont retirés depuis le 24 juin 2026.** Ils ne font plus partie
> du processus de publication et ne doivent pas être recréés. Les anciennes GitHub Pages du dépôt
> dashboard redirigent durablement vers les URL canoniques ci-dessous.

## Registre des pages

| Page | Analyse | Fichier source (repo) | GitHub Pages |
|---|---|---|---|
| Accueil | portail | `enquete_usages_2026/pages/index.html` | [/](https://mathadata.github.io/enquete-usages/) |
| **Synthèse** | Synthèse transversale (à lire en premier) | `enquete_usages_2026/transverse/dashboard_synthese.html` | [/synthese.html](https://mathadata.github.io/enquete-usages/synthese.html) |
| **Typologie** | Cinq façons d'enseigner (profils, rétention) | `enquete_usages_2026/transverse/dashboard_typologie.html` | [/typologie.html](https://mathadata.github.io/enquete-usages/typologie.html) |
| **Séances** | Anatomie d'une séance (scénarios, rythmes, cas) | `enquete_usages_2026/transverse/dashboard_seances.html` | [/seances.html](https://mathadata.github.io/enquete-usages/seances.html) |
| **Volet 1** | Déploiement réel en classe (Capytale) | `enquete_usages_2026/usage-capytale/dashboard.html` | [/volet1.html](https://mathadata.github.io/enquete-usages/volet1.html) |
| **Volet 2** | Du site à la classe (mathadata.fr × Capytale) | `enquete_usages_2026/site-vers-classe/dashboard_volet2.html` | [/volet2.html](https://mathadata.github.io/enquete-usages/volet2.html) |
| **Flux** | Canal d'arrivée → réutilisation → retour (Sankey) | `enquete_usages_2026/transverse/dashboard_flux_profs.html` | [/flux.html](https://mathadata.github.io/enquete-usages/flux.html) |
| **URLR** | Canal sans compte Basthon (URLR × Capytale × site) | `enquete_usages_2026/usage-urlr/dashboard_urlr.html` | [/urlr.html](https://mathadata.github.io/enquete-usages/urlr.html) |

## Checklist à chaque modification d'un dashboard

1. **Éditer uniquement le fichier source** (colonne « Fichier source » ci-dessus). Pour Flux,
   ne pas éditer les chiffres à la main : ils sont **générés** par `build_flux_dashboard.py`
   depuis `facts_profiles.json`.
2. **Committer la source** sur `main` (`git add -A && git commit && git push`).
3. **Publier sur GitHub Pages** :
   ```bash
   bash enquete_usages_2026/publish_pages.sh
   ```
   Copie les 8 fichiers vers la branche `gh-pages`, commit (avec le SHA source dans le message)
   + push, sans `--force`. Idempotent (« déjà à jour, rien à publier » s'il n'y a rien de neuf).

C'est tout : **une seule surface, pas de double publication**.

## Notes

- GitHub Pages est servi depuis la branche **`gh-pages`** (racine), HTTPS forcé. Cette branche ne
  contient **que** les fichiers publiés + `.nojekyll` + `vercel.json` — elle est entièrement
  régénérée par le script, ne pas l'éditer.
- **Pas de dérive possible côté gh-pages** : son contenu vit dans le repo, donc diffable contre la
  source à tout moment (`git show gh-pages:flux.html` vs source). Le script ne pousse que s'il y a
  un diff.
- Avant publication, le script **refuse** de pousser si un email (hors `mathadata.fr`) apparaît dans
  une source (garde-fou anti-fuite de données personnelles).
- Pour ajouter une nouvelle page : ajouter le fichier source, une ligne dans le tableau `MAP` de
  `publish_pages.sh`, une carte dans `pages/index.html`, et une ligne dans ce registre.
