# Comment sont calculés les chiffres de la page **Flux**

> **But de ce document** : expliquer, élément par élément, *la logique de calcul* derrière chaque
> chiffre du dashboard **Flux** (`dashboard_flux_profs.html`) — au niveau de la logique, pas de
> l'implémentation. En particulier : **comment l'appariement site↔Capytale alimente le canal et la
> formation**.
>
> **Source de vérité du code** : [`build_profiles.py`](build_profiles.py) → produit
> [`data/facts_profiles.json`](data/facts_profiles.json). Le dashboard Flux **lit** ces faits, il ne
> recalcule rien. Les **définitions** des termes sont dans [`GLOSSAIRE.md`](GLOSSAIRE.md) (source de
> vérité unique) ; ce document décrit seulement *l'enchaînement de calcul*. Les numéros de ligne
> renvoient à `build_profiles.py` à la date de rédaction (indicatifs).

## Vue d'ensemble de la chaîne

```
sessions.csv (clusters d'élèves <3 h, reconstruits en amont par build_canonical)
   │  count_occasions (fusion des demi-groupes : même activité, 5-15 él., <10 j)
   ▼
escalier 0-5 par prof×année  ──►  max_level  ──►  37 / 47 / 117 / 59
   │
rétention (Y = années où niveau≥4)  ──►  cohorte éligible 77, retour 33,8 %
   │
classify(prof) :  70 paires (match_individuals.py : signaux A/D/E/B)
                  + dates site (createdAt, first_cap, fdate)
                  + first_use (ancre = 1ʳᵉ apparition Capytale)
        (a) apparié 1:1            → canal_source 'individuel'   (74)
        (b) collègue au même UAI   → canal_source 'proxy_etab'   (46)
        (c) aucune trace           → défaut capytale_direct/jamais (140)
   ▼
canal 104/156 · formation 67/193 · timing 61/6
   │  groupby → Sankeys (trajectoires) + funnel (xtab) + formation_effect (k/n)
   ▼
facts_profiles.json   ──►   dashboard Flux (lit, ne recalcule pas)
```

Tous les chiffres ci-dessous excluent le **compte démo** (MD5 « 2 ») et **isolent le hub fondateur**
(MD5 « 0 »), via `enquete_common` (le socle `K`).

---

## 0. La table de base : les « 260 »

`build_profiles.py` ligne ~69 :

```python
tea = teachers.csv
tea = tea[ (taught==True OR tested==True) AND teacher NOT IN (DEMO, PIO) ]
POP = set(tea['teacher'])            # 260
n_touched = (taught==True).sum()     # 223
```

- **260** = profs Capytale ayant **enseigné** (`taught` : a des lignes `role=student`) **ou** **testé**
  (`tested` : a un auto-clone `role=teacher`), hub & démo exclus.
- **223** ont touché des élèves ; **37** sont testeurs purs (260 − 223).

---

## 1. L'escalier 0→5 (profondeur d'usage), par prof × année

Les `sessions.csv` sont **déjà** des clusters d'élèves reconstruits en amont (`build_canonical`, salves
à gap < 3 h). `build_profiles` ne fait que **classer** chaque (prof × année) — ligne ~113 :

```python
for (prof, année), g in sessions.groupby:
    classes = g[ n_eleves >= 5 ]                       # séances "usage-classe"
    n_occ   = Σ_activité  count_occasions(séances ≥5 de cette activité)
    if   n_occ >= 2:    niveau = 5    # usage multiple
    elif n_occ == 1:    niveau = 4    # usage unique
    elif a_des_élèves:  niveau = 3    # sous-seuil (élèves, mais aucune séance ≥5)
    else:               niveau = 2    # auto-test seul
```

`count_occasions` (ligne ~85) **fusionne les demi-groupes** : deux séances de la **même activité**,
chacune **5-15 élèves**, espacées de **< 10 jours** → comptent pour **1 occasion** (sinon +1). Ainsi
« usage multiple » (niveau 5) = vraiment ≥ 2 occasions distinctes, pas un demi-groupe compté deux fois.

- `max_level` d'un prof = max sur ses années.
- Distribution (`facts_profiles.max_level`) : **117** niveau 4, **59** niveau 5, **47** niveau 3, **37** niveau 2.
- **176 « ont atteint une classe »** = niveau ≥ 4 = 117 + 59.

> Niveaux **0-1** (dormant / intention) : côté **site** uniquement, **pas** dans cette table (mondes
> disjoints — cf. glossaire §4). Ils vivent dans la matrice « porte × profondeur » du Volet 2.

---

## 2. La rétention (relation ENTRE années)

`retention()` ligne ~144 :

```python
Y = { années où le prof atteint niveau >= 4 }       # années "classe"
consec   = ∃ y tel que y ET y+1 ∈ Y
react    = |Y| >= 2 mais pas consécutives
revenu   = |Y| >= 2                                 # consécutif OU réactivation
censored = |Y| == 1 ET cette année == "2025-2026"   # ne peut pas encore revenir
```

- **Cohorte éligible = 77** = a atteint une classe (`n_years_classe ≥ 1`) **ET non censuré** (lignes
  ~278-279). Les censurés (1ʳᵉ classe en 2025-26, sans « année d'après » observable) sont **exclus du
  dénominateur** — sinon on sous-estime mécaniquement.
- **Taux de retour = 33,8 %** = `mean(revenu)` sur les 77 = **26 / 77** (`retour_rate_eligible`).
  Détail : 24 retours consécutifs + 2 réactivations. (99 profs sont censurés au total.)

> ⚠️ **Anti-circularité** : la rétention ne regarde que le niveau ≥4 **entre** années ; l'escalier
> (axe 1) reste **strictement intra-annuel**. On ne mélange jamais les deux (cf. glossaire §4-5).

---

## 3. ★ L'appariement : canal & formation par prof Capytale

C'est le cœur de la page Flux, et **il y a deux couches** distinctes.

### Couche 1 — produire les 70 paires (en amont : `match_individuals.py`)

Les signaux **A / D / E / B** tournent **avant** `build_profiles` et écrivent
`site-vers-classe/data/match_candidates.csv` : **70 lignes** reliant un compte Capytale (`md5[:8]`) à un
compte site (`S####`). Rappel des signaux (cf. glossaire §10) :

- **A** (timing) : un user site clique l'activité *A* à *T* ; **un seul** compte Capytale `role=teacher`
  a cloné *A* au **même UAI** dans `[T−2j, T+60j]`.
- **D** (déploiement) : un UAI a **1 seul prof réel** (≥1 ligne `role=student`) **et 1 seul** compte
  site ayant cliqué Capytale → apparié. **Récupère la « plongée directe »** (les 59 % de profs sans
  auto-test, invisibles à A/B qui ne lisent que `role=teacher`).
- **E** (déploiement × activité) : à un UAI multi-comptes, une activité n'a qu'**1** déployeur et **1**
  cliqueur → désambiguïse.
- **B** (UAI 1:1) : exactement 1 compte site et 1 compte Capytale-`teacher` sur l'UAI.

Combinaison par priorité **E (0) < D (1) < A (2) < B (3)** — le **déploiement** (E/D, `role=student`)
passe avant l'**auto-test** (A, `role=teacher`), car le clic mène à cloner→partager, pas à s'auto-tester.
On **écarte** en plus les paires signal-A à établissement **multi-collègues** (≥2 profs déployeurs : l'auto-
testeur y est souvent un collègue → renvoi en `proxy_etab`). 1 site ↔ 1 Capytale. Résultat : **70 paires**
(46 A + 24 B ; par signal : E=34, D=17, A=9, B=10 ; 10 signal-A écartés). `build_profiles` **ne refait pas**
l'appariement, il le **consomme** (ligne ~160) :

```python
matched = { cap_acc[:8] : {statut, ftype, site_code} }   # les 70 paires
```

### Couche 2 — décider canal + formation pour CHACUN des 260 — `classify()` ligne ~188

Entrées côté site (table de travail `payload_users_work.csv`, par compte) : `createdAt` (création),
`first_cap` (1ᵉʳ clic Capytale), `fdate` (date de formation), `is_formed`, `uai`. Plus un index par
établissement :

```python
site_by_uai[uai] = { first_site   = min(createdAt des comptes de cet UAI),
                     has_formed,
                     first_formed = min(fdate des comptes formés de cet UAI) }
```

**L'ancre** (ligne ~198) — le canal décrit l'**origine**, on la fige à la 1ʳᵉ apparition Capytale :

```python
first_use = min(first_test, first_student)   # 1ʳᵉ trace du prof SUR Capytale
grace     = 1 jour
```

Puis **3 régimes**, dans l'ordre :

**(a) Apparié individuellement** — si `md5[:8] ∈ matched` (ligne ~208) :

```python
created      = createdAt du compte site apparié      # pont site_code→site_id (LOCAL)
fclick       = first_cap du même compte
site_contact = min(created, fclick)
canal = via_site        si site_contact <= first_use + grace
canal = capytale_direct sinon            # compte site créé APRÈS l'usage → arrivé par Capytale
canal_source = 'individuel'
si statut ∈ {forme, mentor} :  formation = forme (source 'individuel'),  fdate = sa date
```

→ C'est ici qu'on gère la **flèche inversée** : un prof déjà sur Capytale **avant** de toucher le site
(`site_contact > first_use`) est classé **capytale_direct** même s'il a un compte site (le site n'est
qu'un canal de retour). D'où des appariés qui finissent malgré tout `capytale_direct`.

**(b) Sinon, trace établissement (proxy écologique)** — ligne ~226 :

```python
s = site_by_uai[son UAI]
si s.first_site   <= first_use + grace :  canal = via_site,  canal_source = 'proxy_etab'
si s.has_formed et s.first_formed <= first_use + grace :
        formation = forme (source 'proxy_etab'),  canal = via_site,  fdate = s.first_formed
```

→ Pas d'appariement individuel, **mais** un **collègue** du même établissement a un compte / une
formation **antérieure** au 1ᵉʳ usage → on **suppose** « via le site / formé ». Attribution **moyenne
d'établissement**, confiance basse.

**(c) Sinon, défaut** : `capytale_direct`, `jamais`, `canal_source = 'aucune'`.

**Le timing de la formation** (ligne ~235) :

```python
si formation == forme :
    motrice       si fdate <= first_use + grace     # formé avant/le jour du 1ᵉʳ usage → a pu amorcer
    consolidation sinon                             # formé après → il utilisait déjà
```

### Les chiffres produits (`facts_profiles.json`)

| Variable | Valeurs |
|---|---|
| `canal` | via_site **104** · capytale_direct **156** |
| `canal_source` | individuel **74** · proxy_etab **46** · aucune **140** |
| `formation_statut` | forme **67** · jamais **193** |
| `formation_source` | individuel **40** · proxy_etab **27** · aucune **193** |
| `formation_timing` | motrice **61** · consolidation **6** |

> **Lecture cruciale** : sur 260 profs, **74 ont un lien 1:1**, **46 par proxy établissement**, **140
> par défaut** (54 %). Donc `capytale_direct` (156) et `jamais formé` (193) sont des **bornes hautes** :
> elles incluent « on n'a pas vu de trace » (UAI non déclaré, clic antérieur au tracking du 27/11/25,
> pas d'appariement), pas seulement « prouvé absent ». **Tout ruban Flux qui traverse le pont est donc
> *estimé*.**

### Trace concrète (un prof, pas à pas)

Prof `a3f8…` en plongée directe : `first_test = ∅`, `first_student = 10 mai 2025` → `first_use = 10 mai`.

1. `a3f8 ∈ matched` ? (apparié par le signal D, p.ex.) → oui, `site_code = S0012`.
2. son compte site : `created = 8 mai`, `first_cap = 9 mai` → `site_contact = 8 mai`.
3. `8 mai ≤ 10 mai + 1j` → **canal = via_site** (source `individuel`).
4. `statut = forme`, `fdate = 9 avril` → **formation = forme** ; `9 avril ≤ 10 mai` → **motrice**.

*S'il n'était pas apparié* : on regarderait `site_by_uai[son UAI]` ; un collègue inscrit en janvier
(≤ 10 mai) → **via_site / proxy_etab** ; sinon → **capytale_direct / jamais**.

---

## 4. Les Sankeys (trajectoires) — sur quels sous-ensembles

Calculés par simple `groupby().size()` sur les attributs posés ci-dessus. Le **« devenir »**
(ligne ~321) :

```python
devenir = 'rev' si revenu  sinon  'rec' si censored  sinon  'non'
y1b     = 'multi' si y1_level==5  sinon 'uniq'     # intensité de la 1ʳᵉ année classe
```

| Clé JSON | Population | Croisement |
|---|---|---|
| `traj_canal_devenir` | **176** (a atteint une classe) | canal × devenir |
| `traj_canal_y1_devenir` | 176 | canal × y1 (multi/uniq) × devenir |
| `traj_formation_y1_devenir` | 176 | formation × y1 × devenir |
| `funnel.touched` | **223** | canal × formation × profondeur (test/ss/uniq/multi) |
| `funnel.all` | **260** | idem (+ testeurs purs) |

Exemple : `traj_canal_devenir` → `via_site|rec 62, via_site|rev 8, via_site|non 7` (= 77 via_site ayant
atteint une classe) et `capytale_direct|non 44, …` (= 99). La largeur d'un ruban du Sankey = ce
comptage. Le Sankey « canal → profondeur » agrège les cellules de `funnel.all.xtab` par canal et par
profondeur (via_site : test 14, ss 13, uniq 46, multi 31 → 104).

---

## 5. L'effet formation — `formation_effect` (ligne ~377)

On expose des **comptes bruts `(k, n)`** ; les p-values (Fisher) sont calculées **à l'affichage** par
`build_flux_dashboard.py`, pas stockées.

```python
mult_y1 : parmi les 176, k = (y1_level==5)         # forme / jamais / motrice / via_forme / via_jamais
reach   : parmi les 223, k = (max_level>=4)         # forme 51/58  vs  jamais 125/165
retour  : parmi les 77 éligibles, k = revenu        # forme 7/12   vs  jamais 19/65  ·  motrice 6/11
med     : à y1_level FIXÉ (5=reuse, 4=unique), forme vs jamais  → la formation ajoute-t-elle
          AU-DELÀ de l'intensité an-1 ? (médiation)
censored_formes : part des formés-classe censurés (39/51)  → pourquoi le retour formé est fragile
```

C'est ce qui permet d'écrire honnêtement : « **retour formés 58 % (7/12) vs non-formés 29 % (19/65),
mais n=12, Fisher p≈0,10 → non significatif** ». Le `(7,12)` vient d'ici ; le `p` est recalculé à
l'affichage ; et `censored_formes 39/51` explique pourquoi la base est si petite (la plupart des
formés ayant atteint une classe sont **trop récents** pour qu'on observe leur retour).

---

## Garde-fous & limites (à garder en tête en lisant la page Flux)

- **Le pont est estimé, pas mesuré.** Canal et formation reposent à **28 %** sur un appariement 1:1,
  **18 %** sur un proxy établissement (écologique), **54 %** sur un défaut. → ne jamais lire un ruban
  « capytale_direct / jamais formé » comme une mesure certaine.
- **Deux objets « flux » à ne pas confondre** : la page Flux (escalier côté **Capytale**, 260/223/176)
  n'est **pas** le funnel site (2 715 → … → 337, qui s'arrête au clic, côté **site**). On ne chaîne
  jamais « formés site → usage Capytale » au grain individuel.
- **Couverture UAI** : l'attribution `proxy_etab` et la conversion établissement dépendent de l'UAI
  déclaré (≈ 317/631 formés seulement) ; voir aussi `site-vers-classe/RAPPORT_VOLET2.md` §12.
- **Censure à droite** : 99 profs censurés (1ʳᵉ classe en 2025-26) → exclus des taux de retour.
- **Effet formation = descriptif & confondu** (auto-sélection, endogénéité établissement, récence) :
  on expose des `(k,n)` et une direction, **jamais** un effet causal net.

## Où vérifier / reproduire

- Code : [`build_profiles.py`](build_profiles.py) (couche canonique) ; appariement amont :
  [`../site-vers-classe/match_individuals.py`](../site-vers-classe/match_individuals.py).
- Faits : [`data/facts_profiles.json`](data/facts_profiles.json) (source de vérité des chiffres Flux).
- Génération du dashboard : `build_flux_dashboard.py` (remplit les `<span data-f>` et les Sankeys
  depuis les faits). Régénérer toute la chaîne : `bash ../rebuild_all.sh`.
- Définitions des termes : [`GLOSSAIRE.md`](GLOSSAIRE.md) (fait foi en cas de divergence).
