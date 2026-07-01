---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Enquête usages MathAData — architecture & appariement'
style: |
  :root {
    --ink:#1d3557; --blue:#2a6f97; --teal:#48cae4; --tealbg:#e7f6fb;
    --orange:#e76f51; --orangebg:#fff1ec; --green:#2a9d8f; --greenbg:#e9f7f4;
    --grey:#e0e4ea;
  }
  section { font-size: 23px; padding: 40px 52px; color:#222; }
  h1 { color: var(--ink); font-size: 42px; }
  h2 { color: var(--ink); font-size: 32px; border-bottom: 2px solid var(--grey); padding-bottom: 5px; margin-bottom:14px;}
  h3 { color: var(--blue); margin:6px 0; }
  strong { color: var(--ink); }
  code { background: #f1f3f6; font-size:0.85em; }
  table { font-size: 19px; }
  .small { font-size: 17px; color:#566; }
  .why { background:var(--tealbg); border-left:5px solid var(--blue); padding:8px 14px; font-size:20px; }
  .lim { background:var(--orangebg); border-left:5px solid var(--orange); padding:8px 14px; font-size:20px; }
  section.lead { background:var(--ink); color:#fff; }
  section.lead h1, section.lead h2, section.lead h3 { color:#fff; border:none; }
  section.part { background:var(--blue); color:#fff; justify-content:center;}
  section.part h1, section.part h2 { color:#fff; border:none;}
  /* --- diagram toolkit --- */
  .row { display:flex; align-items:center; justify-content:center; gap:8px; flex-wrap:wrap; margin:6px 0;}
  .col { display:flex; flex-direction:column; gap:8px; }
  .box { border-radius:10px; padding:9px 13px; background:#fff; border:2px solid var(--blue); text-align:center; min-width:90px;}
  .box b { display:block; font-size:26px; color:var(--ink); line-height:1.1;}
  .box span { font-size:15px; color:#566; }
  /* inline emphasis inside flowing-text boxes must NOT become a block stat number */
  .box span b { display:inline; font-size:inherit; color:inherit; font-weight:700; line-height:inherit;}
  .box.desc { text-align:left; }
  .box.desc b { display:inline; font-size:inherit; color:var(--ink); font-weight:700; line-height:inherit;}
  .box.ink{ background:var(--ink); color:#fff; border-color:var(--ink);} .box.ink b,.box.ink span{color:#fff;}
  .box.blue{ background:var(--blue); color:#fff; border-color:var(--blue);} .box.blue b,.box.blue span{color:#fff;}
  .box.teal{ background:var(--tealbg); border-color:var(--teal);}
  .box.orange{ background:var(--orangebg); border-color:var(--orange);} .box.orange b{color:var(--orange);}
  .box.green{ background:var(--greenbg); border-color:var(--green);} .box.green b{color:var(--green);}
  .box.ghost{ background:#fafbfc; border-style:dashed; border-color:#aab;}
  .arr { font-size:26px; color:var(--blue); font-weight:bold; }
  .arrx { font-size:24px; color:var(--orange); font-weight:bold; }
  .bar { background:var(--grey); border-radius:6px; height:30px; margin:4px 0; overflow:hidden;}
  .bar i { display:block; height:100%; background:var(--blue); color:#fff; font-style:normal; line-height:30px; padding-left:10px; white-space:nowrap; font-size:17px;}
  .bar i.hi{ background:var(--green);} .bar i.lo{ background:var(--orange);}
  .tag{ display:inline-block; background:var(--ink); color:#fff; border-radius:5px; padding:1px 8px; font-size:15px;}
  /* compact slide (dense code blocks) */
  section.tight { font-size:20px; padding-top:28px; }
  section.tight h2 { margin-bottom:8px; }
  section.tight p { margin:5px 0; }
  section.tight pre { font-size:13px; margin:5px 0; padding:7px 12px; line-height:1.25; }
  section.tight .why { font-size:18px; padding:6px 12px; }
---

<!-- _class: lead -->

# Enquête usages MathAData
## Architecture de la pipeline & appariement site ↔ Capytale

**Discussion technique** — équipe technique + équipe déploiement / données / formation

<div class="row">
<div class="box blue"><b>3</b><span>sources de données</span></div>
<div class="box blue"><b>2023→26</b><span>3 ans Capytale</span></div>
<div class="box blue"><b>0</b><span>donnée perso publiée</span></div>
</div>

---

## Ce qu'on veut couvrir

<div class="row">
<div class="box teal" style="min-width:340px"><b>1 — La pipeline</b><span>pourquoi · principes · 3 sources · fonctionnement</span></div>
<div class="box orange" style="min-width:340px"><b>2 — L'appariement site↔Capytale</b><span>aucune clé commune · ce qu'on a choisi · limites · alternatives</span></div>
</div>

<div class="why">

**Fil rouge de chaque sujet** : *pourquoi* (la question) → *les données dispo & contraintes* → *comment on a fait* → *détails d'implémentation* → *limites*.

</div>

---

## Le principe directeur : **deux mondes disjoints**

<div class="row">
<div class="box ink" style="min-width:230px"><b>CAPYTALE</b><span>usage EN CLASSE · ANONYME (MD5 ENT)<br>2023→2026</span></div>
<div class="col">
<span class="arrx">⟂</span><span class="small">aucune clé commune</span>
</div>
<div class="box green" style="min-width:230px"><b>mathadata.fr</b><span>parcours AMONT · NOMINATIF<br>tracking clics ≥ 27/11/25</span></div>
</div>

<div class="row">
<div class="box" style="min-width:230px"><b>224</b><span>profs ont enseigné</span></div>
<div class="box" style="min-width:230px"><b>5 854</b><span>élèves</span></div>
<span class="arr">·  un seul pont  ·</span>
<div class="box green"><b>2 715</b><span>comptes site</span></div>
</div>

<div class="row">
<div class="box teal" style="min-width:680px"><b>URLR / Basthon</b><span>3ᵉ source — volumes AGRÉGÉS, aucune identité (6 liens, 1 213 clics)</span></div>
</div>

<div class="lim">

**Conséquence cardinale** : tout ce qui relie les mondes est **estimé**, jamais mesuré. On le dit à chaque chiffre.

</div>

---

<!-- _class: part -->

# Partie 1
## La pipeline : principes, sources, fonctionnement

---

## Pourquoi une pipeline (et pas des scripts ad hoc)

<div class="why">

**Le problème** : 3 sources · 4 analyses · des dizaines de chiffres publiés · plusieurs sessions. Sans discipline → chaque script redéfinit « classe », « prof », « rétention » → **chiffres qui se contredisent**.

</div>

<div class="row">
<div class="box teal" style="min-width:200px"><b>1</b><span>Définitions<br>canoniques centralisées<br>(GLOSSAIRE)</span></div>
<span class="arr">→</span>
<div class="box teal" style="min-width:200px"><b>2</b><span>Une seule couche<br>de calcul<br>(build_profiles)</span></div>
<span class="arr">→</span>
<div class="box teal" style="min-width:200px"><b>3</b><span>facts_*.json =<br>sources de vérité<br>(on lit, pas recalcul)</span></div>
<span class="arr">→</span>
<div class="box green" style="min-width:200px"><b>4</b><span>Contrats<br>anti-régression<br>(pre-commit + CI)</span></div>
</div>

→ Reproductible (`rebuild_all.sh`), **idempotent**, vérifiable, **sans PII**.

---

## Les trois sources de données

<div class="row">
<div class="box ink" style="min-width:300px"><b>CAPYTALE</b><span>1 ligne = 1 clone · anonyme (MD5)<br>2023→2026 · ✅ versionné<br>API c-stat/mathadata, token .env.local</span></div>
<div class="box green" style="min-width:300px"><b>PAYLOAD (site)</b><span>users / sessions / events / clics · nominatif<br>clics ≥ 27/11/25 · ❌ LOCAL & gitignore (PII)<br>MATHADATA_SNAPSHOT fige une extraction</span></div>
</div>
<div class="row">
<div class="box teal" style="min-width:620px"><b>URLR (Basthon)</b><span>clics/uniques par fenêtre · agrégé, aucune identité · liens ≥ 25/12/25 · ✅ versionné · fetch réseau HORS rebuild</span></div>
</div>

| | grain brut | nature | clé d'identité |
|---|---|---|---|
| Capytale | affectation (clone) | usage classe | MD5 ENT (anonyme) |
| Payload | compte / clic | intention amont | nominatif (local) |
| URLR | compteur / fenêtre | volume sans compte | **aucune** |

---

## La donnée brute Capytale : 1 ligne = 1 clone

<div class="row">
<div class="box"><b>role</b><span>TYPE du compte<br>teacher / student</span></div>
<div class="box"><b>teacher</b><span>distributeur<br>= l'identité prof</span></div>
<div class="box"><b>student</b><span>propriétaire du clone<br>(élève ou stagiaire)</span></div>
<div class="box"><b>uai_teach<br>uai_el</b><span>établissements</span></div>
<div class="box blue"><b>mathadata_id</b><span>activité-maître<br>= LE PONT web/b/&lt;id&gt;</span></div>
</div>

<div class="lim">

**Pièges canoniques** — ⚠️ ne JAMAIS compter les profs via `n_teacher_clones` : **59 % des profs (133/224)** n'ont aucun auto-test (« plongée directe »). Compter = `distinct(teacher)` sur lignes `role=student`. · Isoler le **hub fondateur** `cfcd2084…` (MD5 "0", 404 él. / 14 étabs). · Exclure le **compte démo** `c81e728d…` (MD5 "2").

</div>

---

## La chaîne `rebuild_all.sh` — une seule commande

<div class="col">
<div class="row">
<div class="box" style="min-width:160px"><b>[1] CAPYTALE</b><span>build_canonical → teachers_v2 → compute_facts</span></div>
<span class="arr">→</span>
<div class="box ghost" style="min-width:130px"><b>[2] URLR×Cap</b><span>build_canonical<br><span class="tag">auto-skip</span></span></div>
<span class="arr">→</span>
<div class="box ghost" style="min-width:200px"><b>[3] CROISÉ site×Cap</b><span>payload_canonical → <b style="font-size:17px">match_individuals</b> → formation_cohorts<br><span class="tag">snapshot PII requis</span></span></div>
</div>
<div class="row">
<div class="box green" style="min-width:230px"><b>[4] PROFILS canonique</b><span>compute_cross_facts → <b style="font-size:17px">build_profiles</b> → build_master<br>★ profiles_teacher(_year).csv, facts_profiles.json</span></div>
<span class="arr">→</span>
<div class="box" style="min-width:200px"><b>[5] TRANSVERSE</b><span>scenarios → reconcile_facts → flux_dashboard (généré)</span></div>
<span class="arr">→</span>
<div class="box blue" style="min-width:150px"><b>[6] CONTRATS</b><span>check_contracts<br>✅ ou exit 1</span></div>
</div>
</div>

Boîtes pleines = **toujours** rejouées (depuis `public/data`). Boîtes pointillées = **auto-sautées** sans le snapshot PII (clone public). **Idempotent** : re-run = aucune dérive.

---

## Le socle partagé `K` (`enquete_common.py`)

Source **unique** des constantes — tout script `import enquete_common as K`. On ne redéfinit JAMAIS un seuil localement.

<div class="row">
<div class="box orange"><b>EXCLURE</b><span>DEMO c81e728d…</span></div>
<div class="box orange"><b>ISOLER</b><span>hub PIO cfcd2084…</span></div>
<div class="box teal"><b>≥ 5</b><span>usage-classe</span></div>
<div class="box teal"><b>≥ 10</b><span>séance riche</span></div>
<div class="box teal"><b>≥ 20</b><span>grande classe</span></div>
<div class="box teal"><b>5-15 / 10j</b><span>fusion demi-groupes</span></div>
</div>

<div class="row">
<div class="box ink"><b>260</b><span>Capytale (2-5)</span></div>
<div class="box ink"><b>223</b><span>touché élèves</span></div>
<div class="box ink"><b>176</b><span>classe ≥5</span></div>
<div class="box ink"><b>47</b><span>sous-seuil</span></div>
<div class="box ink"><b>37</b><span>testeurs</span></div>
<div class="box ink"><b>77</b><span>cohorte rétention</span></div>
</div>

Populations **ancrées** (`K.EXPECT`) : les contrats cassent si une régénération les fait bouger sans revue consciente. Fonctions : `school_year()` (coupure **1ᵉʳ août**), `exclude_special()`, `sanitize_json()`.

---

## Cœur algorithmique : reconstruction des **séances**

Capytale ne donne pas la notion de séance → on la reconstruit par **clustering temporel**.

<div class="why">
Séance = run maximal de clones <b>ÉLÈVES</b> de même <code>(teacher, mathadata_id, uai_el)</code>, créations consécutives espacées de <b>&lt; 3 h</b>.
</div>

<div class="row">
<div class="box green"><b>13:01</b></div><div class="box green"><b>13:03</b></div><div class="box green"><b>13:05</b></div>
<span class="arrx">— gap &gt; 3 h —</span>
<div class="box teal"><b>16:40</b></div><div class="box teal"><b>16:42</b></div>
</div>
<div class="row">
<div class="box green" style="min-width:230px"><b>Séance A</b><span>n_eleves=3 · span_min</span></div>
<span class="arr"> </span>
<div class="box teal" style="min-width:170px"><b>Séance B</b><span>n_eleves=2</span></div>
</div>

<div class="lim">

⚠️ **Durée médiane d'un run ≈ 7 min** : ce sont des **salves** (créneau de connexion), pas la durée du cours. Demi-groupes (même activité, 5-15 él., &lt; 10 j) fusionnés en **1 occasion**.

</div>

---

## L'escalier de profondeur 0→5 (par prof × année)

<div class="row">
<div class="box green"><b>0</b><span>dormant<br><span class="tag">site</span></span></div>
<span class="arr">→</span>
<div class="box green"><b>1</b><span>intention<br><span class="tag">site</span></span></div>
<span class="arr">→</span>
<div class="box ink"><b>2</b><span>auto-test<br>37 profs</span></div>
<span class="arr">→</span>
<div class="box ink"><b>3</b><span>sous-seuil<br>47</span></div>
<span class="arr">→</span>
<div class="box ink"><b>4</b><span>usage unique<br>≥5 él.</span></div>
<span class="arr">→</span>
<div class="box ink"><b>5</b><span>usage multiple<br>≥2 occasions</span></div>
</div>

<div class="row">
<div class="box green" style="min-width:300px"><b>côté SITE</b><span>niveaux 0-1 (2 715 comptes) — matrice Volet 2</span></div>
<div class="box ink" style="min-width:300px"><b>côté CAPYTALE</b><span>niveaux 2-5 (260) — profiles_teacher_year</span></div>
</div>
<div class="row">
<div class="box blue" style="min-width:300px"><b>176</b><span>atteignent une classe (niveau ≥ 4)</span></div>
</div>

Barreaux **exclusifs** : chaque prof-année tombe dans un seul. Les deux mondes ne se recouvrent que par l'appariement (70 paires).

---

## Le funnel complet : du site… au mur de l'univers Capytale

<div class="col">
<div class="bar"><i style="width:100%">2 715 comptes site &nbsp;(100 %)</i></div>
<div class="bar"><i style="width:63%">1 712 complets &nbsp;(63 %)</i></div>
<div class="bar"><i style="width:23%">631 formés &nbsp;(23 %)</i></div>
<div class="bar"><i class="lo" style="width:12.4%">337 clic Capytale (12 %)</i></div>
</div>

<div class="row"><span class="arrx">⛔ changement d'univers — aucun identifiant commun · 44 % des établissements à usage n'ont AUCUN compte site</span></div>

<div class="col">
<div class="bar"><i class="hi" style="width:82%">224 ont enseigné &nbsp;(Capytale, anonyme)</i></div>
<div class="bar"><i class="hi" style="width:65%">176 usage-classe ≥5</i></div>
<div class="bar"><i class="hi" style="width:55%">150 séance riche ≥10 &nbsp;→ 5 854 élèves</i></div>
</div>

<div class="lim">

Le ratio **224 / 2 715 (~8 %) n'est PAS un taux de conversion** : deux populations partiellement disjointes. Les seuls taux propres sont **intra-univers** (Capytale : 401 engagés → 224 ont enseigné = 56 %).

</div>

---

## `facts_*.json` : on lit, on ne recalcule pas

<div class="row">
<div class="col">
<div class="box ghost"><b>usages_enriched</b><span>1 clone</span></div>
<div class="box ghost"><b>sessions</b><span>1 séance</span></div>
<div class="box ghost"><b>profiles_teacher</b><span>1 prof ★</span></div>
</div>
<span class="arr">→</span>
<div class="col">
<div class="box blue"><b>facts_profiles</b><span>★ flux / rétention</span></div>
<div class="box blue"><b>facts_reconciliation</b><span>fiche de référence</span></div>
<div class="box blue"><b>facts_cross / _formation</b><span>site × Capytale</span></div>
</div>
<span class="arr">→</span>
<div class="box green" style="min-width:170px"><b>dashboards .html</b><span>chiffres EN DUR<br>(CSP-safe)<br>Flux = généré</span></div>
</div>

**Règle de réponse** : chercher d'abord dans les **facts**, puis dans les **tables** ; ne recalculer que l'inexistant — et alors depuis les tables canoniques, jamais en redéfinissant un terme.

---

## Anti-dérive : ce qui empêche les chiffres de mentir

`check_contracts.py` doit finir par `✅ tous les contrats respectés` :

<div class="row">
<div class="box green" style="min-width:210px"><b>223 + 37 = 260</b><span>partition population</span></div>
<div class="box green" style="min-width:210px"><b>176 + 47 = 223</b><span>partition classe</span></div>
<div class="box teal" style="min-width:210px"><b>JSON strict</b><span>NaN/Inf rejetés</span></div>
</div>
<div class="row">
<div class="box teal" style="min-width:210px"><b>md5[:8]</b><span>pseudonymat</span></div>
<div class="box teal" style="min-width:210px"><b>dashboards ↔ facts</b><span>concordance forcée</span></div>
<div class="box orange" style="min-width:210px"><b>0 e-mail</b><span>dans data/ & public/</span></div>
</div>

<div class="row">
<div class="box ink" style="min-width:300px"><b>hook pre-commit</b><span>versionné — commit refusé si rouge</span></div>
<div class="box ink" style="min-width:300px"><b>CI GitHub</b><span>contrats rejoués à chaque push</span></div>
</div>

Un chiffre **ne peut pas diverger en silence**.

---

<!-- _class: part -->

# Partie 2
## L'appariement site ↔ Capytale
### le cœur de la discussion technique

---

## Pourquoi : les questions à trancher

<div class="why">

On sait <b>séparément</b> ce qui se passe sur le site (intention) et sur Capytale (usage classe). On veut reconstituer <b>le pipeline complet</b> et répondre à des questions de déploiement.

</div>

<div class="row">
<div class="box teal" style="min-width:270px"><b>Formation → classe ?</b><span>quel format / concentration convertit ?</span></div>
<div class="box teal" style="min-width:270px"><b>Porte d'entrée ?</b><span>site-first vs Capytale-direct</span></div>
</div>
<div class="row">
<div class="box teal" style="min-width:270px"><b>Canal & formation</b><span>d'un prof Capytale → alimenter les profils</span></div>
<div class="box teal" style="min-width:270px"><b>Intention → usage ?</b><span>le déclaré prédit-il le réel ?</span></div>
</div>

→ Toutes exigent de **relier** un compte site (nominatif) à un usage Capytale (anonyme).

---

## La contrainte fondamentale : aucune clé commune

<div class="row">
<div class="box green" style="min-width:300px"><b>SITE (Payload)</b><span>user_id · nom · prénom · e-mail<br>uai déclaré · clics datés</span></div>
<div class="col"><span class="arrx">✗</span><span class="small">pas d'e-mail<br>côté Capytale</span></div>
<div class="box ink" style="min-width:300px"><b>CAPYTALE</b><span>teacher = MD5 d'un compte ENT<br>uai_teach / uai_el · clones datés</span></div>
</div>

- Capytale **anonyme par conception** (RGPD/ENT) : le MD5 n'est rattachable à personne.
- Les **seuls attributs partagés** : **UAI + activité + temps**. Pas de jointure possible → le lien est **inféré**.

<div class="lim">

**Décision de cadrage** : conclusions robustes au grain **établissement / cohorte**. L'individuel est un **bonus inféré, à confiance signalée** : il *alimente le canal* et *illustre*, il ne *mesure pas* une population.

</div>

---

## Le seul pont direct : le clic `web/b/<id>`

<div class="row">
<div class="box green" style="min-width:330px"><b>SITE — nominatif</b><span>consultation_rss.file =<br>"…capytale…/web/b/<b>3515488</b>"<br>→ ce user a cliqué CETTE activité, à CETTE date</span></div>
<span class="arr">═══►</span>
<div class="box ink" style="min-width:300px"><b>CAPYTALE — anonyme</b><span>mathadata_id = <b>3515488</b><br>→ des clones datés de cette activité,<br>par un MD5 anonyme</span></div>
</div>

<div class="lim">

**Le pont s'arrête au clic.** Cliquer le lien ≠ cloner sur Capytale (le clonage ENT en aval est anonyme). Donc même avec le pont, relier *le clic* au *bon compte Capytale* reste une inférence : **même UAI + même activité + timing**.

</div>

---

## Le déclic : qu'est-ce qui est partagé entre les deux mondes ?

<div class="row">
<div class="box green" style="min-width:230px"><b>SITE</b><span>nom · e-mail · formé ?<br>(qui, nominatif)</span></div>
<div class="box ink" style="min-width:230px"><b>commun aux DEUX</b><span>★ l'établissement (UAI)<br>★ l'activité (mathadata_id)</span></div>
<div class="box ink" style="min-width:230px"><b>CAPYTALE</b><span>hash anonyme · clones<br>(usage classe)</span></div>
</div>

<div class="why">

**L'idée centrale** : il n'y a pas d'identité commune, **mais l'UAI et l'activité existent dans les deux mondes**. → On ne relie pas des **personnes**, on relie des **établissements** et des **activités**. Tout le reste en découle.

</div>

---

## Trois façons de relier (du + robuste au + fragile)

<div class="col">
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box green" style="min-width:170px; display:flex; flex-direction:column; justify-content:center"><b>1</b><span>grain ÉTABLISSEMENT</span></div>
<div class="box desc" style="flex:1">clé = <b>UAI</b> (exacte, dans les 2 mondes) · <b>mesure l'impact formation en classe</b> · robuste mais <b>écologique</b> (peut-être un collègue)</div>
</div>
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box teal" style="min-width:170px; display:flex; flex-direction:column; justify-content:center"><b>2</b><span>grain SITE pur</span></div>
<div class="box desc" style="flex:1">« formé → a cliqué » · <b>pas besoin de pont</b> (2 events du site) · mesuré proprement, mais = <b>intention</b>, pas usage classe</div>
</div>
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box orange" style="min-width:170px; display:flex; flex-direction:column; justify-content:center"><b>3</b><span>grain INDIVIDU</span></div>
<div class="box desc" style="flex:1">le <b>pont du clic</b> (web/b) · tente « cette personne = ce compte Capytale » · <b>inféré</b>, bonus illustratif, confiance signalée</div>
</div>
</div>

L'**impact formation** repose surtout sur la **méthode 1**. La 3 *raconte*, elle ne *mesure* pas.

---

## Méthode 1 — grain établissement : pas à pas

<div class="row">
<div class="box green" style="min-width:175px"><b>1</b><span>prof formé<br>(site, nommé)</span></div>
<span class="arr">→</span>
<div class="box ink" style="min-width:140px"><b>2</b><span>son UAI<br>(déclaré)</span></div>
<span class="arr">→</span>
<div class="box ink" style="min-width:230px"><b>3</b><span>cet UAI a-t-il un usage ÉLÈVE Capytale ?<br>(historique complet 2023→26)</span></div>
<span class="arr">→</span>
<div class="box green" style="min-width:130px"><b>oui</b><span>= converti</span></div>
</div>

<div class="row">
<div class="box green"><b>59 %</b><span>ciblée (13/22 étabs)</span></div>
<div class="box"><b>30 %</b><span>webinaire (18/61)</span></div>
<div class="box orange"><b>10 %</b><span>masse (13/126)</span></div>
</div>

<div class="lim">

**Limites** : ⚠️ **écologique** (l'utilisateur peut être un collègue, pas le formé) · ⚠️ **UAI déclaré** seulement par **317/631 formés** · ⚠️ **endogénéité** (9/26 étabs déjà actifs avant la formation). → direction robuste, **chiffre = ordre de grandeur**.

</div>

---

## Exemple concret : un lycée suivi des deux côtés

<div class="row">
<div class="box green" style="min-width:330px; text-align:left"><b>Côté SITE (nominatif)</b><span><br>• 3 profs du « lycée Pasteur » inscrits<br>• 2 formés en oct. 2024 (on a leurs e-mails)<br>• 1 seul a renseigné l'UAI <code>0590XXXX</code></span></div>
<div class="box ink" style="min-width:330px; text-align:left"><b>Côté CAPYTALE (anonyme)</b><span><br>• à l'UAI <code>0590XXXX</code> : 309 lignes <code>role=student</code><br>• activités Géométrie + Stat, mai 2025<br>• distribuées par un hash <code>a3f8…</code></span></div>
</div>

<div class="row">
<div class="box teal" style="min-width:680px"><b>lien = l'UAI</b><span>→ « le lycée Pasteur a basculé en usage classe » ✅ &nbsp; — mais <b>on ne sait pas lequel des 3 profs</b> est le hash a3f8…</span></div>
</div>

<div class="lim">

C'est tout le sens (et la limite) du grain établissement : **« l'établissement a bougé » est sûr ; « le formé a enseigné » ne l'est pas.**

</div>

---

## Méthode 2 — site pur : l'intention (sans pont)

« Formé » et « a cliqué un lien Capytale » sont **deux événements du site** → comparaison interne, pas besoin de relier les mondes.

<div class="row">
<div class="box green"><b>23,8 %</b><span>des formés ont cliqué Capytale</span></div>
<span class="arr">vs</span>
<div class="box orange"><b>9,0 %</b><span>des non-formés</span></div>
<div class="box ghost"><b>≈ 2,5×</b><span>plus de clics</span></div>
</div>

<div class="lim">

✅ **Mesuré proprement** (1:1 dans le site). ⚠️ Mesure l'**intention** (le clic), **pas** l'usage en classe. ⚠️ Auto-sélection (on forme des gens déjà motivés). → C'est un **2ᵉ « effet formation »**, distinct de l'aboutissement-classe (méthode 1) — ne jamais les confondre.

</div>

---

## Méthode 3 — appariement individuel : le pont du clic

<div class="row">
<div class="box green" style="min-width:300px; text-align:left"><b>SITE</b> — « Mme Martin »<span><br>formée · UAI = lycée X<br>clique le lien <code>web/b/3515488</code> (Éq. réduite)<br><b>le 3 mars</b></span></div>
<span class="arr">→ ? →</span>
<div class="box ink" style="min-width:300px; text-align:left"><b>CAPYTALE</b><span><br>combien de comptes <code>teacher</code> ont cloné<br>l'activité 3515488 au lycée X<br>entre le <b>1ᵉʳ mars et le 2 mai</b> ?</span></div>
</div>

<div class="row">
<div class="box green" style="min-width:330px"><b>exactement 1</b><span>→ inféré : ce compte = Mme Martin (conf. A)</span></div>
<div class="box orange" style="min-width:330px"><b>2 ou plus</b><span>→ ambigu : on n'attribue PAS</span></div>
</div>

**70 paires** au total — un **bonus illustratif** à confiance signalée. Détail des règles (A/D/E/B) page suivante.

---

<!-- _class: tight -->

## Anatomie d'une ligne Capytale (1 ligne = 1 clone)

`role` = qui **possède** le clone · `teacher` = qui le **distribue** · `student` = le propriétaire

**① Déploiement direct (« plongée directe ») — 59 % des profs**
```
role=student  teacher=a3f8…  student=<élève>  uai_teach=0590X  mathadata_id=3515488   × 28
```
→ Mme Martin : **28 lignes role=student, 0 ligne role=teacher**. Visible **seulement** par D/E.

**② Prof qui s'auto-teste d'abord**
```
role=teacher  teacher=b7c2…  student=b7c2…   (l'auto-test : il est son propre owner)
role=student  teacher=b7c2…  student=<élève> (puis ses élèves)
```
→ M. Durand : 1 ligne role=teacher **+** lignes role=student. Visible par A/B.

**③ Formation (formateur + stagiaire)**
```
role=teacher  teacher=X(formateur)  student=Y(stagiaire)  uai_teach=<X>  uai_el=<Y>
```
→ Le stagiaire Y est `role=teacher`, son id est dans la colonne `student`. Compté (à tort) par `n_teacher_clones`.

<div class="why">

**Compter un prof = `distinct(teacher)` sur les lignes `role=student`.** Les signaux A/B ne voient que les profs de ② (qui ont une ligne `role=teacher`) → d'où D/E, qui lisent le **vrai enseignement** (`role=student`) et récupèrent ceux de ①.

</div>

---

## Méthode 3 en détail : les 4 signaux (A · D · E · B)

<div class="col">
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box green" style="min-width:150px; display:flex; flex-direction:column; justify-content:center"><b>A</b><span>timing · haute</span></div>
<div class="box desc" style="flex:1">user clique act. A à T ; <b>UN SEUL</b> compte Capytale <code>role=teacher</code> a cloné A au <b>même UAI</b> dans <code>[T−2j, T+60j]</code></div>
</div>
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box green" style="min-width:150px; display:flex; flex-direction:column; justify-content:center"><b>D</b><span>déploiement · haute/moy.</span></div>
<div class="box desc" style="flex:1">UAI à <b>1 seul prof réel</b> (a des élèves) <b>et 1 seul</b> cliqueur site → apparié <span class="small">(A si l'activité recoupe, sinon B)</span> — récupère la <b>« plongée directe »</b></div>
</div>
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box teal" style="min-width:150px; display:flex; flex-direction:column; justify-content:center"><b>E</b><span>déploi.×act. · haute</span></div>
<div class="box desc" style="flex:1">UAI multi-comptes : une activité n'a qu'<b>1</b> déployeur + <b>1</b> cliqueur (déploi. après clic) → désambiguïse</div>
</div>
<div class="row" style="flex-wrap:nowrap; align-items:stretch">
<div class="box orange" style="min-width:150px; display:flex; flex-direction:column; justify-content:center"><b>B</b><span>UAI 1:1 · moyenne</span></div>
<div class="box desc" style="flex:1">exactement <b>1</b> compte site et <b>1</b> compte Capytale-teacher sur l'UAI</div>
</div>
</div>

**Combinaison** par priorité croissante **E (0) < D (1) < A (2) < B (3)** — le **déploiement** (E/D) avant l'**auto-test** (A) ; les signal-A à établissement **multi-collègues sont écartés** (→ proxy_etab). On garde **1 site ↔ 1 Capytale**.

---

## Le piège qui a forcé D et E

<div class="lim">

**A et B ne voient que les comptes `role=teacher`** (auto-tests). Or **59 % des profs (133/224)** ne se testent JAMAIS — ils distribuent directement (« plongée directe »). A/B les rataient **tous**.

</div>

<div class="row">
<div class="box ink" style="min-width:220px"><b>A + B seuls</b><span>vus uniquement via role=teacher</span></div>
<span class="arrx">rate 59 % des profs</span>
<div class="box orange" style="min-width:130px"><b>46</b><span>paires</span></div>
<span class="arr">+ D + E →</span>
<div class="box green" style="min-width:130px"><b>75</b><span>paires</span></div>
</div>

<div class="why">

C'est exactement le même piège que `n_teacher_clones` : confondre « s'est auto-testé » et « est un prof ». Prof réel = MD5 `teacher` ayant ≥1 ligne `role=student` ; son UAI est sur `uai_teach` de ses lignes élèves.

</div>

---

## Résultats & pseudonymisation à deux niveaux

<div class="row">
<div class="box green"><b>75</b><span>paires site↔Capytale</span></div>
<div class="box"><b>53</b><span>confiance A</span></div>
<div class="box orange"><b>22</b><span>confiance B</span></div>
<div class="box"><b>26,8 %</b><span>des 280 cliqueurs à UAI connu</span></div>
</div>

<div class="row">
<div class="box ink" style="min-width:330px"><b>match_candidates.csv — VERSIONNÉ</b><span>site = S0001… · Capytale = md5[:8]<br>+ conf, UAI, commune, académie, statut</span></div>
<div class="box orange" style="min-width:330px"><b>match_nominatif.csv — LOCAL (_local/)</b><span>nom · prénom · e-mail — JAMAIS committé<br>mode --local-only · sur demande explicite</span></div>
</div>

Ordre de sortie **déterministe** (idempotence). Calibré sur le pionnier (Haubourdin `0590093F`) + UAI 1:1.

---

## Galerie de cas concrets (appariement individuel)

| Réf | Établissement | Profil | Chaîne observée | Ce que ça illustre |
|---|---|---|---|---|
| **A** | Le Vigan (Montpellier) | présentiel · conf A | compte créé **le jour de la formation**, clone « Éq. réduite » le jour même, **0 élève** encore | **amorçage immédiat** (classes à la rentrée) |
| **B** | Orsay (Versailles) | webinaire · conf A | 3 activités, **65 élèves** sur 5 séances · **2 comptes** au même UAI | étab sûr, **collègue ambigu** |
| **C** | Poissy (Versailles) | **non formé** · conf A | **60 élèves** · 1ᵉʳ clone **avant** le clic site | **flèche inversée** + productif sans formation |
| **D** | Douai (Lille) | webinaire · conf B | **99 élèves**, 9 séances sur **2 ans** | **ré-useur durable** |
| **E** | Ciboure (Bordeaux) | petit collège · conf B | chaîne complète mais **3 élèves** | **faux positif coûteux**, signal fragile |

<div class="why">

Ces 5 cas couvrent les situations-types : converti-vite · collègue-indistinct · déjà-autonome (le site n'est qu'un retour) · installé-dans-la-durée · trop-petit-pour-être-sûr. **L'individuel donne à voir le scénario ; il ne le chiffre pas.**

</div>

---

## Exploitation (1) — les deux portes

<div class="row">
<div class="box ink" style="min-width:170px"><b>174</b><span>étabs à usage classe Capytale</span></div>
<span class="arr">→</span>
<div class="box green"><b>97</b><span>56 % — ont un compte site<br>« site-first »</span></div>
<div class="box orange"><b>77</b><span>44 % — AUCUN compte site<br>« Capytale-direct »</span></div>
</div>
<div class="row">
<div class="box ghost" style="min-width:560px"><span>dont <b>42/77</b> marqués par l'ancienne « Intro IA » (absente du site) — l'héritage des précurseurs</span></div>
</div>

<div class="why">

**Insight** : 44 % des **établissements à usage** n'ont **aucun compte site**. La découverte « froide » passe par le **catalogue Capytale** et le bouche-à-oreille, pas par le SEO. Le site est surtout un canal de **préparation et de relance**.

</div>

---

## Exploitation (2) — l'effet formation

Croisement **cohorte × usage élève établissement** (historique Capytale complet, **non biaisé** par la fenêtre de tracking) :

<div class="col">
<div class="bar"><i class="hi" style="width:59%">Établissement-ciblée &nbsp;59 % &nbsp;(13/22 étabs)</i></div>
<div class="bar"><i style="width:30%">Distanciel / webinaire &nbsp;30 % &nbsp;(18/61)</i></div>
<div class="bar"><i class="lo" style="width:10%">Académique de masse &nbsp;10 % &nbsp;(13/126)</i></div>
</div>

<div class="why">

**Ce n'est pas le format qui prédit l'aboutissement, c'est la concentration** — facteur **~6**, alors que ciblée et masse sont **toutes deux du présentiel**. → Levier déploiement n°1.

</div>

<div class="lim">

Endogénéité : **9/26** étabs présentiels à usage utilisaient déjà Capytale **avant** la formation. Base petite (22 étabs) → ordre de grandeur, direction robuste.

</div>

---

## Exploitation (3) — figer le canal & timer la formation

L'appariement (ou, à défaut, la **trace établissement**) alimente `build_profiles.py` :

<div class="col">
<div class="row">
<div class="box ink" style="min-width:150px"><b>prof Capytale</b></div>
<span class="arr">→</span>
<div class="box green" style="min-width:230px"><b>apparié A/B/D/E ?</b><span>canal_source = 'individuel' (haute conf.)</span></div>
</div>
<div class="row">
<div class="box ghost" style="min-width:150px"><span>sinon</span></div>
<span class="arr">→</span>
<div class="box teal" style="min-width:230px"><b>collègue formé/site au même UAI ?</b><span>'proxy_etab' (écologique)</span></div>
<span class="arr">→</span>
<div class="box ghost" style="min-width:150px"><b>sinon</b><span>capytale_direct</span></div>
</div>
<div class="row">
<div class="box blue" style="min-width:560px"><b>formation</b><span>date ≤ 1ᵉʳ usage classe → <b>motrice</b> (amorce) &nbsp;·&nbsp; sinon → <b>consolidation</b> (renforce)</span></div>
</div>
</div>

<div class="lim">

**Règle stricte** : `proxy_etab` sert un **agrégat**, **jamais** une identité nominative. On sépare toujours : (1) formés agrégés ; (2) appariements A/B ; (3) personnes nominatives uniques.

</div>

---

## Lecture façon Sankey : canal → profondeur (les 260 profs)

<svg viewBox="0 0 1000 410" style="width:100%; max-height:430px;">
  <rect x="122" y="20" width="26" height="135" fill="#2a9d8f"/>
  <rect x="122" y="179" width="26" height="203" fill="#1d3557"/>
  <rect x="700" y="20" width="26" height="48" fill="#b8c2cf"/>
  <rect x="700" y="80" width="26" height="61" fill="#e9a78f"/>
  <rect x="700" y="153" width="26" height="152" fill="#6fa8c7"/>
  <rect x="700" y="317" width="26" height="77" fill="#2a9d8f"/>
  <polygon points="148,20 700,20 700,38 148,38" fill="#2a9d8f" opacity="0.40"/>
  <polygon points="148,38 700,80 700,97 148,55" fill="#2a9d8f" opacity="0.40"/>
  <polygon points="148,55 700,153 700,213 148,115" fill="#2a9d8f" opacity="0.40"/>
  <polygon points="148,115 700,317 700,357 148,155" fill="#2a9d8f" opacity="0.40"/>
  <polygon points="148,179 700,38 700,68 148,209" fill="#1d3557" opacity="0.28"/>
  <polygon points="148,209 700,97 700,141 148,253" fill="#1d3557" opacity="0.28"/>
  <polygon points="148,253 700,213 700,305 148,345" fill="#1d3557" opacity="0.28"/>
  <polygon points="148,345 700,357 700,394 148,382" fill="#1d3557" opacity="0.28"/>
  <text x="114" y="86" text-anchor="end" font-size="19" fill="#1d3557" font-weight="700">via le site</text>
  <text x="114" y="106" text-anchor="end" font-size="15" fill="#566">104 profs</text>
  <text x="114" y="284" text-anchor="end" font-size="19" fill="#1d3557" font-weight="700">Capytale-direct</text>
  <text x="114" y="304" text-anchor="end" font-size="15" fill="#566">156 profs</text>
  <text x="734" y="48" font-size="17" fill="#1d3557" font-weight="700">test seul · 37</text>
  <text x="734" y="116" font-size="17" fill="#1d3557" font-weight="700">sous-seuil · 47</text>
  <text x="734" y="233" font-size="17" fill="#1d3557" font-weight="700">usage unique · 117</text>
  <text x="734" y="360" font-size="17" fill="#1d3557" font-weight="700">usage multiple · 59</text>
</svg>

<div class="why">

Largeur du ruban = nb de profs. **via_site** : 74 % atteignent une classe (uniq+multi), 30 % en usage multiple. **Capytale-direct** : davantage en test/sous-seuil. ⚠️ **Descriptif** — le canal est *estimé* (cf. les 3 régimes, ci-après).

</div>

---

## Les Sankeys flux : **deux objets distincts** (le piège n°1)

<div class="row">
<div class="box green" style="min-width:300px"><b>Funnel SITE</b><span>2 715 → 1 712 → 631 formés → 337 clic<br>1:1 <b>intra-site</b> · mesuré · s'arrête à l'<b>intention</b> (le clic)</span></div>
<div class="box ink" style="min-width:300px"><b>Sankey FLUX (canonique)</b><span>260 / 223 / 176 profs <b>Capytale</b><br>1:1 <b>intra-Capytale</b> · l'escalier = 0/1/plusieurs usages</span></div>
</div>
<div class="row">
<div class="box orange" style="min-width:620px"><b>le pont entre les deux = ESTIMÉ</b><span>canal « via_site » & statut « formé » d'un prof Capytale = attribués, pas joints</span></div>
</div>

<div class="lim">

⚠️ **On ne chaîne JAMAIS** « formés site → usage Capytale 0/1/plusieurs » au grain individuel : mondes disjoints. Le « combien de fois en classe » est mesuré **côté Capytale** ; le « formé » y est **posé par estimation**. Le funnel site, lui, ne voit rien après le clic.

</div>

---

## D'où viennent les rubans : 3 régimes de confiance

Pour chacun des **260 profs Capytale**, `build_profiles.classify()` attribue canal + formation :

<div class="row">
<div class="box green" style="min-width:200px"><b>74</b><span>canal · <b>individuel</b><br>appariement 1:1 (A/B/D/E)</span></div>
<div class="box teal" style="min-width:200px"><b>46</b><span>canal · <b>proxy_etab</b><br>collègue au même UAI (moyenne d'étab.)</span></div>
<div class="box orange" style="min-width:200px"><b>140</b><span>canal · <b>aucune</b> (54 %)<br>défaut → capytale_direct</span></div>
</div>
<div class="row">
<div class="box green" style="min-width:200px"><b>40</b><span>formation · individuel</span></div>
<div class="box teal" style="min-width:200px"><b>27</b><span>formation · proxy_etab</span></div>
<div class="box orange" style="min-width:200px"><b>193</b><span>formation · aucune → « jamais »</span></div>
</div>

<div class="lim">

**Seuls ~28 % des profs (74/260) ont un lien 1:1.** 18 % par **moyenne d'établissement**, **54 % par défaut**. → « capytale_direct » et « jamais formé » sont des **bornes** : elles incluent « on n'a pas vu de trace », pas seulement « prouvé absent ». D'où le ruban **estimé**.

</div>

<div class="why">

**Sankey « formé → profondeur »** : porte sur les **67 profs Capytale tagués formés** (≠ 631 site) → 9 test · 7 sous-seuil · 24 usage unique · 27 usage multiple. La conversion « formation→classe » (59/30/10 %) est, elle, au **grain établissement** (agrégé).

</div>

---

## Ce qu'on ne peut pas suivre (recensement des pertes & biais)

<div class="row">
<div class="box orange"><b>70 %</b><span>comptes site SANS UAI<br>(1 915 / 2 715)</span></div>
<div class="box orange"><b>50 %</b><span>formés sans UAI<br>(314 / 631)</span></div>
<div class="box orange"><b>54 %</b><span>profs Capytale<br>sans trace site (140)</span></div>
<div class="box orange"><b>44 %</b><span>étabs à usage<br>sans compte site (77)</span></div>
</div>
<div class="row">
<div class="box ghost"><b>1 003</b><span>newsletter-only<br>(188 formés)</span></div>
<div class="box ghost"><b>&lt; 27/11/25</b><span>clics invisibles<br>(19,7 % vs 27,5 %)</span></div>
<div class="box ghost"><b>147</b><span>formation date<br>inconnue (1984)</span></div>
<div class="box ghost"><b>67</b><span>« Étranger »<br>0 conversion possible</span></div>
<div class="box ghost"><b>1 466</b><span>élèves « classroom-only »<br>invisibles à l'amont</span></div>
</div>

<div class="lim">

**Le risque principal** : lire un ruban « capytale_direct / jamais formé » comme une **mesure** alors que, pour la moitié des profs, c'est une **absence de trace** (UAI manquant, tracking tardif, pas d'appariement). Tous ces chiffres restent des **ordres de grandeur** au grain établissement, jamais des taux individuels.

</div>

---

## Limite de premier ordre : couverture UAI ⟂ maturité

La conversion « formation→classe » exige l'UAI. Or **la couverture est inversement corrélée au recul** :

| Cohorte | profs | avec UAI | |
|---|---:|---:|---|
| **Lille oct. 2024** (18 mois de recul) | 40 | **6** | le 66,7 % repose sur **6 étabs** |
| Amiens | 19 | **1** | |
| ENS_25 sept. 2025 | 52 | **3** | |
| Présentiel **2026-03** | 39 | **39** | couverture quasi totale… |
| Présentiel **2026-05** | 42 | **41** | …mais **pas encore de recul** |

<div class="lim">

**La tension structurelle** : les cohortes **mûres** (le meilleur recul pour juger « a fini par déboucher ») ont la **pire** couverture UAI ; les cohortes **2026** (couverture quasi parfaite, le formulaire capte l'UAI depuis janv. 2026) **n'ont pas encore déployé**. → précision dégradée ; on n'affirme que la **direction** (concentration ≫ dispersion), corroborée par le terrain (Lille 2024 = 841 élèves, *mesurés*).

</div>

<div class="why">

**Correctif possible (livrable « données »)** : rendre l'UAI **obligatoire** à l'inscription / en formation, ou le récupérer via le roster de formation — réglerait le problème pour l'avenir.

</div>

---

## Les limites honnêtes (les drapeaux assumés)

<div class="row">
<div class="box orange" style="min-width:215px"><b>13/70</b><span>ont un usage Capytale AVANT le contact site → « site→classe » inversé (canal de retour)</span></div>
<div class="box orange" style="min-width:215px"><b>2 UAI</b><span>portent 2 comptes Capytale → étab certain, bon prof non</span></div>
<div class="box orange" style="min-width:215px"><b>conf. B</b><span>UAI 1:1 sans timing → faux positifs (petits collèges)</span></div>
</div>
<div class="row">
<div class="box orange" style="min-width:330px"><b>≥ 27/11/25</b><span>tracking des clics → clics antérieurs sous-captés → sur-attribution à capytale_direct</span></div>
<div class="box orange" style="min-width:330px"><b>non représentatif</b><span>sur-représente les profils engagés → jamais extrapolé en taux de population</span></div>
</div>

<div class="why">

**Doctrine** : *l'individuel confirme le scénario, il ne le mesure pas.*

</div>

---

## Les autres options — et pourquoi pas (pour l'instant)

| Option alternative | Pourquoi écartée |
|---|---|
| **Clé commune via Capytale** (id / e-mail hashé partagé) | Gouvernance/RGPD : anonyme par conception. *La vraie solution long terme.* |
| **Record linkage probabiliste** (Fellegi-Sunter, scoring pondéré) | Aucun champ nominatif côté Capytale à comparer — seuls partagés : UAI + activité + temps |
| **Fuzzy matching** sur nom étab/prof | Pas de nom côté Capytale ; l'UAI est déjà exact |
| **Classifieur ML supervisé** | Pas de **vérité terrain** (aucune paire certifiée pour entraîner/valider) |
| **Score bayésien continu** | Possible, mais opaque — préféré : règles déterministes auditables + conf. A/B |

<div class="why">

**Notre choix** : règles déterministes **conservatrices** (déclenchées sur l'unicité seule), confiance **signalée**, **calibrées** sur cas connus. Transparence & zéro faux positif PII > rappel maximal — vu l'enjeu et l'absence de vérité terrain.

</div>

---

## URLR / Basthon : le même problème, à l'extrême

<div class="why">

**Pourquoi** : Capytale ne voit pas l'usage <b>sans compte</b> (liens courts Basthon). Combien d'usage passe par ce canal ?

</div>

<div class="row">
<div class="box teal"><b>6</b><span>liens</span></div>
<div class="box teal"><b>1 213</b><span>clics</span></div>
<div class="box teal"><b>206</b><span>séances estimées</span></div>
<div class="box"><b>12</b><span>classes (uniques ≥5)</span></div>
<div class="box orange"><b>44</b><span>classes (NAT-élargi)</span></div>
</div>

- Séance estimée = run d'heures actives même lien, débuts &lt; 3 h (même logique que Capytale).
- Taille `n_visiteurs_uniques_urlr` — **non additive**, clé de dédup **non documentée**, **IP anonymisées** → un **NAT d'établissement sous-compte une classe** (clics/unique : 2,97, jusqu'à 6,3).
- Parades : **proxy par clics** (1 clic = 1 participation, exploratoire) + **NAT-suspect** (≤4 uniques mais ≥10 clics).
- Croisement Capytale **national & inféré** (chevauchement temporel) : modes *remplacement* / *dépannage* **compatibles** — jamais une attribution certaine.

---

<!-- _class: part -->

# Synthèse

---

## Les principes transférables

<div class="row">
<div class="box teal" style="min-width:215px"><b>1</b><span>Définitions canoniques centralisées &gt; locales</span></div>
<div class="box teal" style="min-width:215px"><b>2</b><span>Une couche de calcul ; chiffres dans des facts qu'on lit</span></div>
<div class="box teal" style="min-width:215px"><b>3</b><span>Contrats auto (pre-commit + CI) : pas de dérive silencieuse</span></div>
</div>
<div class="row">
<div class="box green" style="min-width:215px"><b>4</b><span>Séparer mesuré / estimé — le dire à chaque chiffre</span></div>
<div class="box green" style="min-width:215px"><b>5</b><span>Grain robuste d'abord ; individuel en bonus, conf. signalée</span></div>
<div class="box green" style="min-width:215px"><b>6</b><span>PII : pseudonymes versionnés, nominatif strictement local</span></div>
</div>

---

## Ce que l'appariement permet — et ne permet pas

| ✅ Permet | ❌ Ne permet pas |
|---|---|
| Mesurer l'effet formation au grain **établissement** | Affirmer « tel prof = telle personne » avec certitude |
| Reconstituer **les deux portes** (site vs Capytale-direct) | Un **taux de conversion** site → classe individuel |
| Figer le **canal** & **timer la formation** des profils | Attribuer une salve URLR à un prof (sauf copie + A/B) |
| **Illustrer** le pipeline par des cas réels | Extrapoler les 70 paires en population |

<div class="lim">

**La phrase à retenir** : *deux mondes sans clé commune, un seul pont qui s'arrête au clic — donc tout lien est inféré, conservateur, et à confiance signalée.*

</div>

---

<!-- _class: lead -->

# Discussion

**Annexes** : code du matcher (`match_individuals.py`), glossaire canonique, rapports Volet 1 / Volet 2 / Typologie / Séances / URLR, dashboards publiés (`mathadata.github.io/enquete-usages`).

*Tous les chiffres : pseudonymisés, sans PII, reproductibles via `rebuild_all.sh`.*
