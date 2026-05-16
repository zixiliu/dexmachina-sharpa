"""
Automates the docs' three-phase gain tuning loop (wrist_trans -> wrist_rot -> finger).
Each group is tuned by sweeping kp with kv=0, then kv with the chosen kp fixed,
and finally validated on the full retargeted trajectory.

Drives `hand_proc/tune_gains.py --auto_continue` as subprocess and parses
per-iter `mean_err_*` lines from stdout. Reports a paste-ready cfg block.

Run from the `dexmachina/` directory:
    python hand_proc/auto_tune_gains.py --hand sharpa --clip box-0-230-s01-u01
"""
import argparse
import re
import subprocess
import sys

KP_SWEEP_RANGES = {
    "wrist_trans": (50.0, 1000.0),
    "wrist_rot": (20.0, 300.0),
    "finger": (5.0, 150.0),
}
KV_SWEEP_RANGE = (0.1, 100.0)
NUM_ITERS = 10

ITER_RE = re.compile(
    r"iter (\d+): kp=([\d.]+) kv=([\d.]+) "
    r"mean_err_left=([\d.]+)m std=([\d.]+) "
    r"mean_err_right=([\d.]+)m std=([\d.]+)"
)


def run_tune_gains(hand, clip, group, kp_lo, kp_hi, kv_lo, kv_hi, step_response):
    cmd = [
        sys.executable, "hand_proc/tune_gains.py",
        "--hand", hand, "--clip", clip,
        "--joint_group", group,
        "--num_iters", str(NUM_ITERS),
        "--kp", str(kp_lo), str(kp_hi),
        "--kv", str(kv_lo), str(kv_hi),
        "--force_range", "100.0", "100.0",
        "--skip_object", "--freespace", "--auto_continue",
    ]
    if step_response:
        cmd.append("--step_response")
    print(f"$ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        return []
    rows = []
    for line in proc.stdout.splitlines():
        m = ITER_RE.search(line)
        if not m:
            continue
        err_mean = (float(m[4]) + float(m[6])) / 2
        std_mean = (float(m[5]) + float(m[7])) / 2
        rows.append({
            "iter": int(m[1]), "kp": float(m[2]), "kv": float(m[3]),
            "err": err_mean, "std": std_mean,
        })
    return rows


def pick_best(rows, key="err"):
    return min(rows, key=lambda r: r[key]) if rows else None


def tune_group(hand, clip, group):
    kp_lo, kp_hi = KP_SWEEP_RANGES[group]
    print(f"\n{'='*60}\n  {group}: phase 1 - sweep kp with kv=0\n{'='*60}")
    rows = run_tune_gains(hand, clip, group, kp_lo, kp_hi, 0.0, 0.0, step_response=True)
    best_kp = pick_best(rows)
    if best_kp is None:
        print(f"  ERROR: phase 1 produced no parsable output for {group}")
        return None
    print(f"\n  -> best kp = {best_kp['kp']:.2f}  (err={best_kp['err']:.5f}m, std={best_kp['std']:.5f})")

    kv_lo, kv_hi = KV_SWEEP_RANGE
    print(f"\n{'='*60}\n  {group}: phase 2 - sweep kv with kp={best_kp['kp']:.2f}\n{'='*60}")
    rows = run_tune_gains(hand, clip, group, best_kp["kp"], best_kp["kp"], kv_lo, kv_hi, step_response=True)
    best_kv = pick_best(rows)
    if best_kv is None:
        print(f"  ERROR: phase 2 produced no parsable output for {group}")
        return None
    print(f"\n  -> best kv = {best_kv['kv']:.2f}  (err={best_kv['err']:.5f}m, std={best_kv['std']:.5f})")

    print(f"\n{'='*60}\n  {group}: phase 3 - validate on full trajectory\n{'='*60}")
    rows = run_tune_gains(hand, clip, group, best_kp["kp"], best_kp["kp"], best_kv["kv"], best_kv["kv"], step_response=False)
    validation = pick_best(rows)
    val_err = validation["err"] if validation else float("nan")
    print(f"\n  -> validation err on full trajectory = {val_err:.5f}m")

    return {"kp": best_kp["kp"], "kv": best_kv["kv"], "val_err": val_err}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hand", default="sharpa")
    ap.add_argument("--clip", default="box-0-230-s01-u01")
    ap.add_argument("--groups", nargs="+", default=["wrist_trans", "wrist_rot", "finger"])
    args = ap.parse_args()

    tuned = {}
    for group in args.groups:
        result = tune_group(args.hand, args.clip, group)
        if result is not None:
            tuned[group] = result

    print(f"\n\n{'='*60}\n  Tuned gains for {args.hand}\n{'='*60}")
    if not tuned:
        print("  No groups tuned successfully.")
        return
    print(f"  Paste into dexmachina/envs/hand_cfgs/{args.hand}.py inside `_ACTUATORS`:\n")
    for group, g in tuned.items():
        print(f'    "{group}": dict(')
        print(f"        joint_exprs=[...],")
        print(f"        kp={g['kp']:.1f},")
        print(f"        kv={g['kv']:.2f},")
        print(f"        force_range=50.0,")
        print(f"    ),  # validation err on full traj = {g['val_err']:.5f}m")


if __name__ == "__main__":
    main()
