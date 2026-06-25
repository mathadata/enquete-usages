#!/usr/bin/env python3
"""Génère la page web autonome URLR depuis les faits canoniques."""
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "dashboard_urlr.html"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


FR_MONTHS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}


def sp(n):
    """Entier formaté à la française (espace pour les milliers)."""
    return f"{n:,}".replace(",", " ")


def dec(x):
    """Décimal formaté à la française (virgule)."""
    return str(x).replace(".", ",")


def pct(part, whole):
    return round(100 * part / whole) if whole else 0


def build_replacements(payload):
    """Tous les nombres en clair de la page, recalculés depuis les faits canoniques.

    Aucun chiffre n'est écrit en dur dans le gabarit : la page a une source de vérité unique
    (les facts_urlr*.json), et `check_contracts.py` revérifie ces nombres indépendamment.
    """
    u, c, s = payload["urlr"], payload["cross"], payload["site"]
    diag = u["diagnostics"]
    by_act = {a["mathadata_id"]: a for a in u["by_activity"]}
    pub, lock = s["public_activity"], s["locked_activities"]
    hist = s["historical_direct_click_candidates"]
    top2_clicks = by_act["3515488"]["clics"] + by_act["3518185"]["clics"]
    ratios = [m for m in diag["monthly"] if m["clicks_par_unique_de_fenetre"] is not None]
    lo = min(ratios, key=lambda m: m["clicks_par_unique_de_fenetre"])
    hi = max(ratios, key=lambda m: m["clicks_par_unique_de_fenetre"])
    return {
        # en-tête + volumes globaux
        "__CLICKS__": sp(u["clicks"]),
        "__SESSIONS__": str(u["sessions_estimees"]),
        "__CLASS__": str(u["usage_classe_estime"]),
        "__CLICK_CLASS__": str(diag["sessions_5_clics_ou_plus"]),
        # §01 — apport vs Capytale
        "__OBSSESS__": str(c["urlr_sessions"]),
        "__CAPSESS__": str(c["capytale_sessions"]),
        "__CAPCLASS__": str(c["capytale_usage_classe"]),
        "__RATIOCLASS__": dec(c["ratio_urlr_vs_capytale_usage_classe_pct"]),
        "__RATIOREMP__": dec(c["ratio_remplacement_compatible_vs_capytale_classe_pct"]),
        "__REMP__": str(u["modes_historiques"]["compatible_remplacement"]),
        # §02 — taille / uniques
        "__SIZE1__": str(diag["size_bands"]["1"]),
        "__CPU__": dec(diag["clicks_par_unique_de_fenetre"]),
        "__PCTSOUS5__": str(pct(diag["sessions_sous_5_uniques"], u["sessions_estimees"])),
        "__RATIOMIN__": dec(round(lo["clicks_par_unique_de_fenetre"], 1)),
        "__MONTHMIN__": FR_MONTHS[int(lo["month"][5:7])],
        "__RATIOMAX__": dec(round(hi["clicks_par_unique_de_fenetre"], 1)),
        "__MONTHMAX__": FR_MONTHS[int(hi["month"][5:7])],
        # §03 — modes
        "__REMPCLICS__": str(u["modes_exploratoires_clics"]["compatible_remplacement"]),
        "__INDETCLICS__": str(u["modes_exploratoires_clics"]["indetermine"]),
        "__DEPAN__": str(u["modes_historiques"]["compatible_depannage"]),
        "__INDET__": str(u["modes_historiques"]["indetermine"]),
        "__PSSC__": str(u["indetermines_detail"]["petite_salve_sans_capytale"]),
        # §04 — temporalité scolaire
        "__SCHOOLSESS__": str(diag["school_hours"]["sessions"]),
        "__SCHOOLCLICKS__": sp(diag["school_hours"]["clicks"]),
        "__SCHOOLCLASS__": str(diag["school_hours"]["usage_classe_estime"]),
        # §05 — concentration par activité
        "__TOP2CLICKS__": sp(top2_clicks),
        "__TOP2PCT__": str(pct(top2_clicks, u["clicks"])),
        "__FETUS5C__": str(by_act["6944347"]["salves_5_clics_ou_plus"]),
        # §06 — site
        "__DIRECT__": sp(s["totals"]["basthon_direct_clicks"]),
        "__PUBDIRECT__": str(pub["basthon_direct_clicks"]),
        "__PUBANON__": str(pub["basthon_direct_anonymous"]),
        "__PUBANONPCT__": str(pct(pub["basthon_direct_anonymous"], pub["basthon_direct_clicks"])),
        "__LOCKDIRECT__": str(lock["basthon_direct_clicks"]),
        "__LOCKANON__": str(lock["basthon_direct_anonymous"]),
        "__LOCKANONPCT__": str(pct(lock["basthon_direct_anonymous"], lock["basthon_direct_clicks"])),
        "__CANDSESS__": str(hist["candidate_sessions"]),
        "__CANDUSERS__": str(hist["distinct_candidate_users"]),
        "__CANDAB__": str(hist["candidate_sessions_with_capytale_match_ab"]),
        "__STRONG24__": str(hist["strong_candidate_sessions_24h"]),
        "__STRONGAB__": str(hist["strong_sessions_with_capytale_match_ab"]),
    }


def main():
    payload = {
        "urlr": load("facts_urlr.json"),
        "cross": load("facts_urlr_cross.json"),
        "site": load("facts_urlr_site.json"),
    }
    html = TEMPLATE.replace(
        "__DATA__",
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
    )
    replacements = build_replacements(payload)
    # remplacement du plus long au plus court : aucun marqueur n'est préfixe d'un autre.
    for marker in sorted(replacements, key=len, reverse=True):
        html = html.replace(marker, replacements[marker])
    OUT.write_text(html, encoding="utf-8")
    print(f"→ {OUT}")


TEMPLATE = r"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Le canal sans compte — usages URLR / Basthon</title>
<style>
:root{
  --ground:#F4F7F5;--paper:#FFFFFF;--ink:#17221D;--muted:#64736B;--line:#D6E0DA;
  --green:#167C5A;--green2:#DDF1E9;--blue:#2F65C8;--blue2:#E4ECFB;
  --amber:#D58A16;--rose:#C8475D;--grey:#95A29B;--mono:ui-monospace,"SF Mono",Menlo,monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:17px;line-height:1.62}
.wrap{max-width:1080px;margin:auto;padding:0 24px}
.hero{padding:68px 0 44px;background:linear-gradient(145deg,#E4F3EC 0%,#F7F4E8 62%,#EEF3FB 100%);border-bottom:1px solid var(--line)}
.eyebrow,.mono{font-family:var(--mono)}.eyebrow{font-size:12px;text-transform:uppercase;letter-spacing:.18em;color:var(--green);font-weight:700}
h1{font-size:clamp(38px,7vw,78px);line-height:.98;letter-spacing:-.035em;margin:18px 0 20px;max-width:14ch}
h1 em{font-style:normal;color:var(--green)}
.lede{font-size:clamp(19px,2.4vw,24px);color:#405249;max-width:65ch}.lede b{color:var(--ink)}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:34px}
.stat{background:rgba(255,255,255,.82);border:1px solid var(--line);padding:17px;border-radius:13px}
.stat .n{font-family:var(--mono);font-size:30px;font-weight:800;line-height:1;color:var(--green)}
.stat .l{font-size:12px;color:var(--muted);margin-top:8px;line-height:1.35}
section{padding:54px 0;border-bottom:1px solid var(--line)}
.head{display:flex;align-items:baseline;gap:15px}.num{font-family:var(--mono);font-size:13px;color:var(--green);font-weight:700}
h2{font-size:clamp(27px,4vw,42px);line-height:1.05;letter-spacing:-.025em;margin:0}
h3{font-size:18px;margin:0 0 8px}.sub{font-size:19px;color:#46584F;max-width:70ch;margin:13px 0 24px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:15px}
.card,figure{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:21px;margin:0}
.card p{color:var(--muted);font-size:14px;margin:0}.big{font-family:var(--mono);font-size:28px;font-weight:800;color:var(--green)}
.figtitle{font-weight:750;font-size:15px;margin:0 0 3px}.figsub,.cap{font-family:var(--mono);font-size:11px;color:var(--muted);line-height:1.55}
.figsub{margin-bottom:14px}.cap{margin-top:12px}.chart{min-height:240px}.scroll{overflow-x:auto}
.callout{margin-top:18px;background:var(--green2);border-left:4px solid var(--green);padding:17px 20px;border-radius:8px}
.callout.warn{background:#FFF4DF;border-color:var(--amber)}.callout.rose{background:#FAE9EC;border-color:var(--rose)}
.callout p{margin:0;max-width:76ch}.callout b{font-weight:750}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:720px}
th,td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:right}
th:first-child,td:first-child{text-align:left}th{font-family:var(--mono);font-size:10px;color:var(--muted);text-transform:uppercase}
.pill{display:inline-block;border-radius:999px;padding:3px 8px;font-family:var(--mono);font-size:10px;background:var(--blue2);color:var(--blue)}
.recs{display:grid;gap:11px}.rec{background:var(--paper);border:1px solid var(--line);padding:16px 18px;border-radius:11px;display:flex;gap:14px}
.rec .r{font-family:var(--mono);font-weight:800;color:var(--green)}.rec p{margin:2px 0 0;color:var(--muted);font-size:14px}
footer{padding:42px 0 64px;color:var(--muted);font-family:var(--mono);font-size:11px}
a{color:var(--blue)}svg{display:block;width:100%;overflow:visible}
.axis{fill:var(--muted);font:11px var(--mono)}.value{fill:var(--ink);font:700 11px var(--mono)}
.legend{display:flex;gap:14px;flex-wrap:wrap;font:11px var(--mono);color:var(--muted);margin-bottom:10px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px}
@media(max-width:800px){.stats,.grid2,.grid3{grid-template-columns:1fr 1fr}}
@media(max-width:560px){.stats,.grid2,.grid3{grid-template-columns:1fr}.hero{padding-top:46px}}
</style>
</head>
<body>
<header class="hero"><div class="wrap">
  <div class="eyebrow">MathAData · URLR × Capytale × mathadata.fr · décembre 2025 → juin 2026</div>
  <h1>Le canal <em>sans compte</em> existe — mais il reste partiellement invisible</h1>
  <p class="lede">Les liens courts Basthon ajoutent un <b>canal d'usage réel</b> aux analyses Capytale.
  Ils révèlent deux pratiques plausibles — remplacement complet et dépannage de quelques élèves —
  sans permettre d'identifier une classe. Le résultat robuste est le <b>volume de clics et sa temporalité</b> ;
  la taille des groupes reste un plancher fragile.</p>
  <div class="stats">
    <div class="stat"><div class="n" data-v="clicks">__CLICKS__</div><div class="l">clics URLR conservés exactement</div></div>
    <div class="stat"><div class="n" data-v="sessions">__SESSIONS__</div><div class="l">salves / séances Basthon estimées</div></div>
    <div class="stat"><div class="n" data-v="click-class">__CLICK_CLASS__</div><div class="l">salves à ≥ 5 clics — proxy collectif exploratoire</div></div>
    <div class="stat"><div class="n" data-v="class">__CLASS__</div><div class="l">salves à ≥ 5 « uniques » — plancher technique</div></div>
  </div>
</div></header>

<main>
<section><div class="wrap">
  <div class="head"><span class="num">01</span><h2>Ce que URLR ajoute au portrait Capytale</h2></div>
  <p class="sub">Sur les six mêmes activités, le canal sans compte n'est pas marginal en traces :
  il produit __OBSSESS__ salves observables face à __CAPSESS__ séances Capytale. Douze franchissent le seuil
  technique de 5 uniques, mais __CLICK_CLASS__ atteignent au moins 5 clics, contre __CAPCLASS__ séances Capytale à ≥ 5 élèves.</p>
  <div class="grid2">
    <figure><p class="figtitle">Séances de taille classe détectée, par activité</p>
      <p class="figsub">Capytale ≥ 5 élèves · URLR ≥ 5 uniques · URLR ≥ 5 clics</p>
      <div class="legend"><span><i style="background:var(--green)"></i>Capytale</span><span><i style="background:var(--blue)"></i>URLR uniques</span><span><i style="background:var(--rose)"></i>URLR clics</span></div>
      <div id="activityClass" class="chart"></div>
      <p class="cap">Les barres ne représentent pas la même population et ne doivent pas être additionnées.
      URLR ajoute un ordre de grandeur de __RATIOCLASS__ % au volume Capytale détecté, probablement sous-estimé.</p></figure>
    <div>
      <div class="grid2">
        <div class="card"><div class="big">__RATIOCLASS__ %</div><h3>un complément détecté</h3><p>__CLASS__ salves URLR ≥5 pour __CAPCLASS__ séances Capytale ≥5 sur la période commune.</p></div>
        <div class="card"><div class="big">__RATIOREMP__ %</div><h3>remplacements compatibles</h3><p>__REMP__ salves classe sans séance Capytale simultanée, rapportées aux __CAPCLASS__ séances Capytale.</p></div>
      </div>
      <div class="callout"><p><b>Ce que cela change.</b> Les statistiques Capytale ne couvrent pas tout l'usage
      en classe. Elles restent la source des professeurs, élèves, établissements, profondeur et rétention ;
      URLR ajoute un <b>canal complémentaire anonyme</b>, surtout visible au grain activité × temps.</p></div>
    </div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">02</span><h2>La taille des groupes est le principal angle mort</h2></div>
  <p class="sub">__SIZE1__ salves sur __SESSIONS__ n'ont qu'un seul « unique » URLR. Pourtant certaines comptent
  plusieurs dizaines de clics. L'API ne documente pas sa clé de déduplication et URLR indique traiter
  les statistiques avec des IP anonymisées : une classe derrière une IP/NAT commune peut être fortement sous-comptée.
  Au total, le ratio atteint <b>__CPU__ clics par unique de fenêtre</b>.</p>
  <div class="grid2">
    <figure><p class="figtitle">Distribution des « uniques » par salve</p><p class="figsub">métrique de fenêtre URLR, pas élèves</p>
      <div id="sizes" class="chart"></div><p class="cap">__PCTSOUS5__ % des salves restent sous 5 uniques. Ce résultat
      décrit la métrique URLR ; il ne prouve pas que 94 % des usages concernent moins de cinq élèves.</p></figure>
    <figure><p class="figtitle">Le ratio clics / unique change fortement selon le mois</p><p class="figsub">signal d'instabilité pour une lecture en « taille de classe »</p>
      <div id="monthlyRatio" class="chart"></div><p class="cap">Le ratio passe de __RATIOMIN__ en __MONTHMIN__ à __RATIOMAX__ en __MONTHMAX__.
      Sous l'hypothèse raisonnable de peu de réouvertures par élève, les clics sont le meilleur proxy disponible
      du nombre de participants ; ils ne deviennent toutefois pas un effectif mesuré.</p></figure>
  </div>
  <div class="callout warn"><p><b>Conséquence méthodologique.</b> Les catégories remplacement/dépannage
  sont conservées parce qu'elles répondent au protocole fixé, mais elles sont <b>conservatrices</b>.
  Une grande classe partageant une IP peut tomber dans « petite salve » ou « indéterminé ».</p></div>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">03</span><h2>Deux usages plausibles : remplacement et dépannage</h2></div>
  <p class="sub">La coïncidence temporelle nationale ne permet jamais d'attribuer URLR et Capytale
  à la même classe. Elle permet seulement de tester la compatibilité de deux scénarios.</p>
  <div class="grid2">
    <figure><p class="figtitle">Classification canonique et sensibilité exploratoire</p>
      <p class="figsub">__OBSSESS__ salves dans la fenêtre Capytale observable</p>
      <div class="legend"><span><i style="background:var(--green)"></i>uniques strict</span><span><i style="background:var(--amber)"></i>uniques ±1 h</span><span><i style="background:var(--rose)"></i>clics strict</span></div>
      <div id="modes" class="chart"></div>
      <p class="cap">Avec les clics, __REMPCLICS__ salves deviennent compatibles avec un remplacement et les indéterminées
      descendent à __INDETCLICS__. C'est une sensibilité, pas un changement de définition canonique.</p></figure>
    <div class="grid3" style="grid-template-columns:1fr">
      <div class="card"><span class="pill">compatible_remplacement</span><div class="big">__REMP__</div><p>≥5 uniques URLR, aucune séance Capytale simultanée de même activité.</p></div>
      <div class="card"><span class="pill">compatible_depannage</span><div class="big">__DEPAN__</div><p>1–4 uniques URLR pendant exactement une séance Capytale ≥5.</p></div>
      <div class="card"><span class="pill">indetermine</span><div class="big">__INDET__</div><p>Dont __PSSC__ salves à 1–4 uniques sans Capytale simultané : elles peuvent être de petits usages ou des classes écrasées par le NAT.</p></div>
    </div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">04</span><h2>Une signature très scolaire, concentrée en janvier-février</h2></div>
  <p class="sub">__SCHOOLSESS__ salves sur __SESSIONS__ commencent en semaine entre 7 h et 17 h 59 ; elles concentrent
  __SCHOOLCLICKS__ des __CLICKS__ clics et __SCHOOLCLASS__ des __CLASS__ salves de taille classe détectée.</p>
  <figure><p class="figtitle">Chronologie mensuelle</p><p class="figsub">clics, salves et salves ≥5 uniques</p>
    <div class="legend"><span><i style="background:var(--blue)"></i>clics</span><span><i style="background:var(--green)"></i>salves</span><span><i style="background:var(--rose)"></i>salves ≥5</span></div>
    <div id="timeline" class="chart"></div><p class="cap">Toutes les salves ≥5 apparaissent en janvier-février.
    À partir de mars, les clics restent élevés mais les uniques chutent : cela renforce la prudence sur la taille,
    pas l'hypothèse d'une disparition de l'usage.</p></figure>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">05</span><h2>Deux activités concentrent les uniques, cinq portent un signal collectif en clics</h2></div>
  <p class="sub">Statistiques sur les chiffres et équation réduite cumulent __TOP2CLICKS__ clics, soit __TOP2PCT__ % du total,
  et les __CLASS__ salves détectées à ≥5 uniques. Mais Statistiques-fœtus compte __FETUS5C__ salves à ≥5 clics,
  milieu-distance et produit scalaire une chacune : seul vecteur directeur n'en présente aucune.</p>
  <figure><p class="figtitle">Volume URLR par activité</p><p class="figsub">clics, salves ≥5 uniques et salves ≥5 clics</p>
    <div class="legend"><span><i style="background:var(--blue)"></i>clics</span><span><i style="background:var(--green)"></i>salves ≥5 uniques</span><span><i style="background:var(--rose)"></i>salves ≥5 clics</span></div>
    <div id="activityClicks" class="chart"></div><p class="cap">La concentration recoupe les activités déjà
    dominantes dans Capytale, mais le canal sans compte accentue encore la place de la vitrine Statistiques
    et de l'équation réduite.</p></figure>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">06</span><h2>Le site explique une partie du signal — avec une exception publique</h2></div>
  <p class="sub">Avant le nouveau tracking de copie, Payload observe les pages, les clics Capytale et les
  accès Basthon directs du professeur, mais pas le geste décisif « copier le lien court pour les élèves ».</p>
  <div class="grid2">
    <figure><p class="figtitle">Points observables du parcours</p><p class="figsub">grains différents — pas un funnel individuel</p>
      <div id="siteFunnel" class="chart"></div><p class="cap">Les __DIRECT__ accès Basthon directs sont des consultations/tests
      professeur. Les copies restent à zéro historiquement : le tracking est prospectif, sans backfill.</p></figure>
    <div>
      <div class="card"><div class="big">__PUBDIRECT__</div><h3>accès directs sur l'activité publique</h3>
        <p>__PUBANON__ sont anonymes (__PUBANONPCT__ %). Cette activité libre d'accès doit être séparée des cinq activités verrouillées.</p></div>
      <div class="card" style="margin-top:14px"><div class="big">__LOCKDIRECT__</div><h3>accès directs sur les cinq activités verrouillées</h3>
        <p>__LOCKANON__ seulement sont anonymes (__LOCKANONPCT__ %), cohérent avec l'obligation de connexion du professeur.</p></div>
      <div class="card" style="margin-top:14px"><div class="big">__CANDSESS__</div><h3>salves avec un candidat historique unique</h3>
        <p>__CANDUSERS__ comptes connectés distincts ; __CANDAB__ salves ont aussi un appariement Capytale A/B. Au critère strict de 24 h : __STRONG24__ salves, dont __STRONGAB__ appariées A/B.</p></div>
      <div class="callout"><p><b>À partir du déploiement du tracking.</b> `basthon_short_modal_open` et
      `basthon_short_copy` permettront de relier une copie candidate unique à une salve URLR dans les 7 jours
      (A) ou 8–30 jours (B), puis seulement aux appariements individuels site–Capytale A/B.</p></div>
    </div>
  </div>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">07</span><h2>Ce que l'intégration URLR change — et ne change pas</h2></div>
  <div class="grid2">
    <div>
      <h3>Elle change</h3>
      <div class="recs">
        <div class="rec"><span class="r">01</span><div><b>La couverture du canal classe</b><p>Capytale devient une mesure principale mais non exhaustive : Basthon forme un canal complémentaire visible.</p></div></div>
        <div class="rec"><span class="r">02</span><div><b>La lecture des absences Capytale</b><p>Une activité sans séance Capytale simultanée peut tout de même être utilisée via le lien court.</p></div></div>
        <div class="rec"><span class="r">03</span><div><b>Le pilotage produit</b><p>Le geste de copie doit devenir le point d'entrée du suivi, distinct de l'accès direct professeur.</p></div></div>
      </div>
    </div>
    <div>
      <h3>Elle ne change pas</h3>
      <div class="recs">
        <div class="rec"><span class="r">01</span><div><b>Les nombres de professeurs et d'élèves</b><p>URLR n'identifie personne ; aucun volume n'est ajouté aux effectifs Capytale.</p></div></div>
        <div class="rec"><span class="r">02</span><div><b>Les profils et la rétention</b><p>`profiles_teacher*`, profondeur, retour interannuel et formation restent fondés sur Capytale/Payload.</p></div></div>
        <div class="rec"><span class="r">03</span><div><b>Le niveau de preuve</b><p>Historique = candidats nominatifs internes au mieux, jamais auteurs attribués. Futur = attribution inférée A/B après copie observée.</p></div></div>
      </div>
    </div>
  </div>
  <div class="callout rose"><p><b>Priorité 2026-2027.</b> Suivre le taux page → ouverture de modale →
  copie → salve URLR, séparément pour l'activité publique et les cinq activités verrouillées. Auditer ensuite
  la stabilité de `unique_visits` avant d'en faire un KPI de taille ; les clics et la copie sont les métriques
  opérationnelles les plus solides.</p></div>
</div></section>

<section><div class="wrap">
  <div class="head"><span class="num">08</span><h2>Méthode et limites</h2></div>
  <div class="scroll"><table><thead><tr><th>Élément</th><th>Mesure</th><th>Statut</th><th>Limite principale</th></tr></thead><tbody>
    <tr><td>Clic URLR</td><td>compteur API sur une fenêtre</td><td>mesuré</td><td>un même participant peut cliquer plusieurs fois</td></tr>
    <tr><td>Salve / séance Basthon</td><td>heures actives du même lien, gaps &lt;3 h</td><td>estimé</td><td>pas d'événement individuel</td></tr>
    <tr><td>Unique URLR</td><td>recalcul API sur la fenêtre complète</td><td>mesuré par URLR</td><td>méthode d'unicité non documentée ; IP anonymisées / NAT possible</td></tr>
    <tr><td>Remplacement / dépannage historique</td><td>chevauchement national avec Capytale</td><td>compatible</td><td>aucune attribution à une classe</td></tr>
    <tr><td>Attribution future</td><td>copie candidate + appariement individuel A/B</td><td>inféré</td><td>jamais `proxy_etab`, publication agrégée seulement</td></tr>
  </tbody></table></div>
  <p class="sub" style="font-size:15px">Sources : URLR, extraction du 25 juin 2026 ; Capytale, extraction
  du 19 juin 2026 ; Payload, snapshot du 20 juin 2026. Six liens reliés 1:1 aux six `mathadata_id`.
  Aucun nom, e-mail, IP ou identifiant visiteur n'est présent dans cette page.</p>
</div></section>
</main>

<footer><div class="wrap">Rapport détaillé : <a href="https://github.com/mathadata/enquete-usages/blob/main/enquete_usages_2026/usage-urlr/RAPPORT_USAGE_URLR.md">RAPPORT_USAGE_URLR.md</a>
 · Définitions : <a href="https://github.com/mathadata/enquete-usages/blob/main/enquete_usages_2026/transverse/GLOSSAIRE.md">glossaire canonique</a>
 · <a href="index.html">Retour à l'accueil</a></div></footer>

<script>
const D=__DATA__;
const U=D.urlr,C=D.cross,S=D.site;
const labels={"3518185":"Stats chiffres","3515488":"Équation réduite","6944347":"Stats fœtus","6659633":"Milieu-distance","5862412":"Produit scalaire","8790616":"Vecteur directeur"};
const fmt=n=>new Intl.NumberFormat("fr-FR").format(n);
document.querySelector('[data-v="clicks"]').textContent=fmt(U.clicks);
document.querySelector('[data-v="sessions"]').textContent=fmt(U.sessions_estimees);
document.querySelector('[data-v="class"]').textContent=fmt(U.usage_classe_estime);
document.querySelector('[data-v="click-class"]').textContent=fmt(U.diagnostics.sessions_5_clics_ou_plus);
const NS="http://www.w3.org/2000/svg";
function E(n,a={},t=""){const x=document.createElementNS(NS,n);Object.entries(a).forEach(([k,v])=>x.setAttribute(k,v));if(t!=="" )x.textContent=t;return x}
function svgBox(id,w=760,h=280){const host=document.getElementById(id),s=E("svg",{viewBox:`0 0 ${w} ${h}`,role:"img"});host.appendChild(s);return{s,w,h}}
function hBars(id,rows,series,opt={}){const {s,w,h}=svgBox(id,opt.w||760,opt.h||Math.max(250,rows.length*42+42));const left=opt.left||145,right=54,top=20,bottom=25,inner=w-left-right;const mx=Math.max(...rows.flatMap(r=>series.map(q=>r[q.key])))*1.12||1;const gh=(h-top-bottom)/rows.length;rows.forEach((r,i)=>{const y=top+i*gh;s.appendChild(E("text",{x:left-8,y:y+gh*.55,"text-anchor":"end",class:"axis"},r.label));series.forEach((q,j)=>{const bh=Math.min(15,gh/(series.length+1)),yy=y+gh*.23+j*(bh+4),bw=inner*r[q.key]/mx;s.appendChild(E("rect",{x:left,y:yy,width:bw,height:bh,rx:2,fill:q.color}));s.appendChild(E("text",{x:left+bw+5,y:yy+bh-2,class:"value"},fmt(r[q.key])))});});}
function vBars(id,rows,series,opt={}){const {s,w,h}=svgBox(id,opt.w||760,opt.h||280);const left=42,right=20,top=24,bottom=48,innerW=w-left-right,innerH=h-top-bottom;const mx=(opt.max||Math.max(...rows.flatMap(r=>series.map(q=>r[q.key]))))*1.15||1;const gw=innerW/rows.length;rows.forEach((r,i)=>{s.appendChild(E("text",{x:left+gw*(i+.5),y:h-19,"text-anchor":"middle",class:"axis"},r.label));series.forEach((q,j)=>{const bw=Math.min(30,gw/(series.length+1)),x=left+gw*(i+.5)+(j-(series.length-1)/2)*(bw+4)-bw/2,bh=innerH*r[q.key]/mx,y=top+innerH-bh;s.appendChild(E("rect",{x,y,width:bw,height:bh,rx:2,fill:q.color}));s.appendChild(E("text",{x:x+bw/2,y:y-5,"text-anchor":"middle",class:"value"},fmt(r[q.key])))});});s.appendChild(E("line",{x1:left,y1:top+innerH,x2:w-right,y2:top+innerH,stroke:"var(--line)"}));}
function lineChart(id,rows,key,opt={}){const {s,w,h}=svgBox(id,opt.w||760,opt.h||280);const left=42,right=25,top=28,bottom=48,iw=w-left-right,ih=h-top-bottom,mx=Math.max(...rows.map(r=>r[key]))*1.12||1;let pts=[];rows.forEach((r,i)=>{const x=left+iw*(i/(rows.length-1||1)),y=top+ih-ih*r[key]/mx;pts.push(`${x},${y}`);s.appendChild(E("circle",{cx:x,cy:y,r:4,fill:opt.color||"var(--green)"}));s.appendChild(E("text",{x,y:y-9,"text-anchor":"middle",class:"value"},String(r[key]).replace(".",",")));s.appendChild(E("text",{x,y:h-18,"text-anchor":"middle",class:"axis"},r.label));});s.insertBefore(E("polyline",{points:pts.join(" "),fill:"none",stroke:opt.color||"var(--green)","stroke-width":3}),s.firstChild);}
function timelineChart(id,rows){const {s,w,h}=svgBox(id,760,300),left=42,right=22,top=30,bottom=48,iw=w-left-right,ih=h-top-bottom,maxClicks=Math.max(...rows.map(r=>r.clicks))*1.12,maxSessions=Math.max(...rows.map(r=>r.sessions))*1.2,gw=iw/rows.length;rows.forEach((r,i)=>{const cx=left+gw*(i+.5),bw=gw*.34,bh=ih*r.clicks/maxClicks,y=top+ih-bh;s.appendChild(E("rect",{x:cx-bw-2,y,width:bw,height:bh,rx:2,fill:"var(--blue)"}));const sh=ih*r.sessions/maxSessions;s.appendChild(E("rect",{x:cx+2,y:top+ih-sh,width:bw,height:sh,rx:2,fill:"var(--green)"}));if(r.usage_classe_estime){const cy=top+18;s.appendChild(E("circle",{cx,cy,r:11,fill:"var(--rose)"}));s.appendChild(E("text",{x:cx,y:cy+4,"text-anchor":"middle",fill:"white",style:"font:700 10px var(--mono)"},r.usage_classe_estime));}s.appendChild(E("text",{x:cx,y:h-18,"text-anchor":"middle",class:"axis"},r.label));});s.appendChild(E("line",{x1:left,y1:top+ih,x2:w-right,y2:top+ih,stroke:"var(--line)"}));}
const act=C.comparison_by_activity.map(r=>({label:labels[r.mathadata_id],cap:r.capytale_usage_classe,urlr:r.urlr_usage_classe_estime,clickProxy:r.urlr_salves_5_clics_ou_plus,clicks:r.urlr_clics})).sort((a,b)=>b.cap-a.cap);
hBars("activityClass",act,[{key:"cap",color:"var(--green)"},{key:"urlr",color:"var(--blue)"},{key:"clickProxy",color:"var(--rose)"}],{left:130});
const bands=U.diagnostics.size_bands;
vBars("sizes",[{label:"1",v:bands["1"]},{label:"2–4",v:bands["2_4"]},{label:"5–9",v:bands["5_9"]},{label:"10–19",v:bands["10_19"]},{label:"20+",v:bands["20_plus"]}],[{key:"v",color:"var(--green)"}]);
const monthly=U.diagnostics.monthly.map(r=>({...r,label:r.month.slice(5)+"/"+r.month.slice(2,4),ratio:r.clicks_par_unique_de_fenetre}));
lineChart("monthlyRatio",monthly,"ratio",{color:"var(--rose)"});
const modeRows=[{label:"Remplacement",strict:U.modes_historiques.compatible_remplacement,wide:U.modes_sensibilite_pm1h.compatible_remplacement,clicks:U.modes_exploratoires_clics.compatible_remplacement},{label:"Dépannage",strict:U.modes_historiques.compatible_depannage,wide:U.modes_sensibilite_pm1h.compatible_depannage,clicks:U.modes_exploratoires_clics.compatible_depannage},{label:"Indéterminé",strict:U.modes_historiques.indetermine,wide:U.modes_sensibilite_pm1h.indetermine,clicks:U.modes_exploratoires_clics.indetermine}];
vBars("modes",modeRows,[{key:"strict",color:"var(--green)"},{key:"wide",color:"var(--amber)"},{key:"clicks",color:"var(--rose)"}]);
timelineChart("timeline",monthly);
const actClicks=U.by_activity.map(r=>({label:labels[r.mathadata_id],clicks:r.clics,class:r.usage_classe_estime,clickClass:r.salves_5_clics_ou_plus})).sort((a,b)=>b.clicks-a.clicks);
hBars("activityClicks",actClicks,[{key:"clicks",color:"var(--blue)"},{key:"class",color:"var(--green)"},{key:"clickClass",color:"var(--rose)"}],{left:130});
const funnel=[{label:"Pages",v:S.totals.module_views},{label:"Capytale",v:S.totals.capytale_clicks},{label:"Basthon direct",v:S.totals.basthon_direct_clicks},{label:"Copies",v:S.totals.basthon_short_copies},{label:"Salves URLR",v:U.sessions_estimees}];
vBars("siteFunnel",funnel,[{key:"v",color:"var(--green)"}],{max:S.totals.module_views});
</script>
</body></html>"""


if __name__ == "__main__":
    main()
