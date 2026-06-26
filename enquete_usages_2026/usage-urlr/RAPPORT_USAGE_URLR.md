# Le canal sans compte de MathAData

### Ce que les statistiques URLR/Basthon ajoutent aux analyses Capytale et mathadata.fr

> **Données** : URLR, extraction du **25 juin 2026** ; Capytale, extraction du **19 juin
> 2026** ; Payload mathadata.fr, snapshot du **20 juin 2026**. Période URLR : 25 décembre 2025
> → 25 juin 2026. Six liens courts reliés 1:1 aux six activités communes via leur
> `mathadata_id`.
>
> **Sources de vérité** : `data/facts_urlr.json`, `data/facts_urlr_cross.json`,
> `data/facts_urlr_site.json` et `data/sessions.csv`. Définitions canoniques :
> [`GLOSSAIRE.md`](../transverse/GLOSSAIRE.md).

---

## Note de lecture

URLR ajoute une troisième source, mais **pas un troisième monde d'identités** :

- Capytale mesure des professeurs pseudonymisés, des élèves et des séances ;
- Payload mesure le parcours nominatif sur mathadata.fr, localement et sans publication de PII ;
- URLR mesure des **compteurs agrégés par lien et fenêtre temporelle**, sans visiteur, professeur,
  établissement, IP brute ni événement individuel exportable.

Trois niveaux de preuve doivent rester séparés :

1. **Clics URLR** : mesure additive robuste d'ouvertures du lien court.
2. **Séances Basthon estimées** : salves temporelles reconstruites en fusionnant les heures actives
   du même lien dont les débuts successifs sont espacés de moins de 3 h.
3. **Taille et mode** : indices beaucoup plus fragiles. `unique_visits` est recalculé par URLR sur
   chaque fenêtre complète, mais l'API ne documente pas sa clé de déduplication. URLR indique que
   les statistiques reposent sur des **IP anonymisées** ; une classe derrière l'IP/NAT d'un
   établissement peut donc être fortement sous-comptée.

La variable reste nommée `n_visiteurs_uniques_urlr`, conformément à la source. Elle ne doit jamais
être renommée `n_eleves`.

Dans le contexte MathAData, le **nombre de clics est un meilleur proxy du nombre de participants**
que `unique_visits` : les élèves d'une salle informatique partagent souvent la même IP publique, et
il y a peu de raison qu'un élève clique plusieurs fois sur le lien court. **L'équipe adopte donc la
convention de travail « 1 clic = 1 élève »** pour estimer les participations Basthon — en gardant à
l'esprit qu'il s'agit d'une estimation (participations, pas élèves uniques consolidés) et qu'un
rechargement ou une reconnexion compte comme un clic.

---

## 0. Résumé exécutif

Les statistiques URLR confirment qu'une partie de l'usage réel de MathAData échappe à Capytale.
Les six liens courts ont produit **1 213 clics**, regroupés en **206 séances Basthon estimées**.
Sur la période commune observable, on compte **202 salves URLR** face à **356 séances Capytale**
sur les mêmes six activités.

Mais l'information n'a pas la même qualité :

- **12 salves URLR** atteignent au moins 5 « uniques », contre **175 séances Capytale ≥5 élèves** ;
- **57 salves** comptent au moins 5 clics, **41** au moins 10 et **20** au moins 20 ;
- **10** sont compatibles avec un **remplacement complet** de Capytale ;
- **13** sont compatibles avec un **dépannage** de 1 à 4 participants pendant une séance
  Capytale ;
- **179** restent indéterminées.

Ces 12 salves représentent **6,9 %** du volume de séances Capytale de taille classe détecté sur les
six activités ; les 10 remplacements compatibles, **5,7 %**. Ce sont des **planchers**, pas une
estimation exhaustive du canal Basthon : 157 salves sur 206 n'ont qu'un seul « unique », alors que
certaines comptent plusieurs dizaines de clics.

En appliquant exactement les mêmes règles au **nombre de clics** — sous la convention adoptée
« **1 clic = 1 élève** » — la classification devient **43 remplacements compatibles, 7 dépannages
compatibles et 152 indéterminés**.

En consolidant les deux lectures — **classe Basthon estimée élargie = ≥ 5 uniques OU NAT-suspecte**
(≤ 4 uniques mais ≥ 10 clics) — on détecte **44 séances de taille classe** (12 par les uniques +
32 masquées par un NAT), contre 12 par les uniques seuls. Ces séances totalisent **~933 élèves
estimés** (participations, 1 clic = 1 élève ; ~1 213 clics URLR au total). Ce chiffre est
**estimé**, séparé et **jamais additionné** aux effectifs Capytale ; il est désormais affiché en
note dans la synthèse et le flux.

Les principaux éclairages sont les suivants :

1. **Capytale n'est pas exhaustif du canal classe.** URLR montre un canal sans compte autonome,
   modeste dans les classes détectées mais substantiel en traces temporelles.
2. **Les usages remplacement et dépannage coexistent probablement.** Le signal strict trouve
   10 remplacements compatibles et 13 dépannages compatibles.
3. **La taille est sous-observée.** Le ratio clics / unique de fenêtre passe de 1,4 en janvier à
   6,3 en mars. Une lecture littérale des uniques comme navigateurs ou élèves est injustifiable.
4. **Deux activités concentrent 78 % des clics et tout le signal fondé sur les uniques**, mais pas
   tout le signal classe plausible : avec le seuil exploratoire de 5 clics, **cinq des six
   activités** présentent au moins une salve compatible avec un groupe.
5. **Le signal est scolaire.** 153 salves commencent en semaine entre 7 h et 17 h 59 ; elles
   concentrent **1 067 clics (88 %)** et 11 des 12 salves classe détectées.
6. **L'activité publique est un cas à part.** Elle compte 311 accès Basthon directs côté site,
   dont 253 anonymes (81 %), contre 18 anonymes sur 203 accès directs pour les cinq activités
   verrouillées.
7. **Le tracking de copie est la pièce manquante.** Le snapshot historique contient 9 812 vues de
   pages, 1 225 clics Capytale et 514 accès Basthon directs, mais aucune ouverture de modale ni
   copie de lien court — ces événements commencent seulement à leur déploiement.

---

## 1. URLR complète Capytale sans pouvoir s'y additionner

Sur les six activités communes et la période du 25 décembre 2025 au 19 juin 2026 :

| Source / seuil | Séances |
|---|---:|
| Salves URLR observables | **202** |
| Séances Capytale | **356** |
| URLR ≥5 uniques de fenêtre | **12** |
| URLR ≥5 clics *(proxy exploratoire)* | **57** |
| Capytale ≥5 élèves | **175** |
| URLR ≥10 uniques de fenêtre | **5** |
| URLR ≥10 clics *(proxy exploratoire)* | **41** |
| Capytale ≥10 élèves | **144** |

Le premier contraste — 202 vs 356 — montre que les ouvertures sans compte sont fréquentes. Le
second — 12 vs 175 au seuil classe — montre soit que le canal Basthon sert surtout à des usages
isolés, soit que `unique_visits` sous-compte fortement les groupes derrière une infrastructure
réseau partagée. Les données ne permettent pas de trancher complètement ; les clics élevés pour un
seul unique rendent la seconde explication très plausible dans au moins une partie des cas.

Il serait donc faux :

- d'ajouter 408 « uniques par fenêtre » aux élèves Capytale ;
- de considérer les 206 salves comme 206 classes ;
- ou, inversement, de conclure que seules 12 classes ont utilisé Basthon.

La formulation correcte est : **12 salves de taille classe sont détectées par le critère URLR,
sur un canal dont la taille réelle est probablement sous-observée**.

### Comparaison par activité

| Activité | Clics URLR | Salves URLR | ≥5 uniques | ≥5 clics | Capytale ≥5 |
|---|---:|---:|---:|---:|---:|
| Statistiques — chiffres | **584** | 96 | **5** | **28** | 71 |
| Équation réduite | **367** | 55 | **7** | **20** | 39 |
| Statistiques — fœtus | 179 | 23 | 0 | **7** | 23 |
| Milieu-distance | 47 | 10 | 0 | 1 | 16 |
| Produit scalaire | 20 | 9 | 0 | 1 | 10 |
| Vecteur directeur | 16 | 13 | 0 | 0 | 16 |

URLR renforce la domination des deux portes d'entrée principales déjà visibles dans les autres
volets. Mais l'affirmation « seules deux activités ont un signal classe » est fausse dès que l'on
utilise les clics comme proxy : Statistiques-fœtus présente 7 salves à ≥5 clics, milieu-distance et
produit scalaire une chacune. Les 262 clics des quatre activités moins volumineuses ne correspondent
donc clairement pas à « zéro usage collectif ».

---

## 2. Le diagnostic décisif : `unique_visits` n'est pas une taille de classe fiable

Distribution des 206 salves :

| Uniques URLR dans la fenêtre | Salves |
|---|---:|
| 1 | **157** |
| 2–4 | 37 |
| 5–9 | 7 |
| 10–19 | 3 |
| ≥20 | 2 |

Ainsi, **94 %** des salves sont sous le seuil de 5 uniques. Pourtant, on observe par exemple des
fenêtres avec 46 clics et 1 unique, ou 47 clics et 4 uniques. Ces écarts ne sont pas compatibles
avec une lecture naïve « 1 unique = 1 élève ».

Sur l'ensemble, le ratio est de **2,97 clics par unique de fenêtre**. Il varie fortement par
activité :

| Activité | Clics / unique de fenêtre |
|---|---:|
| Statistiques — fœtus | **7,16** |
| Milieu-distance | 3,62 |
| Statistiques — chiffres | 3,11 |
| Équation réduite | 2,31 |
| Produit scalaire | 2,22 |
| Vecteur directeur | 1,14 |

Cette hétérogénéité est cohérente avec des réseaux/NAT différents selon les établissements et les
séances. Elle rend `unique_visits` impropre à la comparaison des tailles entre activités.

Le diagnostic mensuel va dans le même sens :

| Mois | Clics | Somme des uniques de fenêtre* | Clics / unique | Salves ≥5 |
|---|---:|---:|---:|---:|
| Déc. 2025 | 5 | 3 | 1,67 | 0 |
| Janv. 2026 | 240 | 169 | **1,42** | **7** |
| Févr. | 197 | 66 | 2,98 | **5** |
| Mars | 252 | 40 | **6,30** | 0 |
| Avril | 260 | 57 | 4,56 | 0 |
| Mai | 138 | 40 | 3,45 | 0 |
| Juin | 121 | 33 | 3,67 | 0 |

\* *Somme non dédupliquée entre salves, utilisée uniquement comme diagnostic.*

Les clics restent forts au printemps alors que les salves ≥5 disparaissent. Il est improbable que
le canal classe cesse précisément au moment où l'usage Capytale atteint son pic printanier. La
prudence impose donc de traiter :

- les **clics** comme métrique de volume ;
- les **clics par salve** comme meilleur proxy disponible du nombre de participants, sous
  l'hypothèse explicite de peu de réouvertures ;
- les **salves** comme métrique temporelle ;
- les **uniques** comme borne basse technique ;
- les seuils ≥5/≥10/≥20 comme **détection conservatrice**, pas recensement.

---

## 3. Remplacement complet et dépannage : deux scénarios visibles, aucun attribuable

La classification historique stricte compare chaque salve URLR aux séances Capytale de même
activité dont les intervalles se chevauchent exactement :

| Mode | Définition | Strict | Sensibilité ±1 h |
|---|---|---:|---:|
| Remplacement compatible | URLR ≥5, aucune séance Capytale simultanée | **10** | **10** |
| Dépannage compatible | URLR 1–4, exactement une séance Capytale ≥5 | **13** | **22** |
| Indéterminé | toutes les autres situations | 179 | 170 |

### Pourquoi 179 cas indéterminés ?

La catégorie n'est pas un résidu mystérieux. Elle est presque entièrement causée par le critère
fondé sur les uniques :

| Motif exclusif | Salves |
|---|---:|
| **1–4 uniques sans aucune séance Capytale simultanée** | **169** |
| 1–4 uniques avec une séance Capytale elle-même sous 5 élèves | 6 |
| ≥5 uniques avec une séance Capytale simultanée | 2 |
| 1–4 uniques avec plusieurs séances Capytale candidates | 2 |

Les **169 petites salves sans Capytale** ne peuvent être appelées « dépannage », puisqu'il n'y a
aucune classe Capytale à dépanner ; elles ne peuvent pas non plus être appelées « remplacement »
avec la règle historique, puisqu'elles n'atteignent pas 5 uniques. Or c'est précisément la
configuration attendue si une classe entière partage une IP publique.

En remplaçant le seuil d'uniques par le seuil de clics, **33 de ces situations basculent
principalement vers le remplacement compatible** : le total passe de 10 à 43 remplacements et le
nombre d'indéterminés descend de 179 à 152. Les 152 restants correspondent surtout à de vraies
petites salves de 1–4 clics ou à des parallélismes avec Capytale impossibles à attribuer.

Deux résultats sont robustes :

1. **Le remplacement compatible existe.** Les 10 cas ne changent pas avec ±1 h. Ils forment le
   noyau le plus net d'un usage entièrement hors Capytale.
2. **Le dépannage est plus sensible à l'horloge.** Neuf cas supplémentaires apparaissent à ±1 h.
   C'est cohérent avec des élèves qui rejoignent Basthon au début ou en cours d'une séance
   Capytale, mais cela montre aussi que la coïncidence exacte est un critère fragile.

Ces catégories restent des **compatibilités nationales**. Deux salves simultanées de même activité
peuvent provenir de deux établissements différents. Aucune identité URLR ne permet de les rattacher.

---

## 4. Une temporalité scolaire nette

En définissant les heures scolaires comme un début du lundi au vendredi entre 7 h et 17 h 59 :

- **153 salves sur 206 (74 %)** se situent dans cette fenêtre ;
- elles concentrent **1 067 clics sur 1 213 (88 %)** ;
- et **11 des 12** salves de taille classe détectée.

Les jours les plus actifs sont le mercredi (356 clics), le mardi (328), le jeudi (242) et le lundi
(203). Les week-ends ne représentent que 22 salves et 25 clics. Le canal n'est donc pas seulement
une collection de tests personnels ou d'ouvertures techniques : sa structure temporelle est
fortement compatible avec un usage en contexte scolaire.

Les salves de taille classe détectées se concentrent en janvier-février. Une salve de 40 uniques
apparaît toutefois à 21 h, rappelant qu'une grande vague hors temps scolaire peut être une diffusion
de lien, un test collectif ou un autre usage non attribuable — l'heure seule ne suffit jamais à
qualifier une classe.

---

## 5. Le site : trois gestes distincts avant la séance Basthon

Le snapshot Payload historique observe, sur les six pages activité :

| Événement | Volume | Interprétation |
|---|---:|---|
| Vues de page activité | **9 812** | exposition/intérêt |
| Clics Capytale | **1 225** | intention d'ouvrir le canal ENT |
| Accès Basthon direct | **514** | consultation/test professeur |
| Ouvertures de modale lien court | 0 | tracking prospectif |
| Copies de lien court | 0 | tracking prospectif |
| Salves URLR | **206** | ouvertures ultérieures du lien par ses destinataires |

Ces nombres ne forment pas encore un funnel individuel : les périodes, utilisateurs et grains
diffèrent. Surtout, l'accès Basthon direct et la copie du lien court sont deux gestes opposés :

- **accès direct** : le professeur ouvre lui-même le notebook ;
- **copie** : le professeur prépare la diffusion du lien aux élèves.

Les nouveaux événements `basthon_short_modal_open` et `basthon_short_copy` permettront de séparer
ces gestes. Le tracking commence à son déploiement ; aucun historique de copie ne doit être
reconstruit.

### L'activité publique `3518185` doit rester séparée

| Groupe | Vues page | Clics Capytale | Basthon direct | dont anonymes |
|---|---:|---:|---:|---:|
| Statistiques-chiffres, publique | 3 747 | 598 | **311** | **253 (81 %)** |
| Cinq activités verrouillées | 6 065 | 627 | 203 | **18 (9 %)** |

L'activité publique concentre près de la moitié des clics URLR et surtout la quasi-totalité des
accès Basthon directs anonymes. Elle peut être ouverte par un élève, un professeur non connecté ou
un visiteur quelconque. Elle ne doit jamais servir à estimer un nombre de professeurs.

---

## 6. Attribution future : ce qui deviendra possible

### Ce que les clics Basthon directs permettent déjà — seulement comme candidats

Payload connaît nominativement les utilisateurs connectés qui ont cliqué sur **« Accès direct au
notebook »**. Le snapshot contient **142 utilisateurs connectés distincts** ayant fait au moins un
tel clic. On peut donc produire localement une liste de professeurs ayant testé/consulté Basthon.

En rapprochant ces clics des salves URLR de même activité :

- **57 salves** ont un candidat connecté unique dans les 7 jours, ou à défaut entre 8 et 30 jours ;
- cela représente **31 personnes candidates distinctes** ;
- **11 salves / 6 personnes** disposent aussi d'un appariement individuel Capytale A/B ;
- avec un critère beaucoup plus strict — candidat unique dans les 7 jours et clic direct dans les
  24 h — il ne reste que **10 salves**, dont **2** avec appariement Capytale A/B ;
- sur les cinq activités verrouillées : **33** salves candidates, **8** au critère 24 h, dont
  seulement **2** avec appariement Capytale A/B.

Cette analyse peut être **nominative en interne**, car Payload contient noms et e-mails. Elle ne
permet toutefois pas d'affirmer que la personne a distribué le lien court : le clic direct prouve
seulement qu'elle a ouvert le notebook long depuis la modale. Elle a pu tester sans copier ; à
l'inverse, elle a pu copier sans cliquer sur l'accès direct. Les noms ne doivent donc être présentés
que comme **candidats exploratoires**, jamais comme auteurs attribués des salves.

### Le tracking de copie permettra une attribution nettement plus solide

Après déploiement du tracking de copie, une salve URLR pourra chercher les copies précédentes de la
même activité :

- **confiance A** : une unique personne candidate dans les 7 jours ;
- **confiance B** : une unique personne candidate entre 8 et 30 jours ;
- plusieurs candidats ou aucun : non attribué.

Pour qualifier remplacement ou dépannage au niveau professeur, une seconde condition est
obligatoire : l'utilisateur doit déjà être relié individuellement à Capytale par un appariement A/B
existant. Le proxy établissement `proxy_etab` est interdit.

Les futurs modes seront :

- `depannage_infere` : professeur attribué, séance Capytale simultanée du même professeur et
  activité, URLR 1–4 uniques ;
- `remplacement_infere` : professeur attribué, URLR ≥5 et aucune séance Capytale simultanée de ce
  professeur ;
- sinon `indetermine`.

Même alors, les résultats publiés resteront **agrégés**. Aucune identité candidate, date de copie
individuelle ou identifiant Payload ne doit apparaître dans le dépôt ou la page publique.

---

## 7. Ce que URLR change dans les conclusions transversales

### Ce qui change

1. **Capytale devient une mesure principale mais non exhaustive de l'usage classe.** Une absence de
   trace Capytale n'est plus synonyme d'absence d'activité : une partie peut passer par Basthon.
2. **Le canal « sans compte » doit être suivi séparément.** Il ne correspond ni à
   `via_site`/`capytale_direct`, qui décrivent l'origine des professeurs, ni à une nouvelle
   population identifiable.
3. **Le dépannage devient un mode d'usage explicite.** Une petite salve URLR en parallèle d'une
   séance Capytale peut refléter quelques mots de passe oubliés, une panne ENT ou un accès de
   secours.
4. **Le remplacement complet devient mesurable prospectivement.** Les copies suivies permettront
   de repérer les professeurs qui choisissent Basthon pour toute la classe.
5. **Un volet Basthon estimé est désormais affiché à part.** ~44 séances de taille classe et
   ~933 élèves estimés (1 clic = 1 élève) apparaissent en note dans la synthèse et le flux ; un flag
   pseudonyme `basthon_user` marque dans `profiles_teacher.csv` les 3 professeurs Capytale appariés
   A/B identifiés comme utilisateurs Basthon. Tout reste estimé, séparé et non additionné.

### Ce qui ne change pas

- les nombres de professeurs, élèves et établissements Capytale ;
- `profiles_teacher.csv` et `profiles_teacher_year.csv` ;
- la profondeur d'usage, la réutilisation intra-annuelle et la rétention interannuelle ;
- les effets de formation ;
- les canaux `via_site` / `capytale_direct`.

URLR n'identifie aucune personne et ne peut donc enrichir ces indicateurs sans attribution future
qualifiée. Ajouter ses clics aux élèves ou ses salves aux séances Capytale créerait une fausse
précision.

---

## 8. Recommandations de pilotage

1. **Piloter le funnel page → modale → copie → salve URLR.** C'est le seul trajet qui décrit
   réellement la distribution du lien court aux élèves.
2. **Séparer activité publique et activités verrouillées.** Leurs populations anonymes et leurs
   parcours d'accès sont structurellement différents.
3. **Utiliser les clics comme KPI URLR principal.** Les uniques servent au diagnostic et aux bornes
   basses, pas encore à un KPI de taille de classe.
4. **Auditer `unique_visits` après quelques mois de tracking.** Comparer le nombre de copies
   attribuées, les clics URLR et les tailles Capytale simultanées pour quantifier l'effet NAT/IP.
5. **Suivre séparément dépannage et remplacement.** Le premier mesure la robustesse opérationnelle
   du dispositif ; le second, une vraie substitution au canal ENT.
6. **Ne jamais intégrer URLR aux profils avant preuve suffisante.** Toute attribution reste A/B,
   agrégée et sans `proxy_etab`.

---

## Limites

- L'API URLR ne fournit ni événement individuel, ni IP brute, ni localisation, navigateur,
  référent ou identité via l'endpoint utilisé.
- `unique_visits` est non additif et sa méthode de déduplication n'est pas documentée. URLR précise
  seulement que les IP sont anonymisées.
- Une séance Basthon est une salve reconstruite, pas la durée réelle d'un cours.
- Les chevauchements URLR/Capytale sont nationaux : simultanéité ne signifie pas même classe.
- Les liens existent seulement depuis le 25 décembre 2025 ; aucune comparaison pluriannuelle ou
  mesure de rétention Basthon n'est encore possible.
- Le tracking des copies commence à son déploiement ; les zéros historiques ne signifient pas
  absence de copies.

**Documents liés** : [Volet 1 — Capytale](../usage-capytale/RAPPORT_ENQUETE_USAGES.md) ·
[Volet 2 — site × Capytale](../site-vers-classe/RAPPORT_VOLET2.md) ·
[Synthèse transversale](../transverse/SYNTHESE_FINALE_2026.md) ·
[Schéma URLR](../DONNEES_BRUTES_URLR.md).
