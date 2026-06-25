#!/usr/bin/env python3
"""Récupère les liens et statistiques URLR sans conserver les champs personnels.

Sorties versionnables :
  - public/data/urlr_links_AAAAMMJJ.csv : 1 ligne par lien + totaux sur la fenêtre observée
  - public/data/urlr_daily_AAAAMMJJ.csv : 1 ligne par lien × jour de Paris avec activité non nulle
  - public/data/urlr_hourly_AAAAMMJJ.csv : 1 ligne par lien × heure de Paris avec activité non nulle
  - public/data/urlr_bursts_AAAAMMJJ.csv : salves horaires + uniques recalculés sur chaque fenêtre

La clé URLR_API_KEY est lue depuis l'environnement ou `.env.local`, sans jamais être affichée.
Le champ API `user` (e-mail du créateur), `workspace_id` et `folder_id` sont volontairement exclus.
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env.local"
OUTDIR = ROOT / "public" / "data"
MAPPING = Path(__file__).resolve().parent / "urlr_activity_mapping.csv"
API_BASE = os.environ.get("URLR_API_URL", "https://urlr.me/api/v2").rstrip("/")
PARIS = ZoneInfo("Europe/Paris")

LINK_COLUMNS = [
    "link_id", "short_url", "code", "label", "mathadata_id", "mathadata_title",
    "resource_slug", "destination_url", "notebook_source_url", "created_at", "updated_at",
    "window_start", "window_end", "visits", "unique_visits", "clicks", "scans", "extracted_at",
]
DAILY_COLUMNS = [
    "link_id", "code", "label", "mathadata_id", "mathadata_title", "resource_slug",
    "date_paris", "window_start", "window_end", "visits", "unique_visits", "clicks",
    "scans", "extracted_at",
]
HOURLY_COLUMNS = [
    "link_id", "code", "label", "mathadata_id", "mathadata_title", "resource_slug",
    "date_paris", "hour_paris", "hour_start", "hour_end", "visits", "unique_visits",
    "clicks", "scans", "extracted_at",
]
BURST_COLUMNS = [
    "burst_id", "link_id", "code", "label", "mathadata_id", "mathadata_title",
    "resource_slug", "start", "end", "active_hours", "visits", "unique_visits",
    "clicks", "scans", "extracted_at",
]
STAT_KEYS = ("visits", "unique_visits", "clicks", "scans")
ADDITIVE_KEYS = ("visits", "clicks", "scans")


def load_api_key():
    key = os.environ.get("URLR_API_KEY", "").strip()
    if key:
        return key
    if ENV.exists():
        for raw in ENV.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("URLR_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                if key:
                    return key
    sys.exit(f"✗ URLR_API_KEY absent. Ajoute-le dans {ENV} (fichier gitignore).")


def iso(dt):
    return dt.isoformat(timespec="seconds")


def api_get(path, key, params=None, attempts=6):
    url = f"{API_BASE}/{path.lstrip('/')}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={
        "X-API-KEY": key,
        "Accept": "application/json",
        "User-Agent": "mathadata-enquete-usages/urlr-fetch",
    })
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or 500 <= exc.code < 600
            if not retryable or attempt == attempts - 1:
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                sys.exit(f"✗ URLR HTTP {exc.code} sur {path}: {detail}")
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt
            time.sleep(min(delay, 30))
        except urllib.error.URLError as exc:
            if attempt == attempts - 1:
                sys.exit(f"✗ Échec réseau URLR sur {path}: {exc.reason}")
            time.sleep(min(2 ** attempt, 30))
    raise AssertionError("boucle de retry URLR épuisée")


def fetch_links(key):
    links = []
    page = 1
    expected_total = None
    while True:
        payload = api_get("links", key, {"limit": 50, "page": page})
        required = {"links", "total", "pages", "page"}
        if not required.issubset(payload):
            sys.exit(f"✗ Réponse URLR /links invalide, champs manquants: {sorted(required - set(payload))}")
        expected_total = int(payload["total"])
        links.extend(payload["links"])
        if page >= int(payload["pages"]):
            break
        page += 1
    ids = [link.get("id") for link in links]
    if len(links) != expected_total or len(ids) != len(set(ids)):
        sys.exit(
            f"✗ Pagination URLR incohérente: total annoncé={expected_total}, "
            f"reçus={len(links)}, ids uniques={len(set(ids))}"
        )
    required_link = {"id", "url", "domain", "code", "label", "created_at", "updated_at"}
    for link in links:
        missing = required_link - set(link)
        if missing:
            sys.exit(f"✗ Lien URLR {link.get('id', '?')} incomplet: {sorted(missing)}")
    return links


def load_mapping(links):
    if not MAPPING.exists():
        sys.exit(f"✗ Mapping URLR→MathAData absent: {MAPPING}")
    with MAPPING.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"code", "urlr_label", "mathadata_id", "mathadata_title", "mapping_basis"}
    if not rows or not required.issubset(rows[0]):
        sys.exit(f"✗ Schéma de mapping URLR invalide: colonnes requises {sorted(required)}")
    by_code = {row["code"]: row for row in rows}
    if len(by_code) != len(rows):
        sys.exit("✗ Codes dupliqués dans le mapping URLR→MathAData.")
    link_codes = {link["code"] for link in links}
    missing = link_codes - set(by_code)
    stale = set(by_code) - link_codes
    if missing:
        sys.exit(
            "✗ Nouveaux liens URLR sans activité canonique. Complète "
            f"{MAPPING.relative_to(ROOT)} pour: {sorted(missing)}"
        )
    if stale:
        print(f"⚠ Codes présents dans le mapping mais absents de l'API: {sorted(stale)}")
    for link in links:
        row = by_code[link["code"]]
        if row["urlr_label"] != (link["label"] or ""):
            sys.exit(
                f"✗ Libellé URLR modifié pour {link['code']}: "
                f"mapping={row['urlr_label']!r}, API={link['label']!r}"
            )
    return by_code


def fetch_stats(key, link_id, start, end):
    payload = api_get("statistics", key, {
        "link_id": link_id,
        "from": iso(start),
        "to": iso(end),
    })
    required = {"link_id", *STAT_KEYS}
    if not required.issubset(payload):
        sys.exit(
            f"✗ Statistiques URLR incomplètes pour {link_id}: "
            f"{sorted(required - set(payload))}"
        )
    if payload["link_id"] != link_id:
        sys.exit(f"✗ URLR a renvoyé les statistiques d'un autre lien pour {link_id}")
    values = {}
    for name in STAT_KEYS:
        value = payload[name]
        if not isinstance(value, int) or value < 0:
            sys.exit(f"✗ Statistique URLR invalide {name}={value!r} pour {link_id}")
        values[name] = value
    return values


def start_of_day(dt):
    local = dt.astimezone(PARIS)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def resource_metadata(link):
    label = link["label"] or ""
    resource_slug = label.split(":", 1)[1] if ":" in label else label
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(link["url"]).query)
    notebook_source = (query.get("from") or [""])[0]
    return resource_slug, notebook_source


def build_rows(key, links, mapping, cutoff):
    link_rows = []
    daily_rows = []
    hourly_rows = []
    for index, link in enumerate(sorted(links, key=lambda item: (item["created_at"], item["id"])), 1):
        activity = mapping[link["code"]]
        created = datetime.fromisoformat(link["created_at"]).astimezone(PARIS)
        window_start = start_of_day(created)
        if window_start >= cutoff:
            sys.exit(f"✗ Date de création future/invalide pour {link['id']}: {link['created_at']}")
        print(f"→ [{index}/{len(links)}] {link['label'] or link['code']}")
        total = fetch_stats(key, link["id"], window_start, cutoff)
        additive_sum = {name: 0 for name in ADDITIVE_KEYS}
        day_start = window_start
        while day_start < cutoff:
            next_midnight = start_of_day(day_start + timedelta(days=1))
            day_end = min(next_midnight, cutoff)
            stats = fetch_stats(key, link["id"], day_start, day_end)
            for name in ADDITIVE_KEYS:
                additive_sum[name] += stats[name]
            if any(stats[name] for name in ADDITIVE_KEYS):
                resource_slug, _ = resource_metadata(link)
                common = {
                    "link_id": link["id"],
                    "code": link["code"],
                    "label": link["label"],
                    "mathadata_id": activity["mathadata_id"],
                    "mathadata_title": activity["mathadata_title"],
                    "resource_slug": resource_slug,
                }
                daily_rows.append({
                    **common,
                    "date_paris": day_start.date().isoformat(),
                    "window_start": iso(day_start),
                    "window_end": iso(day_end),
                    **stats,
                    "extracted_at": iso(cutoff),
                })
                hourly_sum = {name: 0 for name in ADDITIVE_KEYS}
                hour_start_utc = day_start.astimezone(timezone.utc)
                day_end_utc = day_end.astimezone(timezone.utc)
                while hour_start_utc < day_end_utc:
                    hour_end_utc = min(hour_start_utc + timedelta(hours=1), day_end_utc)
                    hour_start = hour_start_utc.astimezone(PARIS)
                    hour_end = hour_end_utc.astimezone(PARIS)
                    hour_stats = fetch_stats(key, link["id"], hour_start, hour_end)
                    for name in ADDITIVE_KEYS:
                        hourly_sum[name] += hour_stats[name]
                    if any(hour_stats[name] for name in ADDITIVE_KEYS):
                        hourly_rows.append({
                            **common,
                            "date_paris": hour_start.date().isoformat(),
                            "hour_paris": hour_start.strftime("%H:00"),
                            "hour_start": iso(hour_start),
                            "hour_end": iso(hour_end),
                            **hour_stats,
                            "extracted_at": iso(cutoff),
                        })
                    hour_start_utc = hour_end_utc
                if hourly_sum != {name: stats[name] for name in ADDITIVE_KEYS}:
                    sys.exit(
                        f"✗ Contrôle horaire URLR échoué pour {link['id']} le "
                        f"{day_start.date()}: somme horaire={hourly_sum}, jour={stats}"
                    )
            day_start = day_end
        if additive_sum != {name: total[name] for name in ADDITIVE_KEYS}:
            sys.exit(
                f"✗ Contrôle URLR échoué pour {link['id']}: "
                f"somme quotidienne={additive_sum}, total={total}"
            )
        resource_slug, notebook_source = resource_metadata(link)
        link_rows.append({
            "link_id": link["id"],
            "short_url": f"https://{link['domain']}/{link['code']}",
            "code": link["code"],
            "label": link["label"],
            "mathadata_id": activity["mathadata_id"],
            "mathadata_title": activity["mathadata_title"],
            "resource_slug": resource_slug,
            "destination_url": link["url"],
            "notebook_source_url": notebook_source,
            "created_at": link["created_at"],
            "updated_at": link["updated_at"],
            "window_start": iso(window_start),
            "window_end": iso(cutoff),
            **total,
            "extracted_at": iso(cutoff),
        })
    return link_rows, daily_rows, hourly_rows


def build_bursts(key, hourly_rows):
    """Fusionne les heures actives de même lien si leurs débuts sont espacés de <3 h.

    Les métriques de la salve sont redemandées à URLR sur la fenêtre complète : en particulier,
    `unique_visits` n'est jamais obtenu en sommant les uniques horaires.
    """
    by_link = {}
    for row in hourly_rows:
        by_link.setdefault(row["link_id"], []).append(row)
    bursts = []
    burst_number = 0
    for link_id, rows in sorted(by_link.items()):
        rows = sorted(rows, key=lambda row: datetime.fromisoformat(row["hour_start"]))
        groups = []
        current = []
        previous_start = None
        for row in rows:
            start = datetime.fromisoformat(row["hour_start"])
            if previous_start is not None and start - previous_start >= timedelta(hours=3):
                groups.append(current)
                current = []
            current.append(row)
            previous_start = start
        if current:
            groups.append(current)
        for group in groups:
            burst_number += 1
            start = datetime.fromisoformat(group[0]["hour_start"])
            end = datetime.fromisoformat(group[-1]["hour_end"])
            stats = fetch_stats(key, link_id, start, end)
            additive = {name: sum(int(row[name]) for row in group) for name in ADDITIVE_KEYS}
            if additive != {name: stats[name] for name in ADDITIVE_KEYS}:
                sys.exit(
                    f"✗ Contrôle salve URLR échoué pour {link_id} {iso(start)}–{iso(end)}: "
                    f"heures={additive}, fenêtre={stats}"
                )
            first = group[0]
            bursts.append({
                "burst_id": f"U{burst_number:04d}",
                "link_id": link_id,
                "code": first["code"],
                "label": first["label"],
                "mathadata_id": first["mathadata_id"],
                "mathadata_title": first["mathadata_title"],
                "resource_slug": first["resource_slug"],
                "start": iso(start),
                "end": iso(end),
                "active_hours": len(group),
                **stats,
                "extracted_at": first["extracted_at"],
            })
    return bursts


def write_csv_atomic(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        "w", newline="", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as tmp:
        writer = csv.DictWriter(tmp, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def parse_args():
    parser = argparse.ArgumentParser(description="Récupère les statistiques anonymes URLR.")
    parser.add_argument(
        "--output-dir", type=Path, default=OUTDIR,
        help="Dossier de sortie (défaut: public/data).",
    )
    parser.add_argument(
        "--replace", action="store_true",
        help="Remplace atomiquement les trois fichiers datés du jour s'ils existent.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cutoff = datetime.now(PARIS).replace(microsecond=0)
    stamp = cutoff.strftime("%Y%m%d")
    links_path = args.output_dir / f"urlr_links_{stamp}.csv"
    daily_path = args.output_dir / f"urlr_daily_{stamp}.csv"
    hourly_path = args.output_dir / f"urlr_hourly_{stamp}.csv"
    bursts_path = args.output_dir / f"urlr_bursts_{stamp}.csv"
    existing = [str(path) for path in (links_path, daily_path, hourly_path, bursts_path) if path.exists()]
    if existing and not args.replace:
        sys.exit("✗ Extraction URLR du jour déjà présente, aucun écrasement:\n  " + "\n  ".join(existing))

    key = load_api_key()
    print(f"→ Appel API URLR v2, coupure figée à {iso(cutoff)}")
    links = fetch_links(key)
    if not links:
        sys.exit("✗ Aucun lien URLR retourné par l'API.")
    mapping = load_mapping(links)
    link_rows, daily_rows, hourly_rows = build_rows(key, links, mapping, cutoff)
    burst_rows = build_bursts(key, hourly_rows)
    write_csv_atomic(links_path, LINK_COLUMNS, link_rows)
    write_csv_atomic(daily_path, DAILY_COLUMNS, daily_rows)
    write_csv_atomic(hourly_path, HOURLY_COLUMNS, hourly_rows)
    write_csv_atomic(bursts_path, BURST_COLUMNS, burst_rows)
    print(f"✓ {len(link_rows)} liens → {links_path.relative_to(ROOT)}")
    print(f"✓ {len(daily_rows)} jours-lien non nuls → {daily_path.relative_to(ROOT)}")
    print(f"✓ {len(hourly_rows)} heures-lien non nulles → {hourly_path.relative_to(ROOT)}")
    print(f"✓ {len(burst_rows)} salves URLR → {bursts_path.relative_to(ROOT)}")
    print("  Champs personnels URLR exclus: user, workspace_id, folder_id.")
    print("  unique_visits est un total de fenêtre non additionnable entre jours.")


if __name__ == "__main__":
    main()
