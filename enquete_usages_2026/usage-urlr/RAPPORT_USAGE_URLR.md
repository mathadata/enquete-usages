# Usage sans compte via URLR — état au 25 juin 2026

## Interprétation

URLR constitue bien un canal d'usage complémentaire à Capytale, mais ses volumes ne doivent pas être
additionnés aux élèves Capytale. La source observe des navigateurs anonymes ouvrant un lien court.
Elle permet d'estimer des salves temporelles et de tester leur compatibilité avec deux usages :

- **remplacement compatible** : une salve d'au moins 5 visiteurs uniques sans séance Capytale
  simultanée de la même activité ;
- **dépannage compatible** : une petite salve de 1 à 4 visiteurs uniques pendant une unique séance
  Capytale d'au moins 5 élèves.

## Résultats

Les six liens totalisent **1 213 clics**, regroupés en **206 séances Basthon estimées**. Douze
séances atteignent au moins 5 visiteurs uniques, cinq au moins 10 et deux au moins 20.

Sur les **202 séances** situées dans la période où Capytale est observable :

- **10** sont compatibles avec un remplacement complet ;
- **13** sont compatibles avec un dépannage de quelques élèves ;
- **179** restent indéterminées.

Avec une fenêtre de sensibilité élargie de ±1 h, le remplacement reste à 10 et le dépannage passe à
22. Cette variation confirme que le signal de dépannage dépend davantage du calage horaire ; la
classification stricte reste la référence.

Les usages URLR de taille classe se concentrent sur deux activités : l'équation réduite de droite
(7 séances estimées ≥5) et les statistiques sur les chiffres (5). L'activité publique
`3518185` est analysée séparément dans les faits site : elle concentre notamment 253 accès Basthon
directs anonymes dans le snapshot Payload, ce qui interdit de les interpréter comme des professeurs.

## Base et méthode

Une séance URLR est un run maximal d'heures actives du même lien dont les débuts successifs sont
espacés de moins de 3 h. URLR est ensuite requêté sur toute la fenêtre obtenue afin de calculer
`n_visiteurs_uniques_urlr` sans sommer les uniques horaires.

Le croisement historique cherche les séances Capytale de même `mathadata_id` dont les intervalles
chevauchent exactement la fenêtre URLR. Il est national et agrégé : aucune identité, IP ou
localisation URLR n'est disponible.

Le snapshot Payload observe actuellement **9 812 vues** des six pages activité, **1 225 clics
Capytale** et **514 accès Basthon directs**. Il ne contient encore aucun événement d'ouverture de
modale ou de copie du lien court : ce tracking est prospectif et aucun historique n'est inventé.

Sources de vérité :

- `data/sessions.csv` — une séance URLR estimée ;
- `data/facts_urlr.json` — volumes, tailles et modes ;
- `data/facts_urlr_cross.json` — comparaison avec Capytale sur la période commune ;
- `data/facts_urlr_site.json` — événements Payload et cadre d'attribution future.

## Limites

Un visiteur unique URLR est un proxy de navigateur, pas un élève certain. Une coïncidence temporelle
nationale ne prouve pas que les deux salves appartiennent à la même classe. Inversement, l'absence
de séance Capytale simultanée ne prouve pas qu'aucun élève de la classe n'a utilisé Capytale.

Après déploiement du tracking de copie, une attribution ne sera publiée qu'en agrégat. Elle reposera
sur une copie candidate unique dans les 7 jours (confiance A) ou entre 8 et 30 jours (confiance B),
et sur un appariement individuel site–Capytale A/B existant. Les proxys établissement resteront
exclus de cette attribution.
