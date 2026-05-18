"""
Emits an OSMO workflow YAML for the eval sweep (post-training).
Each task picks up its trained checkpoint from `/mnt/amlfs-01/...`, runs
`dexmachina.rl.eval_rl_games` (which writes `eval_ep0.npy`), then
`dexmachina.eval.compute_add` (which writes `add.npy` + `add_stats.json`).
Outputs live next to the checkpoint, in the same NFS tree the training wrote to.

Usage:
    python workflow/generate_eval_sweep.py > workflow/eval_sweep.yaml
    osmo workflow submit workflow/eval_sweep.yaml --pool groot-l40-01
"""
import argparse
import os
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

# `ketchup-40-340-s01-u02` seed=24 crashed during training without saving checkpoints.
SKIP = {("ketchup-40-340-s01-u02", 24)}


def clip_label(clip: str) -> str:
    obj, start, end, subj, use = clip.split("-")
    return f"{obj}{start}-{end}-{subj}-{use}"


def task_block(clip: str, seed: int, image: str, base_mount: str, num_envs: int) -> str:
    label = clip_label(clip)
    task_name = f"{label}-seed{seed}-eval"
    run_name = f"sharpa-f422-{label}-seed{seed}"
    obj_name = clip.split("-")[0]
    return f"""  - name: {task_name}
    image: {image}
    command: [/bin/bash]
    args: [/tmp/entry.sh]
    files:
    - path: /tmp/entry.sh
      contents: |-
        set -e

        export WANDB_MODE=disabled

        RUN_DIR={base_mount}/{run_name}
        # rl_games saves under .../sharpa_hand/<exp_name>/nn/<files>.pth — there's
        # exactly one <exp_name> subdir per run.
        EXP_DIR=$(ls -d $RUN_DIR/sharpa_hand/*/ | head -1 | sed 's:/$::')
        echo "exp_dir=$EXP_DIR"

        # Pick the final-epoch checkpoint (ep_5000), falling back to sharpa_hand.pth.
        CKPT=$(ls $EXP_DIR/nn/last_sharpa_hand_ep_5000_*.pth 2>/dev/null | head -1)
        if [ -z "$CKPT" ]; then
            CKPT=$EXP_DIR/nn/sharpa_hand.pth
        fi
        echo "checkpoint=$CKPT"
        [ ! -f "$CKPT" ] && {{ echo "ERROR: checkpoint missing"; exit 1; }}

        cd /workspace/dexmachina-sharpa/dexmachina
        python -m dexmachina.rl.eval_rl_games \\
            --checkpoint $CKPT \\
            --num_envs {num_envs}

        # eval_rl_games saves to $EXP_DIR/<ckpt_basename>_eval/eval_ep0.npy
        CKPT_BASENAME=$(basename $CKPT .pth)
        EVAL_DIR=$EXP_DIR/${{CKPT_BASENAME}}_eval
        echo "eval_dir=$EVAL_DIR"
        ls $EVAL_DIR

        python -m dexmachina.eval.compute_add \\
            --input $EVAL_DIR \\
            --pattern "**/eval_ep*.npy" \\
            --obj_name {obj_name}

        echo "==SHARPA_EVAL_RESULT_START== {task_name}"
        cat $EVAL_DIR/add_stats.json
        echo ""
        echo "==SHARPA_EVAL_RESULT_END=="
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow_name", default="sharpa-f422-eval")
    ap.add_argument("--image", default="nvcr.io/nvstaging/isaac-amr/dexmachina-sharpa:v2")
    ap.add_argument("--base_mount", default="/mnt/amlfs-01/home/shalinj/training_outputs/dexmachina-sharpa-repro")
    ap.add_argument("--num_envs", type=int, default=20)
    args = ap.parse_args()

    header = f"""workflow:
  name: {args.workflow_name}
  resources:
    default:
      cpu: 15
      gpu: 1
      memory: 32Gi
      storage: 50Gi

  tasks:
"""
    sys.stdout.write(header)
    n = 0
    for clip in CLIPS:
        for seed in SEEDS:
            if (clip, seed) in SKIP:
                continue
            sys.stdout.write(task_block(clip, seed, args.image, args.base_mount, args.num_envs))
            n += 1
    sys.stderr.write(f"Emitted {n} eval tasks (skipped {len(SKIP)})\n")


if __name__ == "__main__":
    main()
