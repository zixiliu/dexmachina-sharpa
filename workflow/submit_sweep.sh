#!/bin/bash
# Generates a single multi-task OSMO workflow YAML containing all 35 jobs
# (7 paper clips × 5 seeds) and submits it. Pattern 1 from gr00t's workflow-patterns
# reference (independent parallel tasks; all run on separate pods).
#
# Usage: bash workflow/submit_sweep.sh <pool-name> [dry]
#   pool-name : e.g. isaac-dev-h100-01, isaac-dev-l40s-04
#   dry       : if "dry", only emit the YAML; do not submit

set -e

POOL=${1:?Usage: $0 <pool-name> [dry]}
DRY=${2:-}
YAML=workflow/sweep.yaml

python workflow/generate_sweep.py > $YAML
echo "Generated $YAML ($(wc -l < $YAML) lines, $(grep -c '  - name:' $YAML) tasks)"

if [ "$DRY" = "dry" ]; then
    echo "Dry-run; not submitting. Inspect $YAML."
    exit 0
fi

osmo workflow submit $YAML --pool $POOL
