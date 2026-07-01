# CLAUDE.md — dépôt `mathadata/enquete-usages`

Ce dépôt public contient les enquêtes reproductibles sur les usages MathAData, leurs données
pseudonymisées, rapports et pages publiées. L'application interactive Next.js vit séparément dans
`akimx98/mathadata-dashboard-next`.

# Enquête usages — playbook d'exploration des données

> **À lire avant toute analyse de données MathAData** (toi, future session, ou collègue).
> Quand on te demande « explore les données / calcule X / fais un graphe », commence ici.

## 1. La règle nº 1 : les définitions sont canoniques et centralisées

**[`enquete_usages_2026/transverse/GLOSSAIRE.md`](enquete_usages_2026/transverse/GLOSSAIRE.md) est la
source de vérité de TOUTES les définitions** (année scolaire, prof, séance, classe, profondeur
d'usage, canal, formation, rétention, niveau…). **Ne JAMAIS** redéfinir un terme localement ni
inventer un seuil. Si un calcul a besoin d'une notion, elle doit déjà être dans le glossaire ; sinon,
**on l'ajoute au glossaire d'abord**, puis on calcule. En cas de divergence entre un rapport et le
glossaire, **le glossaire gagne** (le rapport est à corriger).

Les `DEFINITIONS.md` / `DEFINITIONS_VOLET2.md` ne contiennent que les **spécificités de source**
(chemins, schémas, quirks) et **pointent** vers le glossaire pour le sens.

## 2. La couche de calcul canonique

Les variables dérivées par prof naissent dans **un seul** module :
**[`enquete_usages_2026/transverse/build_profiles.py`](enquete_usages_2026/transverse/build_profiles.py)**
→ produit `transverse/data/profiles_teacher_year.csv` (prof × année), `profiles_teacher.csv` (attributs
figés + rétention), `facts_profiles.json` (agrégats = source de vérité des chiffres du dashboard Flux).
**Toute nouvelle variable « profil » s'ajoute là**, pas dans un script ad hoc du scratchpad.
`reconcile_facts.py` → `facts_reconciliation.json` recalcule les figures récurrentes des rapports
sur la base canonique (+ écarts ≥5/≥10) : c'est la **fiche de référence chiffrée** pour vérifier/citer.

## 3. Les deux mondes (le piège structurant)

Deux sources **disjointes**, sans clé commune directe :
- **Capytale** (`public/data/capytale_fresh_20260619.csv`) — usage en classe, **anonyme** (MD5).
  Couvre 2023→2026.
- **mathadata.fr / Payload** — parcours amont, **nominatif**, snapshot **local & gitignore** dans
  `../mathadata-website/private/payload-snapshots/<timestamp>/` (repo voisin). Par défaut, les scripts
  prennent le dossier horodaté le plus récent ; définir `MATHADATA_SNAPSHOT` fige une extraction. Le
  tracking des clics ne commence que **~27 nov 2025** (avant : clics invisibles → ne pas conclure
  « pas d'intérêt »).

Le pont : un clic site `web/b/<id>` → `<id> == mathadata_id` Capytale. Sinon, **appariement
individuel inféré** (signaux A/B/D/E, 70 paires) + **trace établissement**. Tout ce qui relie les deux
mondes est **estimé**, jamais mesuré — le dire explicitement.

Source complémentaire **URLR** : statistiques anonymes agrégées des liens courts vers les activités
sans compte (actuellement Basthon), disponibles depuis le 25/12/2025. Aucun visiteur ou
établissement n'est identifiable. Des séances sont **estimées** au grain activité × temps ; leurs
rapprochements Capytale historiques restent nationaux et inférés. Entrées :
`public/data/urlr_{links,daily,hourly,bursts}_*.csv`, produites par `fetch_urlr.py`. Le mapping
canonique vers `mathadata_id` vit dans `enquete_usages_2026/urlr_activity_mapping.csv`.
`unique_visits` est une métrique de fenêtre non additive dont la clé de déduplication n'est pas
documentée ; les IP étant anonymisées, une IP/NAT d'établissement peut sous-compter une classe.
Les clics par salve sont donc aussi exposés comme proxy collectif exploratoire, sans jamais être
assimilés à des élèves. Un clic Payload sur l'accès Basthon direct ne prouve pas une copie du lien
court : il ne peut produire qu'un candidat nominatif interne, jamais une attribution publiée.

## 4. Pièges à connaître (déjà payés — ne pas refaire)

- **`n_teacher_clones` / `n_teacher_accounts` ≠ nombre de profs.** Ces colonnes ne comptent que les
  auto-tests `role=teacher`. **59 % des profs (133/224) n'en créent jamais** (« plongée directe »).
  Pour compter les profs : `distinct(teacher)` sur les lignes `role=student`.
- **Circularité rétention.** La réutilisation (intensité) est **strictement intra-annuelle**. Compter
  une activité/séance d'une autre année rend « réutiliser ⇒ revenir » tautologique. Le retour se
  mesure **entre** années, séparément. (Cf. l'audit qui a invalidé le « 76 % vs 16 % » carrière.)
- **Deux seuils « classe », à ne jamais confondre** (glossaire §3) : **usage-classe = ≥ 5 él.**
  (seuil canonique, 176 profs — gouverne profondeur/rétention/funnels) vs **séance riche / classe
  entière = ≥ 10 él.** (mode-cible de qualité, 150 profs — KPI/prédicteur, pas un seuil d'entonnoir) ;
  **grande classe = ≥ 20** (82). Un « ≥ 10 » dans un rapport = *séance riche*, jamais « la classe ».
- **Hub fondateur** `cfcd2084…` (MD5 "0") : 404 élèves sur 14 établissements → **isoler**, jamais
  un prof local. **Compte démo** `c81e728d…` (MD5 "2") → **exclure**.
- **`ancienne_vague`** (147 formés avant le système de codes du 15/01/26) : type & date **inconnus**,
  ne pas les compter comme webinaire.
- **Récence des cohortes** : lire au présent une cohorte formée en 2026 sous-estime son rendement
  (le déploiement classe se fait au trimestre suivant). Toujours distinguer cohorte mûre / récente.

## 5. Pipeline (ordre de calcul) — **une seule commande**

```
bash enquete_usages_2026/rebuild_all.sh
```
Régénère la **chaîne de calcul canonique** dans l'ordre (Capytale → croisé site×Capytale → couche
profils → scénarios → réconciliation → **dashboard Flux généré**), puis lance les contrats. Les étapes
croisées (snapshot Payload LOCAL) sont auto-sautées si le snapshot/`_local/` est absent ; **idempotent**
(re-run = aucune dérive ; vérifié stable sous `PYTHONHASHSEED` variable). Ordre détaillé dans le script.
Les `data/*.json` (`facts*.json`) sont les **sources de vérité chiffrées** — un dashboard ne recalcule pas,
il **lit** ces faits.

> ⚠️ **Ce que `rebuild_all` ne régénère PAS** (et pourquoi) : (a) les **enquêtes multi-agents** one-shot
> et non déterministes — `facts_investigation.json` (base élargie n≈101, cf. son `_meta`), `SEC_*`,
> `sections_final.json` — se rejouent en relançant leur `workflow_*.js`, pas le pipeline ; (b) les
> **graphiques** (`make_charts*.py`) ; (c) les **dashboards à chiffres en dur** autres que Flux (typologie/
> volet2/synthèse/séances — reportés à la main, mais leur concordance est **contrôlée** par les contrats) ;
> (d) les **rapports `.md`** (rédigés). La rétention **canonique** (77/26/33,8 %) vit dans
> `facts_typologie.json` (régénéré), jamais dans `facts_investigation.json`.

> 🔑 **Régénérer un `workflow_*.js` exige d'activer « ultracode ».** Ces `workflow_*.js`
> (`site-vers-classe/workflow_volet2.js`, `transverse/workflow_typologie.js`) sont des scripts de
> **l'outil Workflow** de Claude Code : ils appellent `agent()`/`pipeline()` et lancent des
> **sous-agents**. Or Claude n'orchestre des multi-agents que sur **opt-in explicite** — mot-clé
> **`ultracode`** dans la demande, ultracode activé pour la session, ou « lance le workflow …js ».
> **Sans cet opt-in, la régénération de ces artefacts one-shot est bloquée** (Claude ne lancera pas
> l'orchestration) — c'est normal, pas un bug. Le pipeline déterministe (`rebuild_all.sh`, Python
> pur) et `check_contracts.py` n'en ont **pas** besoin. ⚠️ Détail d'exécution : ces scripts découvrent
> le snapshot via `node:fs` ; l'outil Workflow n'a pas d'accès disque → exécuter une **copie adaptée**
> où le chemin du snapshot est injecté en dur (retirer `import fs`), puis écrire les sorties depuis la
> valeur de retour du workflow. Contrôler l'**absence de PII** (noms/e-mails) dans les `.md`/`.json`
> régénérés avant tout commit : les contrats ne scannent la PII que dans les `.csv`.

**Socle partagé** : `enquete_usages_2026/enquete_common.py` (= `K`) — **source unique** des constantes
(`DEMO`/`PIO`, seuils `CLASSE_MIN`…, populations nommées `K.EXPECT`), de `school_year`, `exclude_special`,
`sanitize_json`. **Tout script importe K** ; on ne redéfinit JAMAIS une exclusion ou un seuil localement
(c'est ce qui causait « hub oublié dans le script N »).

**Contrats anti-régression** — `python3 enquete_usages_2026/transverse/check_contracts.py` :
JSON **strict** (NaN/Inf réellement rejetés), invariants population/rétention **ancrés sur `K.EXPECT`**
(260/223/176/47/37/77), pseudonymat md5[:8], hub isolé (profils+scénarios+typologie), cohérence interne
`facts_typologie`, concordance **dashboards↔facts**, zéro e-mail dans `data/`. Doit finir par
`✅ tous les contrats sont respectés`.
- **Exécutés automatiquement** : (a) **hook pre-commit** versionné — installer une fois :
  `git config core.hooksPath enquete_usages_2026/hooks` (un commit qui casse un contrat est refusé) ;
  (b) **CI GitHub active** dans `.github/workflows/contrats-enquete.yml`. Le fichier
  `enquete_usages_2026/hooks/github-workflow-contrats.yml.template` est conservé comme modèle de secours.

⚠️ **Les dashboards `.html` embarquent leurs chiffres en dur** (HTML autonome, CSP-safe : pas de
`fetch` possible). Deux régimes :
- **Flux** : **généré depuis les facts** par `build_flux_dashboard.py` (remplit les `<span data-f>`
  + l'îlot `F` des Sankeys depuis `facts_profiles.json`). Après `build_profiles.py`, relancer
  `build_flux_dashboard.py` → la page est à jour automatiquement.
- **Autres dashboards** (typologie, volet2, synthèse, séances, volet1) : chiffres **encore en dur**
  → après un recalcul, reporter les nombres à la main. `check_contracts.py` (§ ci-dessus) **vérifie
  la concordance** dashboards↔facts et casse si ça diverge (filet anti-oubli).

## 6. Publication (ne jamais diverger)

Voir **[`enquete_usages_2026/PUBLISH.md`](enquete_usages_2026/PUBLISH.md)**. **Une seule surface :
GitHub Pages**. Les anciens Artifacts Claude ne sont plus maintenus depuis le 24 juin 2026.
Source de vérité = les fichiers HTML du repo ; on édite la source
puis on régénère **gh-pages** (`bash enquete_usages_2026/publish_pages.sh`) — jamais l'inverse. Pas de
dérive possible : le contenu gh-pages vit dans le repo (diffable contre la source). Le script **refuse**
de publier si un e-mail non-`mathadata.fr` apparaît dans une source.

## 7. Sécurité (NON NÉGOCIABLE)

- **Aucun** nom / prénom / e-mail dans le repo git **ni** dans les artefacts publiés. Pseudonymes
  `S####` (site) / `md5[:8]` (Capytale), grain établissement/commune.
- Le snapshot Payload reste **local & gitignore**, **jamais committé**. Les fichiers de travail
  nominatifs (ex. `enquete_usages_2026/_local/match_nominatif.csv`, docs `private/`) **ne sortent
  jamais** du local.
- Une analyse nominative interne est permise **uniquement sur demande explicite**, depuis les
  sources locales autorisées. Toute sortie fichier va dans `enquete_usages_2026/private/` ou
  `enquete_usages_2026/_local/`, après vérification avec `git check-ignore -q <chemin>`.
- **Une demande nominative n'implique pas une reconstruction des analyses.** Avec
  `MATHADATA_SNAPSHOT` défini :
  - pour des noms/e-mails ou attributs uniquement côté site, lire directement
    `$MATHADATA_SNAPSHOT/users.json` ;
  - pour rattacher des identités aux profils Capytale déjà versionnés, exécuter seulement
    `python3 enquete_usages_2026/site-vers-classe/match_individuals.py --local-only`, qui écrit
    `_local/match_nominatif.csv` sans modifier les faits ou profils versionnés.
  Ne lancer `rebuild_all.sh` que pour actualiser/recalculer les analyses sur de nouvelles données.
- Une identité côté site est mesurée ; une identité reliée à Capytale est **inférée**. Pour toute
  liste issue du pont site↔Capytale, conserver/indiquer la confiance A/B et ne jamais présenter
  l'attribution comme certaine.
- Avant de terminer une analyse nominative : vérifier `git status --short` et qu'aucune donnée
  personnelle n'a été ajoutée aux fichiers suivis. Marquer la sortie « usage interne — données
  personnelles — ne pas publier ».

## 8. Git (préférence du mainteneur)

**Pas de PR sur ce repo** : commits directs sur `main`, ou auto-merge en fin de tâche après
relecture. Messages de commit en français, scope `(enquête)`.

## 9. Structure (cadre mental)

Historiquement « volet 1 / volet 2 », mais le bon cadre est : **une synthèse transversale + des
analyses qui répondent à des questions différentes** (mêmes définitions canoniques, mêmes données) —
voir `enquete_usages_2026/README.md`. À lire en premier : `transverse/SYNTHESE_FINALE_2026.md`.

## 10. Répondre à une question d'analyse (mode d'emploi)

Appliquer la skill **`.claude/skills/analyse-usages-mathadata/SKILL.md`** à toute question
d'analyse sur `enquete_usages_2026/`, notamment si elle demande des noms/e-mails ou un croisement
site↔Capytale.

Quand on te pose une question sur les données, **dans l'ordre** :
1. **Lis le glossaire** (`transverse/GLOSSAIRE.md`) — vérifie le sens exact des termes en jeu
   (classe ≥5 vs séance riche ≥10, profondeur, canal, rétention, réutilisation intra-annuelle).
2. **Explicite le contrat de calcul** : population, période, événement, seuil, grain, dénominateur,
   exclusions et niveau de confidentialité. Si le glossaire tranche, annonce l'interprétation et
   continue. Si plusieurs lectures plausibles changent matériellement le résultat, pose **une**
   question concise en proposant d'abord l'option canonique. Si la catégorie demandée n'existe pas,
   ne l'invente pas silencieusement : proposer la catégorie canonique la plus proche ou une
   catégorie exploratoire explicitement nommée.
3. **Cherche d'abord la réponse dans les `facts_*.json`** (sources de vérité chiffrées) et les
   tables `data/` — **ne recalcule pas** ce qui existe déjà. Voir la carte §11.
4. **Si la réponse n'existe pas**, calcule-la **depuis les tables canoniques** (`profiles_*`,
   `usages_enriched`, `sessions`, `teachers`), **jamais** en redéfinissant un terme. Une analyse
   jetable → `/tmp` ou `_local/`. Une variable réutilisable → **ajoute-la à `build_profiles.py`**
   et relance (ne crée pas un n-ième script ad hoc).
5. **Cite toujours la base** (seuil, dénominateur, cohorte, année) — c'est là que naissent les
   divergences. Précise « usage-classe ≥5 » vs « séance riche ≥10 », « an-1 seulement », « cohorte
   éligible n=77 », etc.
6. **Ne change un chiffre publié que via la source** (rapport `.md` / dashboard `.html` du repo),
   puis régénère `gh-pages` (§6). Jamais d'édition directe d'une copie publiée.
7. **Garde-fous** : population = exclure démo (MD5 "2") et isoler le hub fondateur (MD5 "0") ;
   profs = `distinct(teacher)` sur lignes `role=student` ; tout lien site↔Capytale est **estimé**.
8. **Forme de réponse** : `Interprétation` → `Résultat` → `Base et méthode` → `Limites`. Pour une
   sortie nominative, ajouter `Destination et confidentialité`.

## 11. Carte des données (où trouver quoi)

**Tables canoniques** (1 ligne = …) :

| Fichier | Grain | Sert à |
|---|---|---|
| `usage-capytale/data/usages_enriched.csv` | 1 affectation Capytale (clone) | base brute enrichie (rôle, activité, UAI, `sy`, dates, `session_id`) |
| `usage-capytale/data/sessions.csv` | 1 séance reconstruite | tailles de classe (`n_eleves`), durées, rythmes |
| `usage-urlr/data/sessions.csv` | 1 séance Basthon estimée | uniques URLR par fenêtre, chevauchements Capytale, modes compatibles |
| `usage-capytale/data/teachers.csv` | 1 prof (md5) | comportement test/enseigne, UAI, années actives/enseignées |
| `usage-capytale/data/establishments.csv` | 1 UAI | géo/IPS/secteur, agrégats établissement |
| `transverse/data/profiles_teacher.csv` | 1 prof (md5[:8]) | **★ profil canonique** : niveau, canal, formation×timing, rétention |
| `transverse/data/profiles_teacher_year.csv` | 1 (prof × année) | **★ profondeur par année** (escalier 0-5), classes/occasions |
| `site-vers-classe/data/match_candidates.csv` | 1 paire site↔Capytale (75) | appariement individuel (sans PII : `S####` ↔ `md5[:8]`) |
| `site-vers-classe/data/capytale_by_uai_*.csv` | 1 UAI | usage Capytale par établissement (deux portes) |
| `transverse/data/master_teachers.csv`, `scenarios_teachers.csv` | 1 prof | substrats typologie (archétypes par règles déterministes) & séances |

**Faits chiffrés** (`*.json`, sources de vérité — lire, pas recalculer) :

| Fichier | Contenu |
|---|---|
| `transverse/data/facts_profiles.json` | **★ profils/flux** : canal, profondeur, rétention (n=77→34 %), trajectoires |
| `transverse/data/facts_reconciliation.json` | **★ fiche de réconciliation** : toutes les figures récurrentes + écarts ≥5/≥10 |
| `usage-capytale/data/facts.json` | volet 1 : croissance, comportements, géo, IPS, tailles |
| `site-vers-classe/data/facts_cross.json`, `facts_formation.json` | croisement site×Capytale, effet formation, cohortes |
| `transverse/data/facts_typologie.json`, `facts_investigation.json`, `facts_scenarios.json` | typologie & séances |
| `usage-urlr/data/facts_urlr.json`, `facts_urlr_cross.json`, `facts_urlr_site.json` | volumes URLR, modes remplacement/dépannage, croisements Capytale et site |

**Entrées brutes** : `public/data/capytale_fresh_20260619.csv` (versionné) ; snapshot Payload
**local & gitignore** (`../mathadata-website/private/payload-snapshots/<timestamp>/`, ou chemin défini
par `MATHADATA_SNAPSHOT`) ; statistiques URLR anonymes
`public/data/urlr_{links,daily,hourly,bursts}_20260625.csv` (versionnées ; fetch réseau hors
`rebuild_all.sh`, dérivés inclus dans le rebuild).
