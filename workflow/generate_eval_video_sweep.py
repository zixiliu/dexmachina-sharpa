"""
Same as `generate_eval_sweep.py` but records a video per (clip, seed) task and
puts it in OSMO's `{{output}}` dir so we can pull videos via `osmo dataset` once
the workflow completes. Re-runs eval (~few min per task) since the previous
sweep didn't record video.
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
SKIP = {("ketchup-40-340-s01-u02", 24)}


def clip_label(clip: str) -> str:
    obj, start, end, subj, use = clip.split("-")
    return f"{obj}{start}-{end}-{subj}-{use}"


def task_block(clip: str, seed: int, image: str, base_mount: str, num_envs: int) -> str:
    label = clip_label(clip)
    task_name = f"{label}-seed{seed}-video"
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
        EXP_DIR=$(ls -d $RUN_DIR/sharpa_hand/*/ | head -1 | sed 's:/$::')
        CKPT=$(ls $EXP_DIR/nn/last_sharpa_hand_ep_5000_*.pth 2>/dev/null | head -1)
        [ -z "$CKPT" ] && CKPT=$EXP_DIR/nn/sharpa_hand.pth
        [ ! -f "$CKPT" ] && {{ echo "ERROR: checkpoint missing"; exit 1; }}
        echo "checkpoint=$CKPT"

        cd /workspace/dexmachina-sharpa/dexmachina
        python -m dexmachina.rl.eval_rl_games \\
            --checkpoint $CKPT \\
            --num_envs {num_envs} \\
            --record_video

        # eval_rl_games saves video.mp4 to $EXP_DIR/<ckpt_basename>_eval/video.mp4
        CKPT_BASENAME=$(basename $CKPT .pth)
        EVAL_DIR=$EXP_DIR/${{CKPT_BASENAME}}_eval
        ls $EVAL_DIR
        VIDEO=$EVAL_DIR/video.mp4
        [ ! -f "$VIDEO" ] && {{ echo "ERROR: video missing"; exit 1; }}

        # Copy to OSMO-managed output so it gets uploaded as a dataset.
        # `{{% raw %}}{{{{output}}}}{{% endraw %}}` escapes the inner `{{{{output}}}}` from osmo's submit-time
        # Jinja so it survives until runtime substitution.
        cp $VIDEO {{% raw %}}{{{{output}}}}{{% endraw %}}/{task_name}.mp4
        echo "video uploaded to OSMO at {task_name}.mp4 ($(du -h $VIDEO | cut -f1))"
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workflow_name", default="sharpa-f422-video")
    ap.add_argument("--image", default="nvcr.io/nvstaging/isaac-amr/dexmachina-sharpa:v3")
    ap.add_argument("--base_mount", default="/mnt/amlfs-01/home/shalinj/training_outputs/dexmachina-sharpa-repro")
    ap.add_argument("--num_envs", type=int, default=4)
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
    sys.stderr.write(f"Emitted {n} video-eval tasks\n")


if __name__ == "__main__":
    main()
