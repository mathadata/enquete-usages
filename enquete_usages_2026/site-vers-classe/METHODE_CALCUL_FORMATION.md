# Comment est calculé le « 59 % » (effet formation, au grain établissement)

> **But** : expliquer la logique de calcul de la conversion *formation → classe* du Volet 2 —
> notamment le **« 59 % des établissements ciblés »** (et le contraste **~6×** avec l'académique de
> masse). Au niveau de la logique, pas de l'implémentation.
>
> **Code** : [`build_formation_cohorts.py`](build_formation_cohorts.py) → produit
> [`data/facts_formation.json`](data/facts_formation.json) et [`data/cohorts.csv`](data/cohorts.csv).
> Le dashboard Volet 2 **lit** ces faits. Définitions des termes : [`../transverse/GLOSSAIRE.md`](../transverse/GLOSSAIRE.md)
> (§7 formation). Numéros de ligne indicatifs.

## Ce que mesure le « 59 % », en une phrase

*Parmi les **établissements distincts** d'où viennent des profs formés en formation **établissement-
ciblée**, quelle part a **au moins un usage élève Capytale** (sur tout l'historique 2023→2026) ?*
→ **13 / 22 = 59 %**. C'est une mesure **écologique** (l'usage peut venir d'un collègue) au **grain
établissement**, pas par personne.

## Vue d'ensemble de la chaîne

```
Capytale (role=student, uai_el)  ──►  cap_used = { UAI ayant ≥1 usage élève, historique complet }
                                                        │
Site (users formés)  ──group by trainedFormation──►  cohortes (code de formation)
        │                                               │
        │  nature(code) par MOTS-CLÉS du label          │
        ▼                                               ▼
   établissement-ciblée / distanciel-webinaire /     pour chaque nature :
   académique-de-masse / pré-service / ancienne_vague    UAI distincts des profs formés
                                                          ∩ cap_used  →  pct_etab
                                                                   │
                                                                   ▼
                                              nature_typology → 59 % / 30 % / ~10 %
```

Le compte démo (MD5 « 2 ») est exclu via le socle `K`.

---

## Étape 1 — Côté Capytale : quels établissements ont un usage élève ?

`build_formation_cohorts.py` lignes ~35-46 :

```python
cap   = lignes Capytale (démo exclu)
stud  = cap[ role == 'student' AND uai_el non vide ]      # vrais élèves
cap_used = { uai_el de chaque ligne élève }               # UAI avec ≥1 usage élève réel
```

- **`cap_used`** = ensemble des UAI (clé = `uai_el`, l'établissement de l'**élève**) ayant **au moins
  une ligne `role=student`** sur **tout l'historique 2023→2026**.
- C'est **non biaisé par la fenêtre de tracking site** (≥ 27/11/25) : on lit l'usage Capytale complet.
- « a une classe » ici = **≥ 1 élève** (a déployé au moins une fois) — c'est **distinct** du KPI qualité
  « vraie séance ≥ 10 él. ». C'est volontaire : on mesure « l'établissement a-t-il basculé en usage ? ».

---

## Étape 2 — Côté site : regrouper les profs formés par cohorte

Lignes ~49-52 :

```python
formed  = users avec statut ∈ {forme, mentor}, hors exclude_from_analytics      # 631
by_code = formed regroupés par leur champ trainedFormation (= l'id du code de formation)
```

Chaque prof formé porte un **code de formation** (`trainedFormation`) résolu dans `formation-codes.json`
(label réel, type, vraie date). Les **147 « ancienne vague »** (codes placeholder à date factice 1984)
sont isolés (`PLACEHOLDER`, ligne ~30) — type & date **inconnus**.

---

## Étape 3 — Classer chaque cohorte par **nature** (mots-clés du label)

`nature(cid)` lignes ~148-155 — c'est une **règle par mots-clés** sur le label de la formation :

```python
si code placeholder 1984           → 'ancienne_vague'
si label contient 'MEEF'           → 'pre-service'         # master MEEF INSPÉ (sans classe)
si label contient un de ETAB_KW    → 'etablissement-ciblee'
si typeFormation ∈ {webdecouv,webinaire} → 'distanciel-webinaire'
sinon                              → 'academique-de-masse'
```

avec `ETAB_KW = [Gif, Arpajon, Calais lycée Pro, 202410_LILLE, AMIENS, MONTPELLIER_25]`.

> ⚠️ **Deux réglages importants, validés par l'équipe** (ligne ~140-147) :
> - **`MEEF` seul = pré-service** (étudiants sans classe, 0 % *par construction*). Le mot-clé n'attrape
>   **pas** « INSPE Formation 26/11 » (profs en exercice).
> - **`ENS_25` (52 profs) N'EST PAS du pré-service** : formation francilienne **ouverte, non ciblée**,
>   suivie par des profs **en exercice** → elle retombe dans **`academique-de-masse`** ; son 0 % d'usage
>   est un **vrai échec de formation de masse**, pas un artefact.
>
> Cette classification est **subjective** (mots-clés) mais **confirmée par l'équipe** (Gif, Lille 2024,
> Calais LP, Amiens = vraies ciblées). C'est la principale source de fragilité du chiffre.

---

## Étape 4 — La conversion au **grain établissement distinct** → le 59 %

Lignes ~157-165 :

```python
pour chaque prof formé u :
    n = nature(son code)
    nat_estab[n].add(u.uai)              # UAI distincts (un lycée à 3 profs formés compte 1 fois)
    si u.uai ∈ cap_used :
        nat_used[n].add(u.uai)

pct_etab[n] = 100 * len(nat_used[n]) / len(nat_estab[n])
```

- **Déduplication par établissement** : un lycée avec 3 collègues formés **compte une seule fois**.
  C'est la différence clé avec le grain prof (qui gonflerait à ~67 % en comptant chaque collègue).
- Seuls les profs formés **ayant un UAI déclaré** entrent dans `nat_estab` (sinon `u.uai` est vide).
  → couverture limitée (≈ 317/631 formés ont un UAI).

**Résultat (`facts_formation.nature_typology`)** :

| Nature | Étab. distincts | Avec classe | **pct_etab** |
|---|---:|---:|---:|
| **établissement-ciblée** | **22** | **13** | **59 %** |
| distanciel-webinaire | 61 | 18 | 30 % |
| académique-de-masse | 126 | 13 | **~10 %** |
| ancienne vague | 31 | 8 | 26 % |
| pré-service (MEEF strict) | ~5 | 0 | 0 % |

→ **Le facteur ~6** = 59 % (ciblée) vs ~10 % (masse), alors que **les deux sont du présentiel**. C'est
le résultat central : ce n'est pas le *format* qui prédit l'aboutissement, c'est la **concentration**.

---

## Le complément : table par cohorte + endogénéité (`cohorts.csv`)

En parallèle (lignes ~60-78), pour **chaque code** on calcule un `pct_used = at_used / n_uai` et, avec
la **vraie date de formation**, on sépare l'usage **antérieur** vs **postérieur** :

```python
pour chaque UAI de la cohorte (date formation fd connue) :
    si 1ʳᵉ séance Capytale de l'UAI >= fd − 7 jours :  usage_after  += 1
    sinon                                            :  usage_before += 1   # ENDOGÈNE
```

- **Endogénéité mesurée** : sur le présentiel, **9/26** établissements à usage utilisaient déjà
  Capytale **avant** la formation (`presentiel_usage_before_endogene`) → la formation ne peut être
  créditée d'environ un tiers de l'usage observé.
- **Délai médian formation → 1ʳᵉ séance ≈ 27 j** (`presentiel_delay_days`, sur les UAI à usage
  postérieur).

---

## L'intention déclarée vs l'usage réel (lignes ~113-131)

Pour chaque *redemption* (validation de code), on compare le(s) **module(s) déclaré(s)** en intention à
l'usage Capytale **réel de l'établissement** :

```python
pour chaque module déclaré m (mappé en mathadata_id via MOD2MID) :
    si l'UAI du prof a effectivement utilisé cette activité :  match_intent += 1
```

→ **6 intentions réalisées / 99** (même activité dans l'établissement) ; mais 85/93 non réalisées
viennent d'établissements **sans aucun TP** → le goulot est le **passage à l'acte**, pas le choix du
module.

---

## Garde-fous & limites (à garder en tête)

- **Écologique** : `cap_used` est au grain établissement (`uai_el`) → l'usage peut venir d'un
  **collègue non formé**, pas du prof formé. On mesure « l'établissement a bougé », pas « le formé a
  enseigné ».
- **Couverture UAI ⟂ maturité** : seuls les formés à **UAI déclaré** comptent (≈ 317/631) ; et les
  cohortes **mûres** (meilleur recul) ont la **pire** couverture (Lille oct. 2024 : 6/40 UAI → le
  66,7 % de cette cohorte repose sur 6 établissements). Cf. `RAPPORT_VOLET2.md` §12.
- **Classification par mots-clés** = subjective (cas borderline : Calais LP), confirmée équipe.
  → la **direction** (concentration ≫ dispersion) est robuste ; le **chiffre exact** (59) est un
  **ordre de grandeur** sur 22 établissements.
- **« A une classe » = ≥ 1 élève** (a déployé), pas la « vraie séance ≥ 10 » : c'est un seuil
  d'**aboutissement**, pas le KPI qualité.
- **Endogénéité non retranchée du pct_etab** : `nature_typology` compte *tout* usage de l'historique,
  y compris antérieur à la formation. La correction d'endogénéité est exposée à part (`usage_before`).
- **Descriptif, non causal** : auto-sélection (on forme des établissements déjà acquis) + endogénéité
  → on n'affirme jamais un effet causal net de la formation.

## Où vérifier / reproduire

- Code : [`build_formation_cohorts.py`](build_formation_cohorts.py) (+ appariement amont éventuel :
  [`match_individuals.py`](match_individuals.py)).
- Faits : [`data/facts_formation.json`](data/facts_formation.json) (nature_typology, endogénéité,
  intention) ; détail par cohorte : [`data/cohorts.csv`](data/cohorts.csv).
- Rapport : [`RAPPORT_VOLET2.md`](RAPPORT_VOLET2.md) §3. Définitions : [`DEFINITIONS_VOLET2.md`](DEFINITIONS_VOLET2.md)
  et [`../transverse/GLOSSAIRE.md`](../transverse/GLOSSAIRE.md).
- Régénérer : `bash ../rebuild_all.sh` (étape croisée, nécessite le snapshot Payload local).
