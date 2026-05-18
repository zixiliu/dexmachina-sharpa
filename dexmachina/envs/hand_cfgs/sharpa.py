"""Sharpa hand cfg for DexMachina.

Five fingers, 22 finger DOFs + 6 forearm DOFs. No mimic joints. Finger anatomy:
  - thumb: CMC_FE, CMC_AA, MCP_FE, MCP_AA, IP            (5 dofs)
  - index/middle/ring: MCP_FE, MCP_AA, PIP, DIP          (4 dofs each, 12 total)
  - pinky: CMC, MCP_FE, MCP_AA, PIP, DIP                  (5 dofs)
  - total: 22 finger + 6 wrist = 28 actuated DOFs

Wrist link is `<side>_hand_C_MC` (palm/wrist body). Outer placeholder is `<side>_root`,
introduced by `dexmachina/hand_proc/prep_sharpa.py` so `add_wrist_dof.py` could attach the
6 forearm joints. Joint limits and gains start as best-guess copies of inspire/schunk;
they get overridden per demo by retargeting and tuned later via `tune_gains.py`.
"""

import os
from os.path import join

from dexmachina.asset_utils import get_urdf_path

sharpa_asset_dir = "sharpa_hand/"
left_rel_urdf = join(sharpa_asset_dir, "left_sharpa_wave_6dof.urdf")
right_rel_urdf = join(sharpa_asset_dir, "right_sharpa_wave_6dof.urdf")

SHARPA_LINK_NAMES = [
    "thumb_fingertip",
    "index_fingertip",
    "middle_fingertip",
    "ring_fingertip",
    "pinky_fingertip",
]

# 6 forearm + 22 finger zeros. Forearm initial guess matches the rough world-pose ranges
# used by inspire (right hand near (-0.35, 0.1, 1.05), left near (0.25, 0.11, 1.0)).
# Real wrist pose comes from demo data once retargeting is wired up.
SHARPA_DEFAULT_QPOS = {
    "left": [0.25, 0.11, 1.00, 0.0, 0.0, 0.0] + [0.0] * 22,
    "right": [-0.35, 0.10, 1.05, 0.0, 0.0, 0.0] + [0.0] * 22,
}

# Forearm joint limits left empty so the env inherits the URDF defaults (±2 m
# translation, ±2π rotation), matching allegro / xhand / schunk. Previously this
# was a verbatim copy of inspire's tight bounds, which had an L/R yaw offset
# tailored to inspire's mirror-symmetric URDF. Sharpa's URDF is not
# mirror-symmetric (right body Z is flipped ~180° about Y), so the inspire offset
# compounded the body-frame mismatch — pinning the right hand's wrist into a 0.6
# rad sector and causing intermittent "stuck wrist" failures in retargeting on
# rotation-heavy moments. Without these overrides the retargeter is free to find
# whatever wrist orientation matches the MANO target.
_LEFT_FOREARM_LIMITS = {}
_RIGHT_FOREARM_LIMITS = {}

# Actuator groups. Finger regex matches anything starting with `<side>_<finger>_`,
# excluding the forearm joints (those use the L_/R_ prefix). kp/kv mirror inspire as
# a reasonable Genesis default; SPIDER's MJWP work suggests Sharpa is sensitive to over-
# stiff actuators on its small finger links — revisit via tune_gains.py once retargeting is
# in place.
_ACTUATORS = {
    "finger": dict(
        joint_exprs=[r"(left|right)_(thumb|index|middle|ring|pinky)_.*"],
        kp=150.0,
        kv=11.2,
        force_range=50.0,
    ),
    "wrist_rot": dict(
        joint_exprs=[r"[LR]_forearm_(roll|pitch|yaw)_link_joint"],
        kp=300.0,
        kv=11.2,
        force_range=50.0,
    ),
    "wrist_trans": dict(
        joint_exprs=[r"[LR]_forearm_t[xyz]_link_joint"],
        kp=261.1,
        kv=11.2,
        force_range=50.0,
    ),
}

SHARPA_LEFT_CFG = {
    "urdf_path": get_urdf_path(left_rel_urdf),
    "wrist_link_name": "left_hand_C_MC",
    # Sharpa has no mimic joints in the URDF.
    "mimic_joint_map": {},
    "kpt_link_names": ["left_" + n for n in SHARPA_LINK_NAMES],
    "joint_limits": _LEFT_FOREARM_LIMITS,
    "default_qpos": SHARPA_DEFAULT_QPOS["left"],
    "actuators": {k: v.copy() for k, v in _ACTUATORS.items()},
    "collision_groups": {
        7: 0,
        13: 1, 23: 1, 28: 1, 33: 1,
        14: 2, 19: 2, 24: 2, 29: 2,
        15: 3, 20: 3, 25: 3, 30: 3,
        16: 4, 21: 4, 26: 4, 31: 4,
        17: 5, 22: 5, 27: 5, 32: 5, 37: 5,
    },
    "collision_palm_name": "left_hand_C_MC",
}

SHARPA_RIGHT_CFG = {
    "urdf_path": get_urdf_path(right_rel_urdf),
    "wrist_link_name": "right_hand_C_MC",
    "mimic_joint_map": {},
    "kpt_link_names": ["right_" + n for n in SHARPA_LINK_NAMES],
    "joint_limits": _RIGHT_FOREARM_LIMITS,
    "default_qpos": SHARPA_DEFAULT_QPOS["right"],
    "actuators": {k: v.copy() for k, v in _ACTUATORS.items()},
    "collision_groups": {
        7: 0,
        13: 1, 23: 1, 28: 1, 33: 1,
        14: 2, 19: 2, 24: 2, 29: 2,
        15: 3, 20: 3, 25: 3, 30: 3,
        16: 4, 21: 4, 26: 4, 31: 4,
        17: 5, 22: 5, 27: 5, 32: 5, 37: 5,
    },
    "collision_palm_name": "right_hand_C_MC",
}

SHARPA_CFGS = dict(left=SHARPA_LEFT_CFG, right=SHARPA_RIGHT_CFG)
