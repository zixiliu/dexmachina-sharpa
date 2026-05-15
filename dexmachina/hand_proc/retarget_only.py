"""Run dex_retargeting on one or more ARCTIC clips and save .pt outputs only.

Same retargeting pipeline as `minimal_retarget.py`, but skips the post-save Genesis viewer
loop (which blocks indefinitely). Suitable for batch runs over the 7-clip Figure 3 set.

Usage (from repo `dexmachina/dexmachina/`):

    python -m dexmachina.hand_proc.retarget_only --hand sharpa --clips box-30-230 ketchup-30-130 ...
"""

import argparse
import os
from copy import deepcopy
from os.path import join
from pathlib import Path

import genesis as gs
import numpy as np
import torch
import yaml
from dex_retargeting.retargeting_config import RetargetingConfig

from dexmachina.hand_proc.hand_utils import parse_clip_string
from dexmachina.hand_proc.minimal_retarget import get_entity_info
from dexmachina.retargeting.retarget_utils import compose_retarget_config, retarget_all_steps


def _build_scene(hand_urdfs):
    scene = gs.Scene(
        sim_options=gs.options.SimOptions(dt=1 / 60, substeps=2, gravity=(0, 0, 0)),
        rigid_options=gs.options.RigidOptions(enable_self_collision=False, enable_joint_limit=True),
        show_viewer=False,
        use_visualizer=False,
    )
    scene.add_entity(gs.morphs.URDF(file="urdf/plane/plane.urdf", fixed=True))
    hand_entities = {}
    for side, urdf_path in hand_urdfs.items():
        hand_entities[side] = scene.add_entity(
            gs.morphs.URDF(
                file=urdf_path,
                fixed=True,
                merge_fixed_links=False,
                recompute_inertia=True,
                collision=False,
            ),
            material=gs.materials.Rigid(gravity_compensation=0.8),
        )
    scene.build(n_envs=1, env_spacing=(2.0, 2.0))
    return scene, hand_entities


def _retarget_clip(args, clip, retargeters, urdfs, hand_entities):
    obj_name, start, end, subject_name, use_clip = parse_clip_string(clip)
    save_dir = join(args.save_dir, args.hand_dir)
    os.makedirs(save_dir, exist_ok=True)
    save_fname = join(save_dir, f"{clip}.pt")
    if os.path.exists(save_fname) and not args.overwrite:
        print(f"  [skip] exists: {save_fname}")
        return

    demo_fname = f"assets/arctic/processed/{subject_name}/{obj_name}_use_{use_clip}.npy"
    if not os.path.exists(demo_fname):
        print(f"  [miss] {demo_fname}")
        return
    loaded = np.load(demo_fname, allow_pickle=True).item()
    world_data = loaded["world_coord"]
    retar_data = {}
    for side in ("left", "right"):
        entity = hand_entities[side]
        hand_init_pos, actuated_dof_names, actuated_dof_idxs = get_entity_info(entity)
        dof_limits = entity.get_dofs_limit(actuated_dof_idxs)
        retar_data[side] = retarget_all_steps(
            dof_limits,
            hand_init_pos,
            actuated_dof_names,
            actuated_dof_idxs,
            retargeters[side],
            int(end - start),
            world_data[f"joints.{side}"],
            args.retarget_type,
            frame_start=start,
        )
    torch.save(retar_data, save_fname)
    print(f"  [save] {save_fname}  ({end - start} frames)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hand", type=str, default="sharpa")
    parser.add_argument("--clips", nargs="+", required=True)
    parser.add_argument("--save_dir", type=str, default="hand_proc/retargeted")
    parser.add_argument("--retarget_type", type=str, default="vector")
    parser.add_argument("--overwrite", "-o", action="store_true")
    args = parser.parse_args()

    args.hand_dir = args.hand if ("_hand" in args.hand or args.hand == "xhand") else args.hand + "_hand"
    robot_dir = f"assets/{args.hand_dir}"
    RetargetingConfig.set_default_urdf_dir(robot_dir)
    with Path(join(robot_dir, "retarget_config.yaml")).open("r") as f:
        input_cfg = yaml.safe_load(f)

    retargeters = {}
    urdfs = {}
    for side in ("left", "right"):
        cfg_dict = compose_retarget_config(
            input_cfg[side],
            args.retarget_type,
            input_cfg.get("low_pass_alpha", 1.0),
            input_cfg.get("low_pass_alpha_vel", 1.0),
            ignore_mimic_joint=False,
            add_dummy_free_joint=False,
        )
        retargeters[side] = RetargetingConfig.from_dict(deepcopy(cfg_dict)).build()
        urdfs[side] = join(robot_dir, cfg_dict["urdf_path"])

    gs.init(backend=gs.gpu, logging_level="warning")
    scene, hand_entities = _build_scene(urdfs)
    print(f"Built {args.hand_dir} scene; retargeting {len(args.clips)} clip(s)")
    for clip in args.clips:
        print(f"clip {clip}:")
        _retarget_clip(args, clip, retargeters, urdfs, hand_entities)


if __name__ == "__main__":
    main()
