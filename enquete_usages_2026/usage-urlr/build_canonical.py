#!/usr/bin/env python3
"""Construit les séances Basthon estimées et les faits URLR × Capytale.

Entrées :
  - public/data/urlr_{links,bursts}_<date>.csv
  - usage-capytale/data/{sessions,usages_enriched}.csv

Sorties versionnables, sans identité :
  - usage-urlr/data/sessions.csv
  - usage-urlr/data/facts_urlr.json
  - usage-urlr/data/facts_urlr_cross.json
"""
from pathlib import Path
import re
import sys

import pandas as pd

ENQ = Path(__file__).resolve().parents[1]
ROOT = ENQ.parent
sys.path.insert(0, str(ENQ))
import enquete_common as K

PUBLIC = ROOT / "public" / "data"
CAP = ENQ / "usage-capytale" / "data"
OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(parents=True, exist_ok=True)

MAPPED_IDS = set(pd.read_csv(ENQ / "urlr_activity_mapping.csv", dtype=str)["mathadata_id"])


def latest(pattern):
    matches = sorted(PUBLIC.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"Aucune entrée {PUBLIC / pattern}")
    return matches[-1]


def overlap(cap, start, end, padding_hours=0):
    pad = pd.Timedelta(hours=padding_hours)
    return cap[(cap["start"] < end + pad) & (cap["end"] >= start - pad)]


def classify(n_unique, candidates):
    if 1 <= n_unique <= 4 and len(candidates) == 1 and int(candidates.iloc[0]["n_eleves"]) >= K.CLASSE_MIN:
        return "compatible_depannage"
    if n_unique >= K.CLASSE_MIN and len(candidates) == 0:
        return "compatible_remplacement"
    return "indetermine"


def counts(series):
    expected = ("compatible_remplacement", "compatible_depannage", "indetermine")
    raw = series.value_counts().to_dict()
    return {name: int(raw.get(name, 0)) for name in expected}


def indeterminate_reason(row):
    n_unique = row["n_visiteurs_uniques_urlr"]
    candidates = row["n_sessions_capytale_simultanees"]
    max_pupils = row["max_eleves_capytale_simultanes"]
    if n_unique >= K.CLASSE_MIN and candidates >= 1:
        return "grande_salve_avec_capytale"
    if 1 <= n_unique <= 4 and candidates == 0:
        return "petite_salve_sans_capytale"
    if 1 <= n_unique <= 4 and candidates > 1:
        return "petite_salve_plusieurs_capytale"
    if 1 <= n_unique <= 4 and candidates == 1 and max_pupils < K.CLASSE_MIN:
        return "petite_salve_avec_capytale_sous_seuil"
    return "autre"


def capytale_observation_end(usages):
    match = re.search(r"(\d{8})", Path(K.capytale_csv()).name)
    if match:
        extraction_day = pd.to_datetime(match.group(1), format="%Y%m%d").tz_localize("Europe/Paris")
        return extraction_day + pd.Timedelta(days=1)
    return usages["created_dt"].max()


def session_diagnostics(sessions):
    size = sessions["n_visiteurs_uniques_urlr"]
    clicks = sessions["clicks"]
    school_hours = (
        (sessions["start"].dt.weekday < 5)
        & sessions["start"].dt.hour.between(7, 17)
    )
    bands = {
        "1": int((size == 1).sum()),
        "2_4": int(size.between(2, 4).sum()),
        "5_9": int(size.between(5, 9).sum()),
        "10_19": int(size.between(10, 19).sum()),
        "20_plus": int((size >= 20).sum()),
    }
    click_bands = {
        "1": int((clicks == 1).sum()),
        "2_4": int(clicks.between(2, 4).sum()),
        "5_9": int(clicks.between(5, 9).sum()),
        "10_19": int(clicks.between(10, 19).sum()),
        "20_29": int(clicks.between(20, 29).sum()),
        "30_plus": int((clicks >= 30).sum()),
    }
    monthly = []
    for month, group in sessions.groupby(sessions["start"].dt.strftime("%Y-%m")):
        unique_sum = int(group["n_visiteurs_uniques_urlr"].sum())
        monthly.append({
            "month": month,
            "sessions": len(group),
            "clicks": int(group["clicks"].sum()),
            "visiteurs_uniques_sommes_non_dedupliquees": unique_sum,
            "clicks_par_unique_de_fenetre": round(
                group["clicks"].sum() / unique_sum, 2
            ) if unique_sum else None,
            "usage_classe_estime": int(group["usage_classe_estime"].sum()),
        })
    return {
        "size_bands": bands,
        "click_bands": click_bands,
        "visiteurs_uniques_sommes_non_dedupliquees": int(size.sum()),
        "clicks_par_unique_de_fenetre": round(clicks.sum() / size.sum(), 2),
        "sessions_un_unique": bands["1"],
        "sessions_sous_5_uniques": int((size < K.CLASSE_MIN).sum()),
        "sessions_5_clics_ou_plus": int((clicks >= K.CLASSE_MIN).sum()),
        "sessions_10_clics_ou_plus": int((clicks >= K.SEANCE_RICHE_MIN).sum()),
        "sessions_20_clics_ou_plus": int((clicks >= K.GRANDE_CLASSE_MIN).sum()),
        # NAT-suspecte : peu d'uniques mais beaucoup de clics → classe derrière une IP commune.
        "sessions_nat_suspect": int(((size <= 4) & (clicks >= K.SEANCE_RICHE_MIN)).sum()),
        # classe Basthon estimée élargie = seuil uniques OU NAT-suspecte (capte les deux types).
        "sessions_classe_uniques_ou_nat": int(
            ((size >= K.CLASSE_MIN) | ((size <= 4) & (clicks >= K.SEANCE_RICHE_MIN))).sum()
        ),
        "school_hours": {
            "definition": "lundi-vendredi, début entre 07:00 et 17:59 Europe/Paris",
            "sessions": int(school_hours.sum()),
            "clicks": int(sessions.loc[school_hours, "clicks"].sum()),
            "usage_classe_estime": int(
                sessions.loc[school_hours, "usage_classe_estime"].sum()
            ),
        },
        "monthly": monthly,
    }


def main():
    links_path = latest("urlr_links_*.csv")
    stamp = links_path.stem.rsplit("_", 1)[-1]
    bursts_path = PUBLIC / f"urlr_bursts_{stamp}.csv"
    if not bursts_path.exists():
        raise FileNotFoundError(
            f"{bursts_path} absent. Relancer fetch_urlr.py pour calculer les uniques par salve."
        )

    links = pd.read_csv(links_path, dtype=str, keep_default_na=False)
    bursts = pd.read_csv(bursts_path, dtype=str, keep_default_na=False)
    cap_sessions = pd.read_csv(CAP / "sessions.csv", dtype=str, keep_default_na=False)
    usages = pd.read_csv(CAP / "usages_enriched.csv", dtype=str, keep_default_na=False)

    for frame, columns in (
        (bursts, ("visits", "unique_visits", "clicks", "scans", "active_hours")),
        (cap_sessions, ("n_eleves",)),
    ):
        for column in columns:
            frame[column] = pd.to_numeric(frame[column], errors="raise").astype(int)
    bursts["start"] = pd.to_datetime(bursts["start"], utc=True).dt.tz_convert("Europe/Paris")
    bursts["end"] = pd.to_datetime(bursts["end"], utc=True).dt.tz_convert("Europe/Paris")
    cap_sessions["start"] = pd.to_datetime(cap_sessions["start"], utc=True).dt.tz_convert("Europe/Paris")
    cap_sessions["end"] = pd.to_datetime(cap_sessions["end"], utc=True).dt.tz_convert("Europe/Paris")
    cap_sessions = cap_sessions[cap_sessions["mathadata_id"].isin(MAPPED_IDS)].copy()

    usages["created_dt"] = pd.to_datetime(usages["created_dt"], utc=True).dt.tz_convert("Europe/Paris")
    cap_observed_end = capytale_observation_end(usages)
    rows = []
    for burst in bursts.itertuples(index=False):
        candidates = cap_sessions[
            (cap_sessions["mathadata_id"] == burst.mathadata_id)
            & (cap_sessions["start"] < burst.end)
            & (cap_sessions["end"] >= burst.start)
        ]
        candidates_pm1 = cap_sessions[
            (cap_sessions["mathadata_id"] == burst.mathadata_id)
            & (cap_sessions["start"] < burst.end + pd.Timedelta(hours=1))
            & (cap_sessions["end"] >= burst.start - pd.Timedelta(hours=1))
        ]
        observable = burst.end <= cap_observed_end
        mode = classify(burst.unique_visits, candidates) if observable else "indetermine"
        mode_pm1 = classify(burst.unique_visits, candidates_pm1) if observable else "indetermine"
        mode_clicks = classify(burst.clicks, candidates) if observable else "indetermine"
        rows.append({
            "session_urlr_id": burst.burst_id,
            "link_id": burst.link_id,
            "code": burst.code,
            "mathadata_id": burst.mathadata_id,
            "mathadata_title": burst.mathadata_title,
            "resource_slug": burst.resource_slug,
            "start": burst.start.isoformat(),
            "end": burst.end.isoformat(),
            "sy": K.school_year(burst.start),
            "date": burst.start.date().isoformat(),
            "active_hours": burst.active_hours,
            "clicks": burst.clicks,
            "n_visiteurs_uniques_urlr": burst.unique_visits,
            "usage_classe_estime": burst.unique_visits >= K.CLASSE_MIN,
            "seance_riche_estimee": burst.unique_visits >= K.SEANCE_RICHE_MIN,
            "grande_classe_estimee": burst.unique_visits >= K.GRANDE_CLASSE_MIN,
            "capytale_observable": observable,
            "n_sessions_capytale_simultanees": len(candidates),
            "max_eleves_capytale_simultanes": int(candidates["n_eleves"].max()) if len(candidates) else 0,
            "mode_historique": mode,
            "n_sessions_capytale_pm1h": len(candidates_pm1),
            "max_eleves_capytale_pm1h": int(candidates_pm1["n_eleves"].max()) if len(candidates_pm1) else 0,
            "mode_sensibilite_pm1h": mode_pm1,
            "mode_exploratoire_clics": mode_clicks,
        })
    sessions = pd.DataFrame(rows)
    sessions["start"] = pd.to_datetime(sessions["start"], utc=True).dt.tz_convert("Europe/Paris")
    sessions["end"] = pd.to_datetime(sessions["end"], utc=True).dt.tz_convert("Europe/Paris")
    sessions = sessions.sort_values(["start", "mathadata_id"])
    sessions["indeterminate_reason"] = ""
    indeterminate_mask = (
        sessions["capytale_observable"]
        & sessions["mode_historique"].eq("indetermine")
    )
    sessions.loc[indeterminate_mask, "indeterminate_reason"] = sessions.loc[
        indeterminate_mask
    ].apply(indeterminate_reason, axis=1)
    sessions["nat_suspect"] = (sessions["n_visiteurs_uniques_urlr"] <= 4) & (
        sessions["clicks"] >= K.SEANCE_RICHE_MIN
    )
    sessions.to_csv(OUT / "sessions.csv", index=False)

    observable_sessions = sessions[sessions["capytale_observable"]].copy()
    by_activity = []
    for mid, group in sessions.groupby("mathadata_id"):
        obs = group[group["capytale_observable"]]
        by_activity.append({
            "mathadata_id": mid,
            "mathadata_title": group.iloc[0]["mathadata_title"],
            "sessions_estimees": len(group),
            "clics": int(group["clicks"].sum()),
            "visiteurs_uniques_par_session_sommes_non_dedupliquees": int(
                group["n_visiteurs_uniques_urlr"].sum()
            ),
            "usage_classe_estime": int(group["usage_classe_estime"].sum()),
            "seance_riche_estimee": int(group["seance_riche_estimee"].sum()),
            "salves_5_clics_ou_plus": int((group["clicks"] >= K.CLASSE_MIN).sum()),
            "salves_10_clics_ou_plus": int((group["clicks"] >= K.SEANCE_RICHE_MIN).sum()),
            "clics_par_unique_de_fenetre": round(
                group["clicks"].sum() / group["n_visiteurs_uniques_urlr"].sum(), 2
            ),
            "modes_observables": counts(obs["mode_historique"]),
            "modes_exploratoires_clics": counts(obs["mode_exploratoire_clics"]),
        })

    indeterminate = observable_sessions[
        observable_sessions["mode_historique"] == "indetermine"
    ].copy()
    facts = {
        "_meta": {
            "source_links": links_path.name,
            "source_bursts": bursts_path.name,
            "session_rule": "même lien; débuts d'heures actives consécutifs espacés de moins de 3 h",
            "size": (
                "unique_visits URLR recalculé sur la fenêtre complète; méthode de déduplication "
                "non documentée par l'API, pas un nombre d'élèves"
            ),
            "unique_visits_caution": (
                "URLR traite les statistiques avec des IP anonymisées sans documenter la clé "
                "d'unicité. Une IP/NAT d'établissement peut donc sous-compter un groupe."
            ),
            "capytale_observed_until": cap_observed_end.isoformat(),
        },
        "links": len(links),
        "activities": int(sessions["mathadata_id"].nunique()),
        "clicks": int(sessions["clicks"].sum()),
        "sessions_estimees": len(sessions),
        "sessions_capytale_observables": len(observable_sessions),
        "usage_classe_estime": int(sessions["usage_classe_estime"].sum()),
        "seances_riches_estimees": int(sessions["seance_riche_estimee"].sum()),
        "grandes_classes_estimees": int(sessions["grande_classe_estimee"].sum()),
        "modes_historiques": counts(observable_sessions["mode_historique"]),
        "modes_sensibilite_pm1h": counts(observable_sessions["mode_sensibilite_pm1h"]),
        "modes_exploratoires_clics": counts(
            observable_sessions["mode_exploratoire_clics"]
        ),
        "indetermines_detail": {
            name: int(value)
            for name, value in indeterminate["indeterminate_reason"].value_counts().items()
        },
        "diagnostics": session_diagnostics(sessions),
        "by_activity": by_activity,
    }
    K.dump_json(facts, OUT / "facts_urlr.json")

    common_start = sessions["start"].min()
    common_end = min(sessions["end"].max(), cap_observed_end)
    cap_common = cap_sessions[
        (cap_sessions["start"] >= common_start) & (cap_sessions["start"] <= common_end)
    ].copy()
    student_common = usages[
        (usages["role"] == "student")
        & usages["mathadata_id"].isin(MAPPED_IDS)
        & (usages["created_dt"] >= common_start)
        & (usages["created_dt"] <= common_end)
    ]
    comparison = []
    for mid in sorted(MAPPED_IDS):
        ug = observable_sessions[observable_sessions["mathadata_id"] == mid]
        cg = cap_common[cap_common["mathadata_id"] == mid]
        comparison.append({
            "mathadata_id": mid,
            "mathadata_title": links.loc[links["mathadata_id"] == mid, "mathadata_title"].iloc[0],
            "urlr_sessions_estimees": len(ug),
            "urlr_clics": int(ug["clicks"].sum()),
            "urlr_visiteurs_uniques_sommes_non_dedupliquees": int(
                ug["n_visiteurs_uniques_urlr"].sum()
            ),
            "urlr_usage_classe_estime": int(ug["usage_classe_estime"].sum()),
            "urlr_seances_riches_estimees": int(ug["seance_riche_estimee"].sum()),
            "urlr_salves_5_clics_ou_plus": int((ug["clicks"] >= K.CLASSE_MIN).sum()),
            "urlr_salves_10_clics_ou_plus": int(
                (ug["clicks"] >= K.SEANCE_RICHE_MIN).sum()
            ),
            "capytale_sessions": len(cg),
            "capytale_eleves_lignes": int((student_common["mathadata_id"] == mid).sum()),
            "capytale_usage_classe": int((cg["n_eleves"] >= K.CLASSE_MIN).sum()),
            "capytale_seances_riches": int((cg["n_eleves"] >= K.SEANCE_RICHE_MIN).sum()),
            "modes_urlr": counts(ug["mode_historique"]),
        })
    cap_class = int((cap_common["n_eleves"] >= K.CLASSE_MIN).sum())
    cap_rich = int((cap_common["n_eleves"] >= K.SEANCE_RICHE_MIN).sum())
    urlr_class = int(observable_sessions["usage_classe_estime"].sum())
    urlr_rich = int(observable_sessions["seance_riche_estimee"].sum())
    urlr_click_class = int((observable_sessions["clicks"] >= K.CLASSE_MIN).sum())
    urlr_click_rich = int((observable_sessions["clicks"] >= K.SEANCE_RICHE_MIN).sum())
    cross = {
        "_meta": {
            "common_start": common_start.isoformat(),
            "common_end": common_end.isoformat(),
            "common_end_exclusive": True,
            "common_last_date": (common_end - pd.Timedelta(days=1)).date().isoformat(),
            "scope": "six activités mappées; comparaison agrégée, sans addition des personnes",
        },
        "urlr_sessions": len(observable_sessions),
        "capytale_sessions": len(cap_common),
        "urlr_usage_classe_estime": urlr_class,
        "capytale_usage_classe": cap_class,
        "urlr_seances_riches_estimees": urlr_rich,
        "capytale_seances_riches": cap_rich,
        "urlr_salves_5_clics_ou_plus": urlr_click_class,
        "urlr_salves_10_clics_ou_plus": urlr_click_rich,
        "ratio_urlr_vs_capytale_usage_classe_pct": round(100 * urlr_class / cap_class, 1),
        "ratio_remplacement_compatible_vs_capytale_classe_pct": round(
            100
            * counts(observable_sessions["mode_historique"])["compatible_remplacement"]
            / cap_class,
            1,
        ),
        "exact_temporal_overlaps": int(
            (observable_sessions["n_sessions_capytale_simultanees"] > 0).sum()
        ),
        "comparison_by_activity": comparison,
    }
    K.dump_json(cross, OUT / "facts_urlr_cross.json")
    print(f"→ {OUT / 'sessions.csv'} ({len(sessions)} séances estimées)")
    print(f"→ {OUT / 'facts_urlr.json'}")
    print(f"→ {OUT / 'facts_urlr_cross.json'}")


if __name__ == "__main__":
    main()
