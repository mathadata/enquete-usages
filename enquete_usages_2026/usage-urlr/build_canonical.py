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


def capytale_observation_end(usages):
    match = re.search(r"(\d{8})", Path(K.capytale_csv()).name)
    if match:
        extraction_day = pd.to_datetime(match.group(1), format="%Y%m%d").tz_localize("Europe/Paris")
        return extraction_day + pd.Timedelta(days=1)
    return usages["created_dt"].max()


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
        })
    sessions = pd.DataFrame(rows)
    sessions["start"] = pd.to_datetime(sessions["start"], utc=True).dt.tz_convert("Europe/Paris")
    sessions["end"] = pd.to_datetime(sessions["end"], utc=True).dt.tz_convert("Europe/Paris")
    sessions = sessions.sort_values(["start", "mathadata_id"])
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
            "modes_observables": counts(obs["mode_historique"]),
        })

    facts = {
        "_meta": {
            "source_links": links_path.name,
            "source_bursts": bursts_path.name,
            "session_rule": "même lien; débuts d'heures actives consécutifs espacés de moins de 3 h",
            "size": "unique_visits URLR recalculé sur la fenêtre complète; proxy de navigateur, pas élève mesuré",
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
            "capytale_sessions": len(cg),
            "capytale_eleves_lignes": int((student_common["mathadata_id"] == mid).sum()),
            "capytale_usage_classe": int((cg["n_eleves"] >= K.CLASSE_MIN).sum()),
            "capytale_seances_riches": int((cg["n_eleves"] >= K.SEANCE_RICHE_MIN).sum()),
            "modes_urlr": counts(ug["mode_historique"]),
        })
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
