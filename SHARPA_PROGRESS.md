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

### 2026-05-15 — reproduction on shalinj machine

Picking up the branch on a new machine (`shalinj@f8cfcba-lcedt`, separate from the `zeol` machine the earlier work was done on). Validating end-to-end before re-retargeting + RL. **Key finding: the prior asset prep was incomplete in two material ways** — collision_groups were empty, and gains were never tuned (inspire's values were left in place as placeholders). Fixed both this session.

**Environment / Genesis version.**
- Conda env `dexmachina` (Python 3.10, torch 2.5.1+cu124) — different setup from the zeol machine's `uv`-based venv.
- Genesis was cloned at `dexmachina-sharpa/Genesis/` rather than `~/Documents/gitlab/Genesis`. HEAD was on `506e2b4 merge` (post-upstream-merge); URDF parsing in this revision returns inhomogeneous `link.inertial_quat` shapes, crashing every example with `ValueError: setting an array element with a sequence. ... shape (29,) + inhomogeneous part` at `rigid_solver_decomp.py:640`. Allegro reproduces the bug, so it's Genesis-wide, not Sharpa-specific.
- Fix: `git -C Genesis checkout e9df2d8` (the "revert to older version" snapshot the zeol notes pinned). `inspect_hand.py --hand allegro_hand --vis` runs cleanly after this. **dexmachina-sharpa's `setup.py` / README do not pin a Genesis commit** — anyone cloning today gets the broken HEAD. Worth a doc fix upstream eventually.

**Asset prep gap #1 — collision_groups was `{}`.**
- `dexmachina/envs/hand_cfgs/sharpa.py` had `"collision_groups": {}` for both left and right (with a comment "intentionally empty until link indices are confirmed"). Every other hand in the repo has a populated `{link_idx: group_id}` dict. The training env uses these to filter self-collision and to bucket contact-retarget data.
- Ran the docs-prescribed gather step:
  ```bash
  cd dexmachina-sharpa/dexmachina
  python hand_proc/inspect_raw_urdf.py --gather_geoms --num_envs 1 \
      --urdf_path assets/sharpa_hand/right_sharpa_wave_6dof.urdf \
      --base_link_name right_hand_C_MC
  # repeat with left_sharpa_wave_6dof.urdf and left_hand_C_MC
  ```
- Both URDFs produced the same 22-entry dict (kinematic symmetry confirmed):
  `{7:0, 13:1,23:1,28:1,33:1, 14:2,19:2,24:2,29:2, 15:3,20:3,25:3,30:3, 16:4,21:4,26:4,31:4, 17:5,22:5,27:5,32:5,37:5}` — palm in group 0, thumb=1, index=2, middle=3, ring=4, pinky=5.
- Pasted into both `SHARPA_LEFT_CFG["collision_groups"]` and `SHARPA_RIGHT_CFG["collision_groups"]`.

**Asset prep gap #2 — gains were inspire copies, never actually tuned.**
- `notes_sharpa.md` explicitly flagged `tune_gains.py` as the unfinished step ("intended for exactly this calibration step — run it before any sweep"). Previous run never executed it; `sharpa.py` shipped with `finger.kp=20, wrist_rot.kp=80, wrist_trans.kp=350` copied from `inspire.py`.
- Discovered `tune_gains.py` requires visual judgment at a `breakpoint()` between iterations — qualitative and hard to be systematic about. Found a latent bug in `hand_utils.py:generate_90degree_rotation_quaternions` (`quaternion_multiply` / `is_duplicate_rotation` are called but never defined; commit `60d3ee5` by Mandi Zhao, never exercised before because `--iterate_quat` was the only caller). Documented upstream; didn't fix since not needed.
- Patched `dexmachina/hand_proc/tune_gains.py` to log mean tracking error + std per iter (queries `entity.get_dofs_position()` on env 0 vs env 1 and accumulates), and added an `--auto_continue` flag that skips the interactive `breakpoint()`s. Makes the script usable in batch.
- Added `dexmachina/hand_proc/auto_tune_gains.py` — wrapper that runs the docs' three-phase methodology end-to-end per joint group: sweep kp with kv=0 (`--step_response`), sweep kv with the chosen kp fixed, then validate on the full trajectory. Drives `tune_gains.py` via subprocess and parses per-iter `mean_err_*` lines. Reports paste-ready cfg block.
- Ran:
  ```bash
  cd dexmachina-sharpa/dexmachina
  python hand_proc/auto_tune_gains.py --hand sharpa --clip box-0-230-s01-u01 \
      2>&1 | tee logs/auto_tune_sharpa.log
  ```
- Tuned gains (now in `_ACTUATORS` of `sharpa.py`):
  - `wrist_trans`: kp=261.1, kv=11.2 (validation err 0.0069m on full traj)
  - `wrist_rot`:   kp=300.0, kv=11.2 (validation err 0.0348 rad) — hit kp ceiling of sweep range
  - `finger`:      kp=150.0, kv=11.2 (validation err 0.0310 rad) — hit kp ceiling, but curve already plateauing
- Visually verified with viewer (`tune_gains.py --num_iters 1 --kp 261.1 261.1 --kv 11.2 11.2 -v --spacing 0.5`) — env 0 (PD-controlled) tracks env 1 (kinematic reference) cleanly on the full box trajectory. Marked acceptable. Could revisit by widening the kp search if RL struggles with wrist_rot / finger tracking.

**Right-hand body-frame asymmetry (observed, deferred).**
- Visually inspecting Sharpa's URDFs at qpos=0: left hand body frame is `X=right, Y=down, Z=fwd` (palm normal -Y); right hand is `X=left, Y=up, Z=fwd` (palm normal +Y). The two URDFs are **not mirror-symmetric** in their root body frame — known property from SPIDER/robotic_grounding prior work.
- `get_base_rotation()` in `inspect_raw_urdf.py` is the only place in this repo that does per-hand quat fixup, and it's viewer-only — never read by `parallel_retarget.py`, env, or RL. Production paths absorb body-frame mismatch through the 6 added forearm DOFs (`tx/ty/tz/roll/pitch/yaw`).
- Confirmed this absorption is already happening in `sharpa.py`: `R_forearm_yaw_link_joint` limits are `(2.50, 3.10)` rad, while `L_forearm_yaw_link_joint` limits are `(-0.70, 0.40)` — an offset of ~180°, exactly the body-frame asymmetry. So the retargeter has range to compensate.
- Decision: **leave as is**. If RL struggles with right-hand wrist orientation, revisit by either (a) baking a corrective quat into the right URDF via `prep_sharpa.py`, (b) plumbing `get_base_rotation()` through `parallel_retarget.py`'s `gs.morphs.URDF(...)` spawn. Both require re-retargeting.

**Other notes_sharpa.md items still open.**
- Wrist link inertias on `*_thumb_CMC_VL` are tiny (`mass=2.5e-3`, `inertia≈1e-7`); SPIDER had to bump these for MuJoCo. Not exercised yet — only surfaces under contact-rich RL.
- Elastomer geom `solref` parameters — same.
- These can wait until the RL smoke test reveals (or fails to reveal) instability.

**State after first pass.**
- `sharpa.py` updated with both fixes (collision_groups + tuned gains).
- `tune_gains.py` has the new error-logging + `--auto_continue`.
- `auto_tune_gains.py` is a new wrapper.

**Re-retargeting with tuned gains (steps D + E from Runbook).**
- Step D (`parallel_retarget.py × 6`, ~30 min) completed cleanly. All 6 `.pt` files in `assets/retargeted/sharpa_hand/` regenerated with the tuned gains.
- Step E (`map_contacts.py × 6`) failed on first attempt because the runbook had the wrong `--load_fname` (was pointing at the retargeter output; the script internally appends `_vector` and wants the ARCTIC source path). Fixed in Runbook E. Rerun completed; all 6 contact files in `assets/contact_retarget/sharpa_hand/` regenerated with shape `(T, 2, 26, 4)`.
- **Tracking error pattern** — right hand stays tight (<2cm max) across all clips. **Left hand spikes on the 340-frame clips:**
  | Clip | Left mean / max | Right mean / max |
  |---|---|---|
  | box (230f)        | 0.0007 / 0.0007m  | 0.0007 / 0.0007m |
  | ketchup-130       | 0.0007 / 0.0007m  | 0.0007 / 0.0007m |
  | ketchup-340       | 0.013 / 0.181m    | 0.001 / 0.016m |
  | mixer-340         | 0.013 / 0.137m    | 0.002 / 0.023m |
  | waffleiron-340    | 0.044 / 0.241m    | 0.001 / 0.004m |
  | notebook-340      | 0.046 / 0.163m    | 0.001 / 0.015m |
- Short clips (130, 230) are bit-clean on both sides. Long clips reveal a left-side issue, presumably either a joint-limit hit during fast wrist transients or a dex_retargeting asymmetry. Confirmed pending — visualize `minimal_retarget.py --clip waffleiron-0-340-s01-u01 --vis --show_mano --show_object -o` and see whether the left hand kinematic target itself looks wrong, or if it's purely a sim-tracking transient.
- Sharpa is data-ready for RL. The left-side spikes mean the policy will learn from sim-tracked references that have 4-24cm errors on a subset of frames in 4 of 7 paper clips. Decide before RL whether to investigate or accept. **User decision: visualized kinematic in viewer, judged "retarget looks good imo" → proceeding to RL without further retargeting fixes.**

**Single-machine RL bring-up (steps F + G from Runbook).**
- **Env gaps discovered**: the conda `dexmachina` env was created from `dexmachina.yaml` at some point but had drifted. Missing/broken on this machine:
  - `setuptools` was 82.0.1; wandb 0.12.21 imports `pkg_resources` which was removed in `setuptools ≥ 81`. Fixed: `pip install "setuptools<81"`.
  - `gymnasium`, `ray`, `tensorboardx` missing (all listed in `dexmachina.yaml`). Fixed: `pip install gymnasium ray tensorboardx`.
  - Clean fix would be `conda env update -f dexmachina.yaml --prune` but we patched in place to keep moving.
- **Smoke test (50 epochs, B=2048, wandb off)** — clean. Reward 110 at ep 50, no NaNs, ~16K env-steps/sec. Confirmed env builds, retargeted + contact data load correctly, collision_groups applied. Used example-script default flags (`-imi 0.3 -bc 0.3 -con 3 --lower_ratios 0.8 0.8 1`) — not paper-matching.
- **Run A (500 ep, wandb on, B=2048, example defaults)** — launched, validated wandb path streams to `nvidia-isaac/v2d-dexmachina-sharpa-repro`. Killed early once paper-matched config was ready since A was effectively the Inspire recipe, not the f422 recipe we want for Sharpa.
- **Run B (500 ep, wandb on, B=4096, paper-matched `f422-low5-th0`)** — completed. wandb: `https://wandb.ai/nvidia-isaac/v2d-dexmachina-sharpa-repro/runs/gdncgvn9`.
  - **Hyperparams set**: `--lower_ratios 0.5 0.8 1`, `-imi 0.2`, `-con 2`, `-bc 0`, `--curr_rew_thres 0.6 0.01 0 0.01` (third arg is `rew_thresholds.imi=0`), `--hybrid_scales 0.1 1.0`, `-am hybrid`, `--actuate_object`. Only known deviation from f422: `episode_length=200` (clip-derived from box-30-230; paper fixes at 300 — would require a code patch in `constructors.py:88` since `--episode_length` is not a CLI flag, `ep_len = end - start` is hard-coded).
  - **Reward**: 110 (ep50) → 114 (ep100) → 123 (ep200) → 121 (ep300) → 124 (ep400) → **125.24 (ep500)**. Trends up modestly with plateau-ish behaviour.
  - **Episode lengths**: 197.9 / 200 — policy almost never triggers early termination; tracking is solid.
  - **Throughput**: 27,900 step_fps at B=4096 (vs 16K at B=2048). 41-min wall-clock for 500 epochs → ~7 hrs projected for 5000 epochs.
  - Verified earlier 4096-OOM memory note doesn't apply here; that was IsaacLab/SONIC. dexmachina+Genesis with B=4096 uses ~20 GB of 48 GB on RTX 6000 Ada.

**OSMO sweep preparation (step H).**
- Wrote `workflow/Dockerfile`, `workflow/train.yaml`, `workflow/submit_sweep.sh`, `.dockerignore`. Mirrors the k-wbp workflow template structure.
- Dockerfile multi-stage: pytorch:2.5.1-cuda12.1 base → install Genesis@e9df2d8 + rl_games@2c1a771 (MandiZhao forks) → install dexmachina runtime deps → copy dexmachina source + assets. ~1 GB of repo content baked in (Sharpa retargeted .pt, contact_retarget .npy, ARCTIC objects + processed sources, hand URDF/meshes).
- `submit_sweep.sh` loops `7 paper clips × 5 seeds = 35` jobs. Dry-run verified.
- **Pending decisions before image build + submission**: registry tag, wandb key, NFS output path, pool (H100 vs L40s), `max_epochs` (5000 paper-nominal vs 2000 fast sanity).

**State at end of session.**
- Sharpa fully data-ready, gains tuned, collision_groups populated, paper-matched RL recipe validated locally on 500 epochs.
- OSMO Pattern-1 multi-task workflow built + image pushed + sweep submitted.

**OSMO sweep submissions.**
- `sharpa-f422-sweep-2` (image `:v1`) — all 35 tasks failed during import: `trimesh` missing in the image. Image had transitive coverage of most deps but not `trimesh`, `mujoco`, `pyvista`, `coacd`, `gym==0.23.1`, `pandas`. Failed workflow completed within ~minutes.
- `sharpa-f422-sweep-3` (image `:v2`, digest `sha256:19e4487f23...`) — re-submitted with broader dep coverage in the Dockerfile. **Running cleanly.**
- Overview: https://us-west-2-aws.osmo.nvidia.com/workflows/sharpa-f422-sweep-3
- Wandb runs (35): https://wandb.ai/nvidia-isaac/v2d-dexmachina-sharpa-repro
- Pool: `groot-l40-01` (349 free GPUs of 480 at submit time).
- Topology: Pattern 1, single workflow, 35 parallel tasks (7 clips × 5 seeds).
- Per-task resources: 1 GPU, 15 CPU (pool max for 1/8 of an 8-GPU L40 node), 64 Gi memory, 100 Gi storage.
- **Measured throughput** (from task `box30-230-s01-u01-seed24` shortly after start): `fps step: ~23,000` at B=4096, `~6 s/epoch` on L40. Comparable to the local RTX 6000 Ada validation (27K fps), despite L40 being a smaller card.
- **Wall-clock projection**: ~8.3 hrs per task at `max_epochs=5000`. All 35 run in parallel → whole sweep finishes in ~8.3 hrs total. Should complete overnight.

**Docker build history (9 rounds, finally green at `:v2`).** The conda `dexmachina` env had drifted; rebuilding from scratch surfaced these layered issues in sequence:
1. `pytorch/pytorch:2.5.1-cuda12.1-cudnn9-devel` ships Python 3.11; rl_games requires `<3.11` → downgrade conda's python to 3.10.
2. `numpy 2.x` (pulled by transitive deps) breaks Genesis's `tetgen` Cython extension → pin `numpy<2`.
3. `setuptools >= 81` removes `pkg_resources` which wandb 0.12.21 imports → pin `setuptools<81`.
4. Final `pip install -e dexmachina` re-upgrades numpy/setuptools → final-layer `pip install --force-reinstall` with all critical pins.
5. `--force-reinstall` knocks out side-deps; bundle wandb/gymnasium/ray/tensorboardx/scikit-learn/seaborn alongside numpy/setuptools in that final layer.
6. `seaborn` is a top-level dexmachina dep (used by `envs/contacts.py`) but wasn't a transitive of anything we installed explicitly.
7. `:v1` ran the imports in a smoke test on the build host but failed cluster-side on `trimesh` (used by `envs/object.py:sample_mesh_vertices` only when an articulated object is loaded — not exercised by the import-only smoke test). Followed by missing `mujoco`, `pyvista`, `coacd`, `pandas`, `gym==0.23.1` once we widened the local sanity check.
8. Final image `:v2` bundles all of `trimesh/mujoco/pyvista/coacd/pandas/gym` in the runtime-deps layer alongside the previously-discovered pins.

Lesson: smoke-test image with the *actual train script entrypoint*, not just import statements, to surface lazy / conditional imports. The `Dockerfile` and `workflow/generate_sweep.py` now default to `:v2`.

**Outstanding work.**
- Watch the sweep progress; intervene if any tasks fail.
- Eval + Figure-3 column extension (step I).

## Runbook — key commands

Canonical commands for each pipeline step. Update with any flag changes or new steps.

### A. Collision-group gather
```bash
cd dexmachina-sharpa/dexmachina
python hand_proc/inspect_raw_urdf.py --gather_geoms --num_envs 1 \
    --urdf_path assets/sharpa_hand/<side>_sharpa_wave_6dof.urdf \
    --base_link_name <side>_hand_C_MC
# At the (Pdb) prompt: `q` to exit. Copy the printed dict into hand_cfgs/sharpa.py.
```

### B. Auto-tune gains (3-phase per joint group, headless)
```bash
cd dexmachina-sharpa/dexmachina
mkdir -p logs
python hand_proc/auto_tune_gains.py --hand sharpa --clip box-0-230-s01-u01 \
    2>&1 | tee logs/auto_tune_sharpa.log
# Paste-ready cfg block at end of stdout. Paste into _ACTUATORS in sharpa.py.
```

### C. Visualize gains on full trajectory
```bash
cd dexmachina-sharpa/dexmachina
python hand_proc/tune_gains.py --hand sharpa --clip box-0-230-s01-u01 \
    --joint_group wrist_trans --spacing 0.5 -v \
    --num_iters 1 --kp 261.1 261.1 --kv 11.2 11.2 --force_range 50 50
```

### D. Re-retarget all 6 source demos with current gains
```bash
cd dexmachina-sharpa/dexmachina
for clip in \
    box-0-230-s01-u01 \
    ketchup-0-130-s01-u01 \
    ketchup-0-340-s01-u02 \
    mixer-0-340-s01-u01 \
    waffleiron-0-340-s01-u01 \
    notebook-0-340-s02-u02 ; do
    python retargeting/parallel_retarget.py \
        --clip $clip --hand sharpa \
        --control_steps 2000 --save_name para --save -ow
done 2>&1 | tee logs/sharpa_reretarget.log
```

### E. Re-run contact retargeting
```bash
cd dexmachina-sharpa/dexmachina
for clip in \
    box-0-230-s01-u01 \
    ketchup-0-130-s01-u01 \
    ketchup-0-340-s01-u02 \
    mixer-0-340-s01-u01 \
    waffleiron-0-340-s01-u01 \
    notebook-0-340-s02-u02 ; do
    obj=$(echo $clip | cut -d- -f1)
    subject=$(echo $clip | cut -d- -f4)
    use=$(echo $clip | cut -d- -f5 | tr -d 'u')
    fname=assets/arctic/processed/${subject}/${obj}_use_${use}.npy
    python retargeting/map_contacts.py --hand sharpa_hand --load_fname $fname
done 2>&1 | tee -a logs/sharpa_reretarget.log
# Gotchas:
# - map_contacts.py wants the ARCTIC SOURCE path (assets/arctic/processed/...),
#   NOT the retargeter output. The script internally derives the retargeter_results
#   path by appending `_vector.npy` to the load_fname basename (map_contacts.py:348-351).
# - map_contacts.py needs --hand sharpa_hand (with _hand suffix, unlike parallel_retarget.py).
# - Needs scikit-learn in the env.
```

### F. RL smoke test
```bash
cd dexmachina-sharpa
WANDB_MODE=disabled python dexmachina/rl/train_rl_games.py \
    --hand sharpa_hand --clip box-30-230-s01-u01 \
    -B 2048 -obf -obt --max_epochs 50 --save_freq 50 \
    --actuate_object --retarget_name para --horizon 16 \
    -imw 0.5 --gain_mode all --curr_schedule uniform --wait_epochs 100 \
    --learning_rate 0.0003 --contact_beta 10 \
    --upper_ratios 0.9 0.9 1 --lower_ratios 0.8 0.8 1 \
    --group_collisions --fixed_mode uniform --uniform_mode slow \
    --action_penalty 0.01 --dialback_ep_len 80 --skip_grad --deque_len 30 \
    --task_rew_betas 10 1 5 --use_retarget_contact \
    --aux_reset_thres 0 0 0 --curr_rew_thres 0.6 0.01 0.01 0.01 \
    -am hybrid --hybrid_scales 0.1 1.0 --kp_init 80 --kv_init 5 \
    -imi 0.3 -bc 0.3 -con 3 -ert 0.6 -exp sharpa_smoke \
    2>&1 | tee logs/sharpa_rl_smoke.log
```
- Adapted from `examples/train_rl.sh`. Changes from example: `--hand sharpa_hand`, `--clip box-30-230-s01-u01`, `-B 2048` (4096 OOMs on single RTX 6000 Ada 48GB per prior memory), `--max_epochs 50` (smoke; production is 5000+), `-exp sharpa_smoke`. WANDB_MODE=disabled until we confirm the loop works.
- **Env gotcha**: `train_rl_games.py:5` does `import wandb` unconditionally. wandb 0.12.21 (installed in the conda env) uses `pkg_resources`, which was removed in `setuptools` ≥81. Pin: `pip install "setuptools<81"` to keep the import path working.

### G. Local paper-matched RL run (single-machine validation)
```bash
cd dexmachina-sharpa
WANDB_ENTITY=nvidia-isaac python dexmachina/rl/train_rl_games.py \
    --hand sharpa_hand --clip box-30-230-s01-u01 \
    -B 4096 -obf -obt --max_epochs 500 --save_freq 100 \
    --actuate_object --retarget_name para --horizon 16 \
    -imw 0.5 --gain_mode all --curr_schedule uniform --wait_epochs 100 \
    --learning_rate 0.0003 --contact_beta 10 \
    --upper_ratios 0.9 0.9 1 --lower_ratios 0.5 0.8 1 \
    --group_collisions --fixed_mode uniform --uniform_mode slow \
    --action_penalty 0.01 --dialback_ep_len 80 --skip_grad --deque_len 30 \
    --task_rew_betas 10 1 5 --use_retarget_contact \
    --aux_reset_thres 0 0 0 --curr_rew_thres 0.6 0.01 0 0.01 \
    -am hybrid --hybrid_scales 0.1 1.0 --kp_init 80 --kv_init 5 \
    -imi 0.2 -bc 0 -con 2 -ert 0.6 \
    --wandb_project v2d-dexmachina-sharpa-repro \
    -exp box30-230_f422_B4096 \
    2>&1 | tee logs/sharpa_rl_500ep_f422_B4096.log
```
- Matches paper's f422-low5-th0 set.
- **Important**: `zero_epoch = max(max_epochs - num_zero_epoch, 0)`. With `--num_zero_epoch` defaulting to 1000 and `max_epochs=500`, `zero_epoch=0` → curriculum gains forced to zero from epoch 1. Run validates "policy without virtual object help"; the actual curriculum decay only exercises when `max_epochs >= num_zero_epoch + few-thousand`. Paper trains at `max_epochs=5000` → curriculum runs epochs 0-4000, zero phase 4000-5000.

### H. OSMO sweep — build image + submit
```bash
# 1) Build (~15-30 min). Run from repo root.
cd dexmachina-sharpa
docker build \
    -t nvcr.io/nvstaging/isaac-amr/dexmachina-sharpa:v1 \
    -f workflow/Dockerfile \
    . 2>&1 | tee logs/docker_build_v1.log

# 2) Push to registry.
docker push nvcr.io/nvstaging/isaac-amr/dexmachina-sharpa:v1

# 3) Submit 35-task multi-task sweep (Pattern 1, single workflow) to OSMO.
bash workflow/submit_sweep.sh groot-l40-01 dry   # generate sweep.yaml only
bash workflow/submit_sweep.sh groot-l40-01       # generate + submit
```
- Pool: `groot-l40-01` (~349 GPUs free of 480 at submission time; user preference: not H100).
- Topology: **Pattern 1** (single workflow, 35 independent parallel tasks). `workflow/generate_sweep.py` emits the YAML; `submit_sweep.sh` wraps generate + submit.
- Per-job resources (`workflow/train.yaml`): 1 GPU, 16 CPU, 64 Gi mem, 100 Gi storage.
- Per-job runtime: ~7 hrs at `max_epochs=5000` (extrapolated from local run's ~41 min for 500 epochs at B=4096).
- Wandb logging: project `v2d-dexmachina-sharpa-repro` under entity `nvidia-isaac` (key embedded in train.yaml).
- Output: `/mnt/amlfs-01/home/shalinj/training_outputs/dexmachina-sharpa-repro/<run_name>/` on NFS.

### I. Eval + Figure 3 column — TBD
