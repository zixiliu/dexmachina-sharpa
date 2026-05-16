"""
Emits an OSMO workflow YAML with one task per (clip, seed) combination — 35 tasks
total for the Figure-3 sweep (7 paper clips × 5 seeds). Tasks are independent
(no `inputs:` between them), so OSMO runs them in parallel.

Usage:
    python workflow/generate_sweep.py > workflow/sweep.yaml
    osmo workflow submit workflow/sweep.yaml --pool isaac-dev-h100-01

Optional CLI args override the workflow defaults (image, max_epochs, etc.).
"""
import argparse
import sys

CLIPS = [
    "box-30-230-s01-u01",
    "ketchup-30-130-s01-u01",
    "mixer-30-200-s01-u01",
    "ketchup-40-340-s01-u02",
    "mixer-40-340-s01-u01",
    "notebook-40-340-s02-u02",
    "waffleiron-40-340-s01-u01",
]
SEEDS = [42, 24, 66, 15, 113]

import os

# Read from env so we don't commit the key. Set WANDB_API_KEY before running this script
# (it's already set if you've done `wandb login`).
WANDB_KEY = os.environ.get("WANDB_API_KEY")
if not WANDB_KEY:
    raise RuntimeError(
        "WANDB_API_KEY env var not set. Run `export WANDB_API_KEY=$(awk '/api.wandb.ai/{flag=1;next}/password/&&flag{print $2;exit}' ~/.netrc)` "
        "or paste the key explicitly before invoking this script."
    )


def clip_label(clip: str) -> str:
    """Convert `box-30-230-s01-u01` -> `box30-230-s01-u01` (paper YAML key style)."""
    obj, start, end, subj, use = clip.split("-")
    return f"{obj}{start}-{end}-{subj}-{use}"


def task_block(clip: str, seed: int, image: str, base_mount: str, wandb_project: str,
               max_epochs: int, save_freq: int) -> str:
    label = clip_label(clip)
    task_name = f"{label}-seed{seed}"
    run_name = f"sharpa-f422-{task_name}"
    return f"""  - name: {task_name}
    image: {image}
    command: [/bin/bash]
    args: [/tmp/entry.sh]
    files:
    - path: /tmp/entry.sh
      contents: |-
        set -ex

        export WANDB_API_KEY={WANDB_KEY}
        export WANDB_ENTITY=nvidia-isaac

        cd /workspace/dexmachina-sharpa/dexmachina

        EXP_DIR={base_mount}/{run_name}
        mkdir -p $EXP_DIR

        echo "Starting: {run_name}  clip={clip}  seed={seed}"

        python -u rl/train_rl_games.py \\
            --hand sharpa_hand \\
            --clip {clip} \\
            --seed {seed} \\
            -B 4096 -obf -obt \\
            --max_epochs {max_epochs} --save_freq {save_freq} \\
            --actuate_object --retarget_name para --horizon 16 \\
            -imw 0.5 --gain_mode all --curr_schedule uniform \\
            --wait_epochs 100 \\
            --learning_rate 0.0003 --contact_beta 10 \\
            --upper_ratios 0.9 0.9 1 --lower_ratios 0.5 0.8 1 \\
            --group_collisions --fixed_mode uniform --uniform_mode slow \\
            --action_penalty 0.01 --dialback_ep_len 80 --skip_grad --deque_len 30 \\
            --task_rew_betas 10 1 5 --use_retarget_contact \\
            --aux_reset_thres 0 0 0 --curr_rew_thres 0.6 0.01 0 0.01 \\
            -am hybrid --hybrid_scales 0.1 1.0 \\
            --kp_init 80 --kv_init 5 \\
            -imi 0.2 -bc 0 -con 2 -ert 0.6 \\
            --wandb_project {wandb_project} \\
            -exp f422 \\
            2>&1 | tee $EXP_DIR/train.log

        cp -r logs/rl_games/sharpa_hand $EXP_DIR/ 2>/dev/null || true
        echo "Done: {run_name}"
    outputs:
      - dataset:
          name: dexmachina-sharpa:{run_name}
          path: {base_mount}/{run_name}
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow_name", default="sharpa-f422-sweep")
    ap.add_argument("--image", default="nvcr.io/nvstaging/isaac-amr/dexmachina-sharpa:v2")
    ap.add_argument("--base_mount", default="/mnt/amlfs-01/home/shalinj/training_outputs/dexmachina-sharpa-repro")
    ap.add_argument("--wandb_project", default="v2d-dexmachina-sharpa-repro")
    ap.add_argument("--max_epochs", type=int, default=5000)
    ap.add_argument("--save_freq", type=int, default=500)
    args = ap.parse_args()

    header = f"""workflow:
  name: {args.workflow_name}
  resources:
    default:
      cpu: 15
      gpu: 1
      memory: 64Gi
      storage: 100Gi

  tasks:
"""
    sys.stdout.write(header)
    for clip in CLIPS:
        for seed in SEEDS:
            sys.stdout.write(task_block(
                clip, seed, args.image, args.base_mount,
                args.wandb_project, args.max_epochs, args.save_freq,
            ))
    sys.stderr.write(f"Emitted {len(CLIPS) * len(SEEDS)} tasks for {args.workflow_name}\n")


if __name__ == "__main__":
    main()
