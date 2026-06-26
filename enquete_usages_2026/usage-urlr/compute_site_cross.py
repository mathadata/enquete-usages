#!/usr/bin/env python3
"""Croise URLR avec le snapshot Payload local, sans publier d'identité.

Produit `usage-urlr/data/facts_urlr_site.json`. Les appariements futurs utilisent uniquement les
paires individuelles A/B déjà validées ; aucun proxy établissement n'identifie un professeur.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import sys

import pandas as pd

ENQ = Path(__file__).resolve().parents[1]
ROOT = ENQ.parent
sys.path.insert(0, str(ENQ))
import enquete_common as K

OUT = Path(__file__).resolve().parent / "data"
PUBLIC = ROOT / "public" / "data"
LOCAL = Path(K.LOCAL)
SNAP = Path(K.snapshot())


def relation_id(value):
    if isinstance(value, dict):
        return value.get("id")
    return value


def resource_key(url):
    parsed = urlsplit(url)
    return unquote(f"{parsed.hostname}{parsed.path}{parsed.query and '?' + parsed.query}")


def counts(series, values):
    raw = series.value_counts().to_dict()
    return {value: int(raw.get(value, 0)) for value in values}


def main():
    required = [SNAP / f"{name}.json" for name in ("users", "events", "consultation_rss")]
    if not all(path.exists() for path in required):
        raise FileNotFoundError(f"Snapshot Payload incomplet: {SNAP}")

    links_path = sorted(PUBLIC.glob("urlr_links_*.csv"))[-1]
    links = pd.read_csv(links_path, dtype=str, keep_default_na=False)
    sessions = pd.read_csv(OUT / "sessions.csv", dtype=str, keep_default_na=False)
    sessions["start"] = pd.to_datetime(sessions["start"], utc=True)
    sessions["end"] = pd.to_datetime(sessions["end"], utc=True)
    sessions["n_visiteurs_uniques_urlr"] = pd.to_numeric(
        sessions["n_visiteurs_uniques_urlr"], errors="raise"
    ).astype(int)

    users = json.load(open(SNAP / "users.json", encoding="utf-8"))
    excluded = {str(user["id"]) for user in users if user.get("exclude_from_analytics")}
    events = json.load(open(SNAP / "events.json", encoding="utf-8"))
    rss = json.load(open(SNAP / "consultation_rss.json", encoding="utf-8"))
    slug_to_mid = dict(zip(links["resource_slug"], links["mathadata_id"]))
    direct_keys = {
        row.mathadata_id: resource_key(row.destination_url) for row in links.itertuples()
    }

    activity = {
        mid: {
            "mathadata_id": mid,
            "mathadata_title": links.loc[links["mathadata_id"] == mid, "mathadata_title"].iloc[0],
            "public": mid == "3518185",
            "module_views": 0,
            "module_view_users": set(),
            "module_view_sessions": set(),
            "capytale_clicks": 0,
            "capytale_click_users": set(),
            "basthon_direct_clicks": 0,
            "basthon_direct_users": set(),
            "basthon_direct_anonymous": 0,
            "modal_opens": 0,
            "short_copies": 0,
        }
        for mid in links["mathadata_id"]
    }
    copies = []
    for event in events:
        event_type = event.get("eventType")
        metadata = event.get("metadata") or {}
        user = relation_id(event.get("user"))
        session = relation_id(event.get("session"))
        if user is not None and str(user) in excluded:
            continue
        if event_type == "module_view":
            mid = slug_to_mid.get(metadata.get("moduleSlug"))
            if mid:
                activity[mid]["module_views"] += 1
                if user is not None:
                    activity[mid]["module_view_users"].add(str(user))
                if session is not None:
                    activity[mid]["module_view_sessions"].add(str(session))
        elif event_type in ("basthon_short_modal_open", "basthon_short_copy"):
            mid = str(metadata.get("mathadataId") or "")
            if mid not in activity:
                continue
            key = "modal_opens" if event_type.endswith("modal_open") else "short_copies"
            activity[mid][key] += 1
            if event_type == "basthon_short_copy" and user is not None:
                copies.append({
                    "mathadata_id": mid,
                    "created_at": pd.to_datetime(event["createdAt"], utc=True),
                    "user_id": str(user),
                })

    direct_click_events = []
    for click in rss:
        user = relation_id(click.get("user"))
        if user is not None and str(user) in excluded:
            continue
        file_key = click.get("file") or ""
        for mid in activity:
            if file_key == f"capytale2.ac-paris.fr/web/b/{mid}":
                activity[mid]["capytale_clicks"] += 1
                if user is not None:
                    activity[mid]["capytale_click_users"].add(str(user))
            if file_key == direct_keys[mid]:
                activity[mid]["basthon_direct_clicks"] += 1
                if user is not None:
                    activity[mid]["basthon_direct_users"].add(str(user))
                    direct_click_events.append({
                        "mathadata_id": mid,
                        "created_at": pd.to_datetime(click["createdAt"], utc=True),
                        "user_id": str(user),
                    })
                else:
                    activity[mid]["basthon_direct_anonymous"] += 1

    match_by_user = {}
    nom_path = LOCAL / "match_nominatif.csv"
    if nom_path.exists():
        candidates = pd.read_csv(
            ENQ / "site-vers-classe" / "data" / "match_candidates.csv",
            dtype=str,
            keep_default_na=False,
        )
        nominal = pd.read_csv(nom_path, dtype=str, keep_default_na=False)
        valid = nominal.merge(
            candidates[["site_code", "cap_acc", "conf"]].rename(columns={"cap_acc": "cap_acc_h8"}),
            on=["site_code", "conf"],
            how="inner",
        )
        valid = valid[valid.apply(lambda row: str(row["cap_acc"]).startswith(row["cap_acc_h8"]), axis=1)]
        valid = valid[valid["conf"].isin(["A", "B"])]
        match_by_user = {
            str(row.site_id): (row.cap_acc, row.conf) for row in valid.itertuples()
        }

    cap_sessions = pd.read_csv(
        ENQ / "usage-capytale" / "data" / "sessions.csv",
        dtype=str,
        keep_default_na=False,
    )
    cap_sessions["start"] = pd.to_datetime(cap_sessions["start"], utc=True)
    cap_sessions["end"] = pd.to_datetime(cap_sessions["end"], utc=True)
    inferred = []
    for session in sessions.itertuples():
        earlier = [
            copy for copy in copies
            if copy["mathadata_id"] == session.mathadata_id
            and copy["created_at"] <= session.start
            and copy["created_at"] >= session.start - pd.Timedelta(days=30)
        ]
        recent_users = {copy["user_id"] for copy in earlier if copy["created_at"] >= session.start - pd.Timedelta(days=7)}
        older_users = {copy["user_id"] for copy in earlier if copy["created_at"] < session.start - pd.Timedelta(days=7)}
        if len(recent_users) == 1:
            user_id = next(iter(recent_users))
            copy_confidence = "A"
        elif not recent_users and len(older_users) == 1:
            user_id = next(iter(older_users))
            copy_confidence = "B"
        else:
            continue
        matched = match_by_user.get(user_id)
        if not matched:
            continue
        teacher, match_confidence = matched
        simultaneous = cap_sessions[
            (cap_sessions["teacher"] == teacher)
            & (cap_sessions["mathadata_id"] == session.mathadata_id)
            & (cap_sessions["start"] < session.end)
            & (cap_sessions["end"] >= session.start)
        ]
        if 1 <= session.n_visiteurs_uniques_urlr <= 4 and len(simultaneous):
            mode = "depannage_infere"
        elif session.n_visiteurs_uniques_urlr >= K.CLASSE_MIN and not len(simultaneous):
            mode = "remplacement_infere"
        else:
            mode = "indetermine"
        inferred.append({
            "copy_confidence": copy_confidence,
            "match_confidence": match_confidence,
            "mode": mode,
        })

    by_activity = []
    for mid, item in activity.items():
        by_activity.append({
            "mathadata_id": mid,
            "mathadata_title": item["mathadata_title"],
            "public": item["public"],
            "module_views": item["module_views"],
            "module_view_users": len(item["module_view_users"]),
            "module_view_sessions": len(item["module_view_sessions"]),
            "capytale_clicks": item["capytale_clicks"],
            "capytale_click_users": len(item["capytale_click_users"]),
            "basthon_direct_clicks": item["basthon_direct_clicks"],
            "basthon_direct_users": len(item["basthon_direct_users"]),
            "basthon_direct_anonymous": item["basthon_direct_anonymous"],
            "basthon_short_modal_opens": item["modal_opens"],
            "basthon_short_copies": item["short_copies"],
        })
    inferred_df = pd.DataFrame(inferred)
    direct_candidates = []
    for session in sessions.itertuples():
        earlier = [
            click for click in direct_click_events
            if click["mathadata_id"] == session.mathadata_id
            and click["created_at"] <= session.start
            and click["created_at"] >= session.start - pd.Timedelta(days=30)
        ]
        recent = {
            click["user_id"] for click in earlier
            if click["created_at"] >= session.start - pd.Timedelta(days=7)
        }
        very_recent = {
            click["user_id"] for click in earlier
            if click["created_at"] >= session.start - pd.Timedelta(days=1)
        }
        older = {
            click["user_id"] for click in earlier
            if click["created_at"] < session.start - pd.Timedelta(days=7)
        }
        if len(recent) == 1:
            user_id = next(iter(recent))
            confidence = "A7"
        elif not recent and len(older) == 1:
            user_id = next(iter(older))
            confidence = "B30"
        else:
            user_id = None
            confidence = "non_attribue"
        direct_candidates.append({
            "confidence": confidence,
            "strong_24h": user_id is not None and len(very_recent) == 1,
            "matched_capytale_ab": user_id in match_by_user if user_id else False,
            "public": session.mathadata_id == "3518185",
            "mode": session.mode_historique,
            "n_uniques": int(session.n_visiteurs_uniques_urlr),
            "clicks": int(session.clicks),
            "user_id": user_id,
        })
    direct_df = pd.DataFrame(direct_candidates)
    # (b) Profil de taille/mode des salves QUI ONT un candidat « clic direct » connu.
    # Agrégat exploratoire, sans nominatif : caractérise l'entonnoir d'adoption Basthon.
    # Les CLICS détectent les classes masquées par un NAT établissement (peu d'uniques, bcp de clics) ;
    # les réouvertures multiples par un même élève sont négligées.
    cand_df = direct_df[direct_df["confidence"].isin(["A7", "B30"])]
    cand_sz = cand_df["n_uniques"]
    cand_cl = cand_df["clicks"]
    cand_size_bands = {
        "1": int((cand_sz == 1).sum()),
        "2_4": int(cand_sz.between(2, 4).sum()),
        "5_9": int(cand_sz.between(5, 9).sum()),
        "10_19": int(cand_sz.between(10, 19).sum()),
        "20_plus": int((cand_sz >= 20).sum()),
    }
    cand_click_bands = {
        "1": int((cand_cl == 1).sum()),
        "2_4": int(cand_cl.between(2, 4).sum()),
        "5_9": int(cand_cl.between(5, 9).sum()),
        "10_19": int(cand_cl.between(10, 19).sum()),
        "20_29": int(cand_cl.between(20, 29).sum()),
        "30_plus": int((cand_cl >= 30).sum()),
    }
    public_rows = [row for row in by_activity if row["public"]]
    locked_rows = [row for row in by_activity if not row["public"]]

    def channel_totals(rows):
        return {
            "module_views": sum(row["module_views"] for row in rows),
            "capytale_clicks": sum(row["capytale_clicks"] for row in rows),
            "basthon_direct_clicks": sum(row["basthon_direct_clicks"] for row in rows),
            "basthon_direct_anonymous": sum(row["basthon_direct_anonymous"] for row in rows),
        }

    facts = {
        "_meta": {
            "snapshot": SNAP.name,
            "tracking_start_existing": "2025-11-27",
            "short_link_tracking": (
                "prospectif; aucun backfill" if not copies else "premiers événements observés"
            ),
            "privacy": "sortie agrégée; aucun site_id, nom, email ou identifiant professeur",
        },
        "by_activity": sorted(by_activity, key=lambda row: row["mathadata_id"]),
        "totals": {
            "module_views": sum(row["module_views"] for row in by_activity),
            "capytale_clicks": sum(row["capytale_clicks"] for row in by_activity),
            "basthon_direct_clicks": sum(row["basthon_direct_clicks"] for row in by_activity),
            "basthon_short_modal_opens": sum(row["basthon_short_modal_opens"] for row in by_activity),
            "basthon_short_copies": sum(row["basthon_short_copies"] for row in by_activity),
        },
        "public_activity": channel_totals(public_rows),
        "locked_activities": channel_totals(locked_rows),
        "future_attribution": {
            "attributed_sessions": len(inferred),
            "copy_confidence": (
                counts(inferred_df["copy_confidence"], ("A", "B")) if len(inferred_df) else {"A": 0, "B": 0}
            ),
            "match_confidence": (
                counts(inferred_df["match_confidence"], ("A", "B")) if len(inferred_df) else {"A": 0, "B": 0}
            ),
            "modes": (
                counts(inferred_df["mode"], ("depannage_infere", "remplacement_infere", "indetermine"))
                if len(inferred_df) else
                {"depannage_infere": 0, "remplacement_infere": 0, "indetermine": 0}
            ),
        },
        "historical_direct_click_candidates": {
            "_note": (
                "Exploratoire uniquement : un accès Basthon direct prouve un test/une consultation "
                "du professeur, pas la copie du lien court aux élèves."
            ),
            "connected_direct_click_users": len({
                event["user_id"] for event in direct_click_events
            }),
            "candidate_sessions": int(
                direct_df["confidence"].isin(["A7", "B30"]).sum()
            ),
            "candidate_sessions_a7": int((direct_df["confidence"] == "A7").sum()),
            "candidate_sessions_b30": int((direct_df["confidence"] == "B30").sum()),
            "strong_candidate_sessions_24h": int(direct_df["strong_24h"].sum()),
            "candidate_sessions_with_capytale_match_ab": int(
                (
                    direct_df["confidence"].isin(["A7", "B30"])
                    & direct_df["matched_capytale_ab"]
                ).sum()
            ),
            "strong_sessions_with_capytale_match_ab": int(
                (direct_df["strong_24h"] & direct_df["matched_capytale_ab"]).sum()
            ),
            "distinct_candidate_users": int(
                direct_df.loc[
                    direct_df["confidence"].isin(["A7", "B30"]), "user_id"
                ].nunique()
            ),
            "distinct_candidate_users_with_capytale_match_ab": int(
                direct_df.loc[
                    direct_df["confidence"].isin(["A7", "B30"])
                    & direct_df["matched_capytale_ab"],
                    "user_id",
                ].nunique()
            ),
            "candidate_burst_size_bands": cand_size_bands,
            "candidate_burst_click_bands": cand_click_bands,
            "candidate_burst_modes": counts(
                cand_df["mode"], ("compatible_remplacement", "compatible_depannage", "indetermine")
            ),
            "candidate_sessions_ge5_uniques": int((cand_df["n_uniques"] >= K.CLASSE_MIN).sum()),
            "candidate_sessions_ge5_clics": int((cand_df["clicks"] >= K.CLASSE_MIN).sum()),
            "candidate_sessions_ge10_clics": int((cand_df["clicks"] >= K.SEANCE_RICHE_MIN).sum()),
            "candidate_sessions_nat_suspect": int(
                ((cand_df["n_uniques"] <= 4) & (cand_df["clicks"] >= K.SEANCE_RICHE_MIN)).sum()
            ),
            "locked_activities": {
                "candidate_sessions": int(
                    (
                        ~direct_df["public"]
                        & direct_df["confidence"].isin(["A7", "B30"])
                    ).sum()
                ),
                "strong_candidate_sessions_24h": int(
                    (~direct_df["public"] & direct_df["strong_24h"]).sum()
                ),
                "candidate_sessions_with_capytale_match_ab": int(
                    (
                        ~direct_df["public"]
                        & direct_df["confidence"].isin(["A7", "B30"])
                        & direct_df["matched_capytale_ab"]
                    ).sum()
                ),
                "strong_sessions_with_capytale_match_ab": int(
                    (
                        ~direct_df["public"]
                        & direct_df["strong_24h"]
                        & direct_df["matched_capytale_ab"]
                    ).sum()
                ),
            },
        },
    }
    K.dump_json(facts, OUT / "facts_urlr_site.json")
    print(f"→ {OUT / 'facts_urlr_site.json'}")


if __name__ == "__main__":
    main()
