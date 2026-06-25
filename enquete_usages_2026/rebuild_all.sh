#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Régénère la CHAÎNE DE CALCUL canonique (facts_*) + le dashboard Flux généré, puis lance les contrats.
# Un seul point d'entrée déterministe → « régénérer les chiffres canoniques » = une commande.
#
#   bash enquete_usages_2026/rebuild_all.sh
#
# NE régénère PAS (par nature) : enquêtes multi-agents one-shot (facts_investigation/SEC_*/sections_final
# — cf. leur _meta, relancer le workflow_*.js), graphiques (make_charts*.py), dashboards à chiffres en dur
# autres que Flux (concordance contrôlée par les contrats), rapports .md (rédigés). Cf. CLAUDE.md §5.
#
# Deux niveaux (les mondes sont disjoints, cf. GLOSSAIRE §0) :
#   - étapes Capytale & transverses : reproductibles depuis le dépôt (public/data + data/ versionnés) ;
#   - étapes croisées (site×Capytale) : nécessitent le snapshot Payload LOCAL (PII) et/ou _local/.
# Les étapes croisées sont AUTO-SAUTÉES si leurs entrées locales sont absentes (machine sans snapshot) ;
# les contrats valident de toute façon l'état versionné.
# ---------------------------------------------------------------------------
set -euo pipefail
E="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"          # enquete_usages_2026/
SNAP="$(PYTHONPATH="$E" python3 -c 'import enquete_common as K; print(K.snapshot())')"
LOCAL="${MATHADATA_LOCAL:-$E/_local}"
CAPYTALE="${MATHADATA_CAPYTALE_CSV:-$E/../public/data/capytale_fresh_20260619.csv}"
if [ ! -f "$CAPYTALE" ]; then
  echo "✗ Extraction Capytale introuvable : $CAPYTALE" >&2
  exit 1
fi
export MATHADATA_CAPYTALE_CSV="$CAPYTALE"
run(){ echo "→ $1"; python3 "$E/$1"; }
skip(){ echo "⏭  SAUTÉ $1 ($2)"; }

echo "Entrée Capytale : $MATHADATA_CAPYTALE_CSV"
echo "═══ 1. Capytale (depuis public/data, toujours reproductible) ═══"
run usage-capytale/build_canonical.py
run usage-capytale/build_teachers_v2.py
run usage-capytale/compute_facts.py

echo "═══ 2. URLR × Capytale (depuis public/data, toujours reproductible) ═══"
if compgen -G "$E/../public/data/urlr_bursts_*.csv" > /dev/null; then
  run usage-urlr/build_canonical.py
else
  skip "usage-urlr/build_canonical.py" "extraction urlr_bursts_* absente ; relancer fetch_urlr.py"
fi

echo "═══ 3. Croisé site × Capytale × URLR (snapshot Payload LOCAL requis) ═══"
if [ -f "$SNAP/users.json" ]; then
  run site-vers-classe/build_payload_canonical.py
  run site-vers-classe/match_individuals.py
  run site-vers-classe/build_formation_cohorts.py
  if [ -f "$E/usage-urlr/data/sessions.csv" ]; then
    run usage-urlr/compute_site_cross.py
  else
    skip "usage-urlr/compute_site_cross.py" "sessions URLR absentes"
  fi
else
  skip "build_payload/match/formation/urlr-site" "snapshot absent: $SNAP"
fi

echo "═══ 4. Couche canonique profils + typologie (tables locales _local/ requises) ═══"
if [ -f "$LOCAL/payload_users_work.csv" ]; then
  run site-vers-classe/compute_cross_facts.py
  run transverse/build_profiles.py
  run transverse/build_master.py
else
  skip "compute_cross/build_profiles/build_master" "table locale absente: $LOCAL/payload_users_work.csv"
fi

echo "═══ 5. Transverses (depuis tables versionnées) ═══"
run transverse/build_scenarios.py
run transverse/reconcile_facts.py
run transverse/build_flux_dashboard.py

echo "═══ 6. CONTRATS (garde-fou — échoue si incohérence) ═══"
python3 "$E/transverse/check_contracts.py"
echo "✓ rebuild_all terminé. Pense à republier avec publish_pages.sh si des dashboards ont changé."
