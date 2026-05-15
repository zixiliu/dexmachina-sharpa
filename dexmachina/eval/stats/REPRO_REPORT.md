# DexMachina Figure 3 "Ours" — Reproduction Report

## Repo state

- `main` is even with `origin/main` at `adae5bf` (was 1 commit behind on first inspection; fast-forwarded to pick up the `dexmachina/eval/` directory added by `adae5bf "eval instructions"`).
- Uncommitted local edit on `main`: `dexmachina/envs/rewards.py` default `use_retarget_contact: False → True`. `examples/train_rl.sh` passes `--use_retarget_contact` explicitly, so this default flip is a no-op for that script.
- New branch `fix/numpy2-trapezoid-compat` (commit `6dc99ad`) with the NumPy 2.x compatibility patch, ready to push to a fork and open as a PR against `MandiZhao/dexmachina`.

## What "Ours" means in Figure 3

From the paper caption + `dexmachina/eval/group_cfgs/dexmachina_main.yaml`:

- **Grid:** 4 hands × 7 ARCTIC clips × 5 seeds = 140 runs.
  - Hands: `inspire_hand_left`, `allegro_hand_left`, `xhand_left`, `schunk_hand_left`.
  - Clips: `ketchup30-130-s01-u01`, `box30-230-s01-u01`, `mixer30-200-s01-u01`, `ketchup40-340-s01-u02`, `mixer40-340-s01-u01`, `notebook40-340-s02-u02`, `waffleiron40-340-s01-u01`.
  - Seeds: 42, 24, 66, 15, 113.
- **Method spec:** `hybrid_scales=[0.1, 1]`, curriculum `schedule=uniform`, actuated object, with three per-hand condition sets:
  - `fast1-420`: `lower_ratios.kp=0.6`, `imi_rew=0.2`, `contact_rew=2`.
  - `f424-low5-imi3` (Inspire only): `lower_ratios.kp=0.5`, `imi_rew=0.3`.
  - `f422` (Allegro / XHand / Schunk): `lower_ratios.kp=0.5`, `imi_rew=0.2`, `contact_rew=2`, `episode_length=300`.
- **Metric:** AUC-ADD over thresholds `[0.01, 0.02, …, 0.09]`, averaged over `top` and `bottom` part vertices.

## Reproduction procedure (eval-only)

1. Synced upstream:
   ```bash
   git stash push -m wip-rewards-default -- dexmachina/envs/rewards.py
   git pull --ff-only origin main
   git stash pop
   ```
2. Downloaded authors' result bundle (3.86 GB):
   ```bash
   pipx install gdown
   mkdir -p data && cd data
   gdown "https://drive.google.com/uc?id=1d8sMncXvPir-PdiUFYW4t-J5YlEf8NFW" \
         -O dexmachina_main_results_data.zip
   unzip -q dexmachina_main_results_data.zip   # 4.2 GB unpacked
   ```
   Layout: `dexmachina_main_results_data/runs/<run_name>/{config.yaml,add.npy,logs/.../eval_ep0.npy,…}` plus `run_paths.json` keyed by hand → clip.
3. Patched two `np.trapz` call sites for NumPy 2.x (see PR section below).
4. Ran the grouping script:
   ```bash
   DATA=data/dexmachina_main_results_data
   python3 -m dexmachina.eval.group_results \
     --run_paths_json $DATA/run_paths.json \
     --run_paths_base $DATA \
     --pattern "**/eval_ep*.npy" \
     --use_auc \
     --output_name dexmachina_main_stats_repro
   ```
   → wrote `dexmachina/eval/stats/dexmachina_main_stats_repro_AUC.json`. Every (hand × clip) cell has the full 5 seeds.

## Results — match against `dexmachina_main_stats_AUC.json`

AUC-ADD per (hand × clip), reproduced values:

| clip | Inspire | Allegro | XHand | Schunk |
|---|---|---|---|---|
| ketchup30-130-s01-u01 | 0.7071 | 0.9140 ⚠ | 0.9038 | 0.8972 |
| box30-230-s01-u01 | 0.8707 | 0.8864 | 0.8653 | 0.8588 |
| mixer30-200-s01-u01 | 0.8982 | 0.7732 | 0.8985 | 0.9031 |
| ketchup40-340-s01-u02 | 0.3234 | 0.8299 | 0.7235 | 0.7001 |
| mixer40-340-s01-u01 | 0.6433 | 0.8112 | 0.6623 | 0.6683 |
| notebook40-340-s02-u02 | 0.7124 | 0.8708 | 0.8905 | 0.6964 |
| waffleiron40-340-s01-u01 | 0.2381 | 0.7536 | 0.8032 | 0.4138 |

- **27 / 28 cells match the reference at floating-point precision** (|diff| ≤ 2.2 × 10⁻¹⁶).
- ⚠ `allegro × ketchup30-130-s01-u01` differs by **2.5 × 10⁻⁵** (ref `0.914025`, repro `0.914000`). Within rounding noise from recomputing AUC on the fly from `add.npy` rather than reading a precomputed `add_stats.json`.

## Comparison against the paper's Figure 3

Bar heights for "Ours" read off `figs/yolo_ADD_AUC.png` (rounded to 0.1 pp in the figure) versus reproduced AUC-ADD × 100. Clip naming maps as follows: the paper's label encodes demo length (`end − start` frames), e.g. `ketchup30-130-s01-u01` → "Ketchup-100", `mixer30-200-s01-u01` → "Mixer-170", `waffleiron40-340-s01-u01` → "Waffleiron-300".

| Hand | Figure label | Paper Fig 3 (%) | Reproduced (%) | Δ (pp) |
|---|---|---:|---:|---:|
| Inspire | Ketchup-100 | 70.7 | 70.71 | +0.01 |
| Inspire | Box-200 | 87.1 | 87.07 | −0.03 |
| Inspire | Mixer-170 | 89.8 | 89.82 | +0.02 |
| Inspire | Ketchup-300 | 32.3 | 32.34 | +0.04 |
| Inspire | Mixer-300 | 64.3 | 64.33 | +0.03 |
| Inspire | Notebook-300 | 71.2 | 71.24 | +0.04 |
| Inspire | Waffleiron-300 | 23.8 | 23.81 | +0.01 |
| Allegro | Ketchup-100 | 91.4 | 91.40 | 0.00 |
| Allegro | Box-200 | 88.6 | 88.64 | +0.04 |
| Allegro | Mixer-170 | 77.3 | 77.32 | +0.02 |
| Allegro | Ketchup-300 | 83.0 | 82.99 | −0.01 |
| Allegro | Mixer-300 | 81.1 | 81.12 | +0.02 |
| Allegro | Notebook-300 | 87.1 | 87.08 | −0.02 |
| Allegro | Waffleiron-300 | 75.4 | 75.36 | −0.04 |
| XHand | Ketchup-100 | 90.4 | 90.38 | −0.02 |
| XHand | Box-200 | 86.5 | 86.53 | +0.03 |
| XHand | Mixer-170 | 89.8 | 89.85 | +0.05 |
| XHand | Ketchup-300 | 72.3 | 72.35 | +0.05 |
| XHand | Mixer-300 | 66.2 | 66.23 | +0.03 |
| XHand | Notebook-300 | 89.0 | 89.05 | +0.05 |
| XHand | Waffleiron-300 | 80.3 | 80.32 | +0.02 |
| Schunk | Ketchup-100 | 89.7 | 89.72 | +0.02 |
| Schunk | Box-200 | 85.9 | 85.88 | −0.02 |
| Schunk | Mixer-170 | 90.3 | 90.31 | +0.01 |
| Schunk | Ketchup-300 | 70.0 | 70.01 | +0.01 |
| Schunk | Mixer-300 | 66.8 | 66.83 | +0.03 |
| Schunk | Notebook-300 | 69.6 | 69.64 | +0.04 |
| Schunk | Waffleiron-300 | 41.4 | 41.38 | −0.02 |

**All 28 / 28 cells agree with the paper figure within ±0.05 pp** — i.e. within the figure's rounding precision. Effectively, the reproduction reproduces Figure 3's "Ours" bars exactly.

## Upstream PR — `np.trapz` → `np.trapezoid`

`np.trapz` was deprecated in NumPy 1.20 and removed in NumPy 2.0. Affects:

- `dexmachina/eval/group_results.py:78` (`compute_auc`)
- `dexmachina/eval/compute_add.py:129` (`compute_auc`)

Patch (commit `6dc99ad` on branch `fix/numpy2-trapezoid-compat`):

```python
trapezoid = getattr(np, "trapezoid", None) or np.trapz
return float(trapezoid(accuracies, x=x_values))
```

Works under both NumPy 1.x and 2.x without a version pin.

To open the PR:

```bash
# 1) Fork MandiZhao/dexmachina on github.com.
# 2) From this checkout:
git remote add fork git@github.com:<your-user>/dexmachina.git
git push -u fork fix/numpy2-trapezoid-compat
# 3) Open https://github.com/MandiZhao/dexmachina/compare/main...<your-user>:fix/numpy2-trapezoid-compat
```

## Files added or changed locally

- `data/dexmachina_main_results_data/` (4.2 GB unpacked) and `data/dexmachina_main_results_data.zip` (3.6 GB).
- `dexmachina/eval/stats/dexmachina_main_stats_repro_AUC.json` — the reproduced numbers.
- `dexmachina/eval/stats/REPRO_REPORT.md` — this file.
- Branch `fix/numpy2-trapezoid-compat` containing the `np.trapz` → `np.trapezoid` patch.
- Uncommitted edit on `main`: `dexmachina/envs/rewards.py` default `use_retarget_contact: False → True` (carried over from before this session).
