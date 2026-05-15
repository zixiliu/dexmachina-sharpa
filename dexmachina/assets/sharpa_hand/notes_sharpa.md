## Notes for Pre-processing Sharpa Hand assets

**Source.** URDFs and meshes copied from `~/Documents/gitlab/video_to_data/robotic_grounding/source/robotic_grounding/robotic_grounding/assets/{urdfs/sharpawave,meshes/sharpa_wave}/` (commit unknown). Five URDF variants:

- `left_sharpa_wave.urdf` / `right_sharpa_wave.urdf` — full-mesh single-hand.
- `left_sharpa_wave_primitive.urdf` / `right_sharpa_wave_primitive.urdf` — capsule-collision variants (lighter solver).
- `dual_sharpa_wave.urdf` — bimanual single-file.

Mesh paths were rewritten from `../meshes/sharpa_wave/...` to `meshes/sharpa_wave/...` so the URDFs are self-contained under this directory (matches schunk/xhand convention).

**Joint inventory.** 32 joints, **no mimic joints** (simpler than Inspire). Root link is `<side>_hand_C_MC` (the wrist body).

**Wrist DOFs.** The raw URDFs ship with no base translation/rotation joints — they are the equivalent of dexmachina's `*_xyz_copy.urdf` / `inspire_hand/right01091.urdf` form, not the `*_6dof.urdf` form. Run `dexmachina/hand_proc/add_wrist_dof.py` to produce `*_6dof.urdf` variants.

**Lessons from prior SPIDER integration.** Verify before assuming each transfers to Genesis/DexMachina. See `~/Documents/gitlab/spider/SHARPA_INVESTIGATION.md` and `SHARPA_TABLE1_RESULTS.md` for full context.

- *Wrist body chain.* Original Sharpa MJCF had 5 nested intermediate wrist links. SPIDER had to flatten them so all 6 wrist joints sit on `hand_C_MC` to make IK work. The DexMachina pipeline uses URDF + Genesis (not MJCF + MuJoCo IK), so the impact may differ; if `add_wrist_dof.py` produces the canonical 6 base joints already attached to the root link, no flattening should be needed.
- *Frame alignment.* In the SPIDER MJCF the body quat is `0.5 -0.5 0.5 0.5` so finger axes match MANO's universal palm frame. Equivalent for URDF: rotate the root link's `<inertial>` and child link `<origin>` accordingly, OR set the spawn quat in `inspect_raw_urdf.py` (the `get_base_rotation` lookup function). I'll test with `--iterate_quat` first to find the correct world orientation.
- *Wrist link inertias.* Original `mass="0.001" diaginertia="1e-8 1e-8 1e-8"` was unusably small for MuJoCo. SPIDER bumped to `mass=0.3, diag=0.001`. The raw URDF here actually keeps the original tiny values (`mass="2.5E-03"`, `inertia` ~ `1e-7`) on the finger link `right_thumb_CMC_VL` — verify whether Genesis tolerates this; if not, sed-bump uniformly.
- *Motor stiffness.* The real-Sharpa actuator gains (kp=0.9–13 finger / 50 wrist-pos / 10 wrist-rot) are far weaker than typical sim-hand conventions. SPIDER's MJWP exploded with kp=300/1000. DexMachina's `tune_gains.py` is intended for exactly this calibration step — run it before any sweep.
- *Elastomer geoms.* Sharpa has unique `elastomer.STL` and `elastomer_surface.STL` meshes (compliant fingertip pads). They appear in the collision shapes; `solref="0.06 0.9"` was the SPIDER default and may need tuning for Genesis.

**Next steps in dexmachina pipeline.**
1. `python dexmachina/hand_proc/inspect_raw_urdf.py --urdf_path <path> --iterate_quat --record_video` to find the correct base rotation. Add the result to the `get_base_rotation()` map in `inspect_raw_urdf.py`.
2. `python dexmachina/hand_proc/add_wrist_dof.py ...` to produce 6-DOF wrist variants.
3. `python dexmachina/hand_proc/tune_gains.py ...` to find stable kp/kd for finger and wrist actuators.
4. Author `dexmachina/envs/hand_cfgs/sharpa.py` analogous to `inspire.py`.
5. Run `dexmachina/hand_proc/minimal_retarget.py` per ARCTIC clip to produce retargeted/contact_retarget/retargeter_results outputs.
