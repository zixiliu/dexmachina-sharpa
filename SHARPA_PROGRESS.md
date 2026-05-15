# Sharpa-in-DexMachina — running log

Cross-session running log. Persistent project memory lives at `~/.claude/projects/-home-zeol-Documents-gitlab-dexmachina/memory/`.

## Goal

1. ✅ Reproduce DexMachina Figure 3 "Ours" for the four shipped hands. Done eval-only from authors' checkpoints; all 28 cells within ±0.05 pp. See `dexmachina/eval/stats/REPRO_REPORT.md`.
2. ⏳ Add Sharpa as a 5th hand alongside Inspire / Allegro / XHand / Schunk and produce a Sharpa column for Figure 3.

## Reference points

- Sharpa URDFs (likely the asset to feed DexMachina): `~/Documents/gitlab/video_to_data/robotic_grounding/source/robotic_grounding/robotic_grounding/assets/urdfs/sharpawave/{left,right,dual}_sharpa_wave[_primitive].urdf`.
- Sharpa MJCFs with SPIDER's flatten-wrist + body-quat fix already applied: `~/Documents/gitlab/spider/spider/assets/robots/sharpa/{left,right,bimanual}.xml`.
- Arctic→Sharpa retargeting script (relevant — DexMachina uses ARCTIC clips): `~/Documents/gitlab/video_to_data/robotic_grounding/scripts/retarget/arctic_to_sharpa.py`.
- SPIDER Sharpa investigation notes: `~/Documents/gitlab/spider/SHARPA_INVESTIGATION.md`, `SHARPA_TABLE1_RESULTS.md`. Includes 4-part IK fix and lessons learned about wrist body chain, alignment quat, inertias, and motor stiffness.
- DexMachina existing hand layout: `dexmachina/dexmachina/assets/<hand>_hand/` for URDFs+meshes; `dexmachina/dexmachina/envs/hand_cfgs/<hand>.py` for joint/mimic/gain config; per-hand `notes_<hand>.md` for asset-prep gotchas.
- Hand-processing pipeline: `dexmachina/dexmachina/hand_proc/` (`add_wrist_dof.py`, `minimal_retarget.py`, `tune_gains.py`, `inspect_raw_urdf.py`). Official walkthrough: https://mandizhao.github.io/dexmachina-docs/1_process_hands.html.

## Plan (high-level)

1. **Asset prep** — drop Sharpa URDF + meshes into `dexmachina/dexmachina/assets/sharpa_hand/`; produce `*_6dof.urdf` variants; write `notes_sharpa.md` describing any URDF touch-ups needed (likely add `<inertial>` to root, swap meshes if sources have issues, etc.).
2. **Hand cfg** — write `dexmachina/dexmachina/envs/hand_cfgs/sharpa.py` mirroring `inspire.py` / `allegro.py`. Covers joint mapping, mimic-joint mapping if any, gain config, and the per-hand class wired into the env constructors.
3. **Inspection / single-frame load** — use `hand_proc/inspect_raw_urdf.py` and `tune_gains.py` to validate the URDF loads in Genesis without exploding.
4. **Per-clip retargeting** — for each of the 7 ARCTIC clips, run `hand_proc/minimal_retarget.py` to produce `retargeted/sharpa_hand/<subject>/`, `contact_retarget/sharpa_hand/<subject>/`, `retargeter_results/sharpa_hand/<subject>/`. Adapt logic from `arctic_to_sharpa.py` if the dexmachina pipeline alone doesn't suffice.
5. **Single RL run smoke test** — pick one (clip, seed) and train to convergence (or partial) with `dexmachina/rl/train_rl_games.py` to make sure the RL loop is healthy on Sharpa.
6. **Full sweep** — 7 clips × 5 seeds = 35 runs. Decide compute budget with user; this is the expensive step. Use the same per-condition-set hyperparameters used for Allegro/XHand/Schunk (closest analogs: `f422-low5-th0` → `lower_ratios.kp=0.5`, `imi_rew=0.2`, `contact_rew=2`, `episode_length=300`).
7. **Eval + report** — run `dexmachina.eval.compute_add` then `group_results` with a Sharpa-extended group config to get AUC-ADD per (clip, seed). Append a Sharpa column to the comparison table in `dexmachina/eval/stats/REPRO_REPORT.md`.

## Open questions / decisions to make with user

- **Wrist DOF source.** Use existing `*_sharpa_wave.urdf` + DexMachina's `add_wrist_dof.py`, or start from the SPIDER MJCF (which already has flattened wrist + correct body quat) and convert MJCF→URDF? The SPIDER MJCF carries lessons learned that the raw URDF doesn't.
- **Bimanual vs single-side.** DexMachina trains bimanual policies; Sharpa needs a paired left+right. The `dual_sharpa_wave.urdf` exists in robotic_grounding — check if that's the right format.
- **Compute scope for the sweep.** 35 runs × ~hours/run = days of GPU. Confirm budget before kicking off.
- **Mimic joints.** Inspire has them and `notes_inspire.md` describes a manual mapping. Sharpa likely has similar tendon-driven structure; need to inspect URDF.
- **Genesis vs MJWP differences.** SPIDER's Sharpa NaN explosion came from MJWP's stiff actuator + low Sharpa inertia. Genesis has different solver dynamics; lessons may not transfer 1:1.

## Log

### 2026-05-08

- Reproduced Figure 3 "Ours" exactly from authors' released checkpoints (28/28 cells within ±0.05 pp). Report: `dexmachina/eval/stats/REPRO_REPORT.md`.
- Patched two `np.trapz` call sites for NumPy 2.x; commit `6dc99ad` on branch `fix/numpy2-trapezoid-compat`. Branch ready to push as PR when GitHub auth is available; not pushed (no `gh` CLI / `GITHUB_TOKEN` in env).
- Surveyed existing Sharpa work in `spider` (SHARPA_INVESTIGATION.md, SHARPA_TABLE1_RESULTS.md, `assets/robots/sharpa/*`) and `video_to_data/robotic_grounding` (URDFs, MJCFs, arctic→sharpa retargeting script). Recorded artifact locations and lessons-learned in memory at `~/.claude/projects/-home-zeol-Documents-gitlab-dexmachina/memory/`.
- Wrote initial memory entries (user, project × 3, reference × 2, feedback × 2) and this running log.
- **Confirmed no upstream Sharpa work** on `MandiZhao/dexmachina` (only `main` branch, no open/closed PRs, no Sharpa-mentioning issues, no Sharpa branches on `MandiZhao/Genesis`). Forging fresh ground.
- **Decision: start from raw URDF in robotic_grounding** rather than spider's MJCFs.
- **Asset prep done.** Copied URDFs + meshes from `robotic_grounding/source/.../assets/{urdfs/sharpawave,meshes/sharpa_wave}/` into `dexmachina/dexmachina/assets/sharpa_hand/` (24 MB). Patched mesh paths from `../meshes/sharpa_wave/` → `meshes/sharpa_wave/` so the layout is self-contained (matches schunk/xhand convention).
- **6-DOF Sharpa URDFs generated.** Sharpa's raw URDF lacks the `<joint name="fixed" type="fixed">` root joint that `add_wrist_dof.py` requires. Wrote `dexmachina/hand_proc/prep_sharpa.py` to scaffold (prepend `<side>_base` link + fixed root joint) then run `add_forearm_dof`. Outputs: `left_sharpa_wave_6dof.urdf` and `right_sharpa_wave_6dof.urdf` (39 joints = 6 forearm + 1 fixed + 32 finger).
- Authored `dexmachina/dexmachina/assets/sharpa_hand/notes_sharpa.md` capturing source provenance, Sharpa-specific quirks (no mimics, root link `*_hand_C_MC`, elastomer geoms, weak motor stiffness), and SPIDER lessons that *may* apply.
- **Blocked on Genesis runtime** for next steps. `inspect_raw_urdf.py`, `tune_gains.py`, `minimal_retarget.py` all import `genesis as gs` at module top; need a conda env with the dexmachina dependencies. Surfacing to user.
- **Env set up via `uv` (not conda)** at `dexmachina/.venv/` (Python 3.10.20). Installed: torch 2.5.1+cu124, MandiZhao/Genesis @ older branch (`e9df2d8`, cloned to `~/Documents/gitlab/Genesis`), libigl 2.5.1, MandiZhao/rl_games (`~/Documents/gitlab/rl_games`), dexmachina editable, dex-retargeting, moviepy 1.0.3, gymnasium/ray/seaborn/wandb/trimesh/lxml/opencv. 3 GPUs detected (2× RTX 6000 Ada 49 GB each, 1× RTX A400 4 GB). Genesis 0.2.1 runs on CUDA. README convention is conda; uv is faster and equivalent for this stack.
- **Bug + fix in `prep_sharpa.py`.** First attempt at the URDF scaffold passed `--base_link=<side>_base` (the outer placeholder), causing `add_wrist_dof.add_forearm_dof` to insert a cycle: `<side>_base ↔ R_forearm_tx_link` plus a disconnected hand body. Fixed by passing `--base_link=<side>_hand_C_MC` (the wrist body) and renaming the outer placeholder to `<side>_root`. Inspire's reference URDF follows the same pattern: outer `root` → `base_link` (the wrist body) via fixed joint, with `--base_link=base_link`.
- **Genesis URDF load: ✅** `right_sharpa_wave_6dof.urdf` parses cleanly. 40 links, 28 actuated DOFs (6 forearm prismatic+revolute + 22 finger revolute joints). Finger joint anatomy: thumb (CMC_FE/AA, MCP_FE/AA, IP), index/middle/ring (MCP_FE/AA, PIP, DIP), pinky (CMC, MCP_FE/AA, PIP, DIP). Fingertip link names: `<side>_<thumb|index|middle|ring|pinky>_fingertip`.
- **Hand cfg authored.** `dexmachina/dexmachina/envs/hand_cfgs/sharpa.py` (mirrors `inspire.py` structure). Wrist link `<side>_hand_C_MC`, no mimic joints, 5 fingertip keypoints, 6 forearm joint limits, 28-element default_qpos. Three actuator regex groups: `finger` (kp=20), `wrist_rot` (kp=80), `wrist_trans` (kp=350). `collision_groups` left empty until link indices are confirmed via `inspect_raw_urdf.py --gather_geoms` (env falls back to disabled self-collision; fine for first pass).
- **Test passes.** `dexmachina/tests/test_new_hand_cfg.py --hand sharpa_hand` resolves both sides through `get_default_robot_cfg` cleanly.

### 2026-05-12

- **Authored `dexmachina/assets/sharpa_hand/retarget_config.yaml`** — dex_retargeting config listing all 28 actuated joints (6 forearm + 22 finger) as `target_joint_names`, 5 fingertip links + MANO indices 16–20.
- **Tried `minimal_retarget.py` first** — works (saves `(T, 28)` `hand_qpos`) but it's diagnostic only and enters a blocking viewer `while True:` after save. Wrote `dexmachina/hand_proc/retarget_only.py` as a loop-free batch driver, but realised this is also the wrong output format (env wants `data["demo_data"]` + `data["retarget_data"]`).
- **`parallel_retarget.py` is the production retargeting** — does dex_retargeting per frame, drives the simulated hand to track the qpos in a parallel envs (one env per demo frame), saves `retarget_data` (joint_qpos / joint_targets / kpt_pos / kpt_names / wrist_pose) + `retargeter_results` + `demo_data` to `assets/retargeted/<hand>/<subject>/<obj>_use_<clip>_vector_para.pt`. Also saves `assets/retargeter_results/<hand>/<subject>/<obj>_use_<clip>_vector.npy`.
- **First retarget pass had a frame-indexing bug.** Saved arrays with `-B N --clip <obj>-<S>-<E>` are only N frames long and represent demo frames `[S, S+N)`. But the env loader slices `data[frame_start:frame_end]` using **absolute source-frame indices** (verified at `dexmachina/envs/constructors.py:60-82`). Fix: re-ran with `--clip <obj>-0-<max_end>-<subject>-<u>` so the saved arrays are aligned to source frame 0.
- **Final retargeted set (6 source demos, each covering ≥ max clip end):**
  - `s01/box_use_01_vector_para.pt` — 230 frames
  - `s01/ketchup_use_01_vector_para.pt` — 130 frames
  - `s01/ketchup_use_02_vector_para.pt` — 340 frames
  - `s01/mixer_use_01_vector_para.pt` — 340 frames (covers both `mixer-30-200` and `mixer-40-340`)
  - `s01/waffleiron_use_01_vector_para.pt` — 340 frames
  - `s02/notebook_use_02_vector_para.pt` — 340 frames
- Control errors after parallel sim tracking are ~5e-4 mean, max ~2e-3 — Sharpa hand tracks the dex_retargeting qpos cleanly in Genesis.
- **`map_contacts.py` for contact retargeting** — produces `assets/contact_retarget/<hand>/<subject>/<obj>_use_<clip>.npy` (the second file the env loads). Two gotchas:
  - Needed `scikit-learn` not in the README deps (was missing → installed via `uv pip install scikit-learn`).
  - The script's asset dir lookup at line 382 uses raw `args.hand` (no `_hand` suffix added), so must pass `--hand sharpa_hand` explicitly. (Inconsistent with `parallel_retarget.py`, which normalizes via `args.hand = ...; hand_name = args.hand if "hand" in args.hand else f"{args.hand}_hand"`.)
- **First box contact retarget: ✅** `contact_retarget/sharpa_hand/s01/box_use_01.npy` saved with `dexlink_contacts.shape = (230, 2, 26, 4)` (26 collision links on Sharpa; inspire has 13).
- **All 6 contact retargets done.** `assets/contact_retarget/sharpa_hand/{s01,s02}/` covers all 6 source demos. Shapes all `(T, 2, 26, 4)` for `dexlink_contacts`.
- **End-to-end data load verified.** `load_genesis_retarget_data` + `load_contact_retarget_data` called with each of the 7 Figure-3 clip specs all return correct frame counts (matching `end - start`) and shapes. Sharpa is now data-ready for RL training; task #20 complete.
