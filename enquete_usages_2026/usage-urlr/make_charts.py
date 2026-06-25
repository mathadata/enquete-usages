#!/usr/bin/env python3
"""Génère les premiers graphiques URLR depuis les extractions publiques."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = Path(__file__).resolve().parent / "charts"
DATA = Path(__file__).resolve().parent / "data"

PAPER = "#F8FAFC"
INK = "#172033"
MUTED = "#64748B"
GRID = "#DCE3EC"
BLUE = "#2563EB"
TEAL = "#0F9D8A"
AMBER = "#F59E0B"
ROSE = "#E24963"
VIOLET = "#7C5CE0"
SKY = "#38A6D8"

ACTIVITY_LABELS = {
    "stats-moyenne-histogramme-mnist": "Statistiques — moyenne & histogramme (MNIST)",
    "geometry2ndeequationdroite-mnist": "Géométrie 2de — équation de droite",
    "stats-moyenne-histogramme-fetal": "Statistiques — moyenne & histogramme (fœtus)",
    "geometry2ndemilieudistance-mnist": "Géométrie 2de — milieu & distance",
    "geometry1eredroiteproduitscalaire-mnist": "Géométrie 1re — produit scalaire",
    "geometry2ndedroitevecteurdirecteur-mnist": "Géométrie 2de — vecteur directeur",
}

MONTHS_FR = {
    1: "janv.",
    2: "févr.",
    3: "mars",
    4: "avr.",
    5: "mai",
    6: "juin",
    7: "juil.",
    8: "août",
    9: "sept.",
    10: "oct.",
    11: "nov.",
    12: "déc.",
}


def latest(pattern: str) -> Path:
    matches = sorted((ROOT / "public/data").glob(pattern))
    if not matches:
        raise FileNotFoundError(f"Aucun fichier public/data/{pattern}")
    return matches[-1]


def fmt_int(value: int | float) -> str:
    return f"{int(value):,}".replace(",", " ")


def activity_label(slug: str) -> str:
    return ACTIVITY_LABELS.get(slug, slug.replace("-", " "))


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.titlesize": 16,
            "axes.titleweight": "bold",
            "axes.titlecolor": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "axes.linewidth": 0.8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.facecolor": PAPER,
            "figure.facecolor": PAPER,
            "savefig.facecolor": PAPER,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "grid.color": GRID,
            "grid.linewidth": 0.7,
            "grid.alpha": 0.8,
        }
    )


def subtitle(ax: plt.Axes, text: str) -> None:
    ax.text(
        0,
        1.015,
        text,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        color=MUTED,
        fontsize=10,
    )


def source_note(fig: plt.Figure, extracted_at: pd.Timestamp, extra: str = "") -> None:
    note = (
        "Source : URLR, extraction publique du "
        f"{extracted_at.tz_convert('Europe/Paris'):%d/%m/%Y à %H:%M}. "
        "Un clic n’est ni une personne ni une séance."
    )
    if extra:
        note += f" {extra}"
    fig.text(0.01, 0.01, note, ha="left", va="bottom", color=MUTED, fontsize=8)


def save(fig: plt.Figure, out_dir: Path, name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, dpi=180, bbox_inches="tight", pad_inches=0.22)
    plt.close(fig)
    print(f"wrote {path.relative_to(ROOT)}")


def validate(daily: pd.DataFrame, links: pd.DataFrame) -> None:
    required_daily = {
        "link_id",
        "resource_slug",
        "date_paris",
        "visits",
        "unique_visits",
        "clicks",
        "scans",
        "extracted_at",
    }
    required_links = {
        "link_id",
        "resource_slug",
        "visits",
        "unique_visits",
        "clicks",
        "scans",
        "extracted_at",
    }
    if missing := required_daily - set(daily.columns):
        raise ValueError(f"Colonnes absentes du fichier quotidien : {sorted(missing)}")
    if missing := required_links - set(links.columns):
        raise ValueError(f"Colonnes absentes du fichier liens : {sorted(missing)}")
    if not daily["link_id"].isin(links["link_id"]).all():
        raise ValueError("Le fichier quotidien contient un lien absent du fichier de totaux.")
    if not (daily["visits"] == daily["clicks"]).all():
        raise ValueError("Cette extraction ne vérifie plus visits == clicks : revoir les graphes.")

    additive = daily.groupby("link_id")[["visits", "clicks", "scans"]].sum()
    expected = links.set_index("link_id")[["visits", "clicks", "scans"]]
    expected = expected.loc[additive.index]
    if not additive.equals(expected):
        raise ValueError("Les sommes quotidiennes ne correspondent pas aux totaux par lien.")


def chart_daily(daily: pd.DataFrame, extracted_at: pd.Timestamp, out_dir: Path) -> None:
    start = daily["date_paris"].min()
    end = daily["date_paris"].max()
    dates = pd.date_range(start, end, freq="D")
    totals = daily.groupby("date_paris")["clicks"].sum().reindex(dates, fill_value=0)
    rolling = totals.rolling(7, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(13, 5.4))
    ax.bar(totals.index, totals.values, width=0.88, color=BLUE, alpha=0.34, label="Clics par jour")
    ax.plot(
        rolling.index,
        rolling.values,
        color=ROSE,
        linewidth=2.6,
        label="Moyenne mobile sur 7 jours",
        zorder=3,
    )
    ax.fill_between(rolling.index, rolling.values, color=ROSE, alpha=0.08)

    for date, value in totals.nlargest(4).items():
        ax.scatter(date, value, s=28, color=BLUE, zorder=4)
        ax.annotate(
            f"{date:%d/%m} · {fmt_int(value)}",
            xy=(date, value),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=INK,
            fontsize=9,
            fontweight="bold",
        )

    ax.set_title("Les ouvertures URLR avancent par vagues", loc="left", pad=32)
    subtitle(
        ax,
        f"{fmt_int(totals.sum())} clics du {start:%d/%m/%Y} au {end:%d/%m/%Y} · "
        "les quatre journées les plus actives sont annotées",
    )
    ax.set_ylabel("Clics URLR")
    ax.set_xlim(start - pd.Timedelta(days=3), end + pd.Timedelta(days=3))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda value, _:
            f"{MONTHS_FR[mdates.num2date(value).month]}\n{mdates.num2date(value).year}"
        )
    )
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    source_note(fig, extracted_at, "Les jours absents du CSV sont traités comme des zéros.")
    fig.subplots_adjust(bottom=0.16, top=0.84)
    save(fig, out_dir, "01_clics_quotidiens.png")


def chart_calendar(daily: pd.DataFrame, extracted_at: pd.Timestamp, out_dir: Path) -> None:
    start = daily["date_paris"].min()
    end = daily["date_paris"].max()
    calendar_start = start - pd.Timedelta(days=start.weekday())
    calendar_end = end + pd.Timedelta(days=6 - end.weekday())
    dates = pd.date_range(calendar_start, calendar_end, freq="D")
    totals = daily.groupby("date_paris")["clicks"].sum().reindex(dates, fill_value=0)
    n_weeks = len(dates) // 7
    grid = totals.to_numpy().reshape(n_weeks, 7).T

    cmap = LinearSegmentedColormap.from_list(
        "urlr",
        ["#EEF2F7", "#C7DDF8", "#67A9E8", BLUE, "#173B88"],
    )
    fig, ax = plt.subplots(figsize=(13, 3.9))
    image = ax.imshow(grid, aspect="auto", interpolation="nearest", cmap=cmap, vmin=0)

    ax.set_yticks(range(7))
    ax.set_yticklabels(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"])
    month_ticks: list[int] = []
    month_labels: list[str] = []
    for period in pd.period_range(start=start, end=end, freq="M"):
        first = max(period.start_time, start)
        last = min(period.end_time.normalize(), end)
        midpoint = first + (last - first) / 2
        week = int((midpoint - calendar_start).days // 7)
        month_ticks.append(week)
        month_labels.append(f"{MONTHS_FR[period.month]}\n{period.year}")
    ax.set_xticks(month_ticks)
    ax.set_xticklabels(month_labels)
    ax.tick_params(axis="both", length=0)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    top = totals.nlargest(5)
    for date, value in top.items():
        week = int((date - calendar_start).days // 7)
        weekday = date.weekday()
        ax.text(
            week,
            weekday,
            fmt_int(value),
            ha="center",
            va="center",
            color="white" if value >= top.iloc[-1] else INK,
            fontsize=8,
            fontweight="bold",
        )

    colorbar = fig.colorbar(image, ax=ax, fraction=0.022, pad=0.02)
    colorbar.set_label("Clics dans la journée", color=INK)
    colorbar.outline.set_visible(False)
    ax.set_title("Le calendrier révèle des pics très ponctuels", loc="left", pad=32)
    subtitle(ax, "Chaque case représente un jour civil en Europe/Paris · les cinq plus gros pics sont chiffrés")
    source_note(fig, extracted_at, "Les cases claires correspondent à zéro clic.")
    fig.subplots_adjust(bottom=0.2, top=0.78)
    save(fig, out_dir, "02_calendrier_des_clics.png")


def chart_monthly(daily: pd.DataFrame, extracted_at: pd.Timestamp, out_dir: Path) -> None:
    frame = daily.copy()
    frame["month"] = frame["date_paris"].dt.to_period("M")
    monthly = frame.pivot_table(
        index="month",
        columns="resource_slug",
        values="clicks",
        aggfunc="sum",
        fill_value=0,
    )
    order = (
        monthly.sum(axis=0)
        .sort_values(ascending=False)
        .index.tolist()
    )
    colors = [BLUE, TEAL, AMBER, ROSE, VIOLET, SKY]

    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(monthly))
    x = np.arange(len(monthly))
    for slug, color in zip(order, colors):
        values = monthly[slug].to_numpy()
        ax.bar(
            x,
            values,
            bottom=bottom,
            width=0.68,
            color=color,
            label=activity_label(slug),
        )
        bottom += values

    for i, total in enumerate(bottom):
        ax.text(
            i,
            total + max(bottom) * 0.018,
            fmt_int(total),
            ha="center",
            va="bottom",
            color=INK,
            fontsize=10,
            fontweight="bold",
        )

    labels = [
        f"{MONTHS_FR[p.month]}\n{p.year}" + ("*" if p.month in {12, 6} else "")
        for p in monthly.index
    ]
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Clics URLR")
    ax.set_title(
        "Trois activités portent l’essentiel des ouvertures",
        loc="left",
        pad=32,
    )
    subtitle(ax, "Clics mensuels empilés par lien court · total mensuel au-dessus de chaque barre")
    ax.set_ylim(0, max(bottom) * 1.17)
    ax.grid(axis="x", visible=False)
    ax.legend(
        handles=[
            Patch(facecolor=color, label=activity_label(slug))
            for slug, color in zip(order, colors)
        ],
        frameon=False,
        fontsize=9,
        ncol=2,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
    )
    source_note(
        fig,
        extracted_at,
        "* Décembre commence le 25/12 ; juin s’arrête au dernier jour non nul du fichier.",
    )
    fig.subplots_adjust(bottom=0.34, top=0.82)
    save(fig, out_dir, "03_clics_mensuels_par_activite.png")


def chart_activity(links: pd.DataFrame, extracted_at: pd.Timestamp, out_dir: Path) -> None:
    ranked = links.sort_values("clicks", ascending=True).copy()
    ranked["display"] = ranked["resource_slug"].map(activity_label)
    y = np.arange(len(ranked))

    fig, ax = plt.subplots(figsize=(12, 6.4))
    ax.barh(y, ranked["clicks"], color="#DCE8F8", height=0.64, label="Clics")
    ax.barh(
        y,
        ranked["unique_visits"],
        color=BLUE,
        height=0.64,
        label="Visites uniques du lien",
    )

    for i, row in enumerate(ranked.itertuples()):
        compact = row.unique_visits < 50
        ax.text(
            row.clicks + 8,
            i - 0.14 if compact else i,
            f"{fmt_int(row.clicks)} clics",
            va="center",
            color=INK,
            fontsize=10,
            fontweight="bold",
        )
        if not compact:
            unique_x = row.unique_visits - 5
            unique_ha = "right"
            unique_color = "white"
            unique_y = i
            unique_text = fmt_int(row.unique_visits)
        else:
            unique_x = row.unique_visits + 3
            unique_ha = "left"
            unique_color = BLUE
            unique_y = i + 0.17
            unique_text = f"{fmt_int(row.unique_visits)} uniques"
        ax.text(
            unique_x,
            unique_y,
            unique_text,
            va="center",
            ha=unique_ha,
            color=unique_color,
            fontsize=9,
            fontweight="bold",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(ranked["display"], fontsize=10)
    ax.set_xlabel("Volume sur toute la fenêtre")
    ax.set_title(
        "Volume et portée ne racontent pas exactement la même chose",
        loc="left",
        pad=32,
    )
    subtitle(
        ax,
        "Barre claire : clics · barre bleue : uniques URLR de fenêtre (méthode de déduplication non documentée)",
    )
    ax.set_xlim(0, ranked["clicks"].max() * 1.23)
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, ncol=2, loc="lower right")
    source_note(
        fig,
        extracted_at,
        "Les uniques ne sont pas dédupliqués entre liens et peuvent sous-compter un réseau partagé/NAT.",
    )
    fig.subplots_adjust(left=0.34, bottom=0.15, top=0.82)
    save(fig, out_dir, "04_volume_et_portee_par_activite.png")


def chart_size_comparison(cross: dict, out_dir: Path) -> None:
    rows = pd.DataFrame(cross["comparison_by_activity"])
    rows["label"] = rows["mathadata_id"].map(
        {
            "3518185": "Stats chiffres",
            "3515488": "Équation réduite",
            "6944347": "Stats fœtus",
            "6659633": "Milieu-distance",
            "5862412": "Produit scalaire",
            "8790616": "Vecteur directeur",
        }
    )
    rows = rows.sort_values("capytale_usage_classe")
    y = np.arange(len(rows))

    fig, ax = plt.subplots(figsize=(11.5, 6))
    ax.barh(y - 0.24, rows["capytale_usage_classe"], height=0.22, color=TEAL, label="Capytale ≥ 5 élèves")
    ax.barh(y, rows["urlr_usage_classe_estime"], height=0.22, color=BLUE, label="URLR ≥ 5 uniques")
    ax.barh(y + 0.24, rows["urlr_salves_5_clics_ou_plus"], height=0.22, color=ROSE, label="URLR ≥ 5 clics")
    ax.set_yticks(y)
    ax.set_yticklabels(rows["label"])
    ax.set_xlabel("Séances sur la période commune")
    ax.set_title("Le signal collectif URLR dépend fortement de la métrique", loc="left", pad=32)
    subtitle(ax, "Uniques = borne basse technique ; clics = proxy exploratoire si les réouvertures sont rares")
    ax.grid(axis="y", visible=False)
    ax.legend(frameon=False, loc="lower right")
    fig.text(
        0.01, 0.01,
        f"Sources : URLR × Capytale, période commune du {cross['_meta']['common_start'][:10]} "
        f"au {cross['_meta']['common_last_date']}. Les populations ne sont pas additionnées.",
        color=MUTED, fontsize=8,
    )
    fig.subplots_adjust(left=0.22, bottom=0.14, top=0.82)
    save(fig, out_dir, "05_seances_urlr_vs_capytale.png")


def chart_modes(facts: dict, out_dir: Path) -> None:
    modes = ["compatible_remplacement", "compatible_depannage", "indetermine"]
    labels = ["Remplacement\ncompatible", "Dépannage\ncompatible", "Indéterminé"]
    strict = [facts["modes_historiques"][mode] for mode in modes]
    sensitivity = [facts["modes_sensibilite_pm1h"][mode] for mode in modes]
    clicks = [facts["modes_exploratoires_clics"][mode] for mode in modes]
    x = np.arange(len(modes))

    fig, ax = plt.subplots(figsize=(9.5, 5.7))
    ax.bar(x - 0.24, strict, width=0.23, color=BLUE, label="Uniques — strict")
    ax.bar(x, sensitivity, width=0.23, color=AMBER, label="Uniques — ± 1 h")
    ax.bar(x + 0.24, clicks, width=0.23, color=ROSE, label="Clics — strict")
    for xpos, values in ((x - 0.24, strict), (x, sensitivity), (x + 0.24, clicks)):
        for xx, value in zip(xpos, values):
            ax.text(xx, value + 2, fmt_int(value), ha="center", color=INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Séances URLR estimées")
    ax.set_title("La majorité des séances reste non attribuable", loc="left", pad=32)
    subtitle(ax, "Indices temporels nationaux : les catégories ne prouvent pas le mode d'une classe")
    ax.set_ylim(0, max(strict + sensitivity + clicks) * 1.14)
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="upper left")
    fig.text(
        0.01, 0.01,
        "Source : facts_urlr.json. Classification sur les seules séances où Capytale est observable.",
        color=MUTED, fontsize=8,
    )
    fig.subplots_adjust(bottom=0.17, top=0.8)
    save(fig, out_dir, "06_modes_remplacement_depannage.png")


def chart_funnel(site: dict, facts: dict, out_dir: Path) -> None:
    totals = site["totals"]
    labels = ["Pages activité", "Clics Capytale", "Accès Basthon\ndirect", "Copies lien court", "Séances URLR\nestimées"]
    values = [
        totals["module_views"],
        totals["capytale_clicks"],
        totals["basthon_direct_clicks"],
        totals["basthon_short_copies"],
        facts["sessions_estimees"],
    ]
    colors = [SKY, TEAL, VIOLET, AMBER, BLUE]
    x = np.arange(len(values))

    fig, ax = plt.subplots(figsize=(11, 5.8))
    bars = ax.bar(x, values, color=colors, width=0.67)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + max(values) * 0.018, fmt_int(value),
                ha="center", color=INK, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Événements / séances")
    ax.set_yscale("symlog", linthresh=1)
    ax.set_title("Le suivi du lien court commence au déploiement", loc="left", pad=32)
    subtitle(ax, "Volumes de grains différents : ce schéma décrit les points observables, pas un funnel individuel")
    ax.grid(axis="x", visible=False)
    fig.text(
        0.01, 0.01,
        f"Sources : snapshot Payload {site['_meta']['snapshot']} et URLR. "
        "Les copies historiques restent à zéro : aucun backfill n'est inventé.",
        color=MUTED, fontsize=8,
    )
    fig.subplots_adjust(bottom=0.18, top=0.8)
    save(fig, out_dir, "07_funnel_site_urlr.png")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--daily",
        type=Path,
        default=None,
        help="CSV quotidien URLR (par défaut : extraction la plus récente).",
    )
    parser.add_argument(
        "--links",
        type=Path,
        default=None,
        help="CSV des liens URLR (par défaut : extraction la plus récente).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUT,
        help="Dossier de sortie des PNG.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    daily_path = args.daily or latest("urlr_daily_*.csv")
    links_path = args.links or latest("urlr_links_*.csv")

    daily = pd.read_csv(daily_path)
    links = pd.read_csv(links_path)
    daily["date_paris"] = pd.to_datetime(daily["date_paris"])
    daily["extracted_at"] = pd.to_datetime(daily["extracted_at"], utc=True)
    links["extracted_at"] = pd.to_datetime(links["extracted_at"], utc=True)
    extracted_at = links["extracted_at"].max()

    validate(daily, links)
    style()
    chart_daily(daily, extracted_at, args.out)
    chart_calendar(daily, extracted_at, args.out)
    chart_monthly(daily, extracted_at, args.out)
    chart_activity(links, extracted_at, args.out)
    facts = json.loads((DATA / "facts_urlr.json").read_text(encoding="utf-8"))
    cross = json.loads((DATA / "facts_urlr_cross.json").read_text(encoding="utf-8"))
    chart_size_comparison(cross, args.out)
    chart_modes(facts, args.out)
    site_path = DATA / "facts_urlr_site.json"
    if site_path.exists():
        chart_funnel(json.loads(site_path.read_text(encoding="utf-8")), facts, args.out)


if __name__ == "__main__":
    main()
