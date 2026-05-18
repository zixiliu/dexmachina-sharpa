"""Sharpa-specific URDF prep: scaffold a fixed root joint, then add 6 forearm DOFs.

Sharpa's raw URDFs (`left_sharpa_wave.urdf` / `right_sharpa_wave.urdf`) place the wrist
body (`<side>_hand_C_MC`) as the topmost link with no parent fixed joint. The shared
`add_wrist_dof.add_forearm_dof` helper asserts the first joint is `type="fixed"` (the
convention used by Inspire / Schunk / XHand / Allegro / Dex3 / DexRobot raw URDFs).

This one-shot script:
1. Reads `<side>_sharpa_wave.urdf`.
2. Prepends a `<side>_base` link plus a fixed `<side>` -> `<side>_hand_C_MC` joint.
3. Writes `<side>_sharpa_wave_scaffold.urdf` (intermediate, kept for inspection).
4. Runs `add_forearm_dof` to produce `<side>_sharpa_wave_6dof.urdf`.

Run from the repo root (or any cwd):

    python -m dexmachina.hand_proc.prep_sharpa
"""

import os

from lxml import etree

from dexmachina.hand_proc.add_wrist_dof import add_forearm_dof

ASSETS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sharpa_hand")
PARSER = etree.XMLParser(remove_comments=True, remove_blank_text=True)


def _scaffold(side: str) -> str:
    src = os.path.join(ASSETS, f"{side}_sharpa_wave.urdf")
    dst = os.path.join(ASSETS, f"{side}_sharpa_wave_scaffold.urdf")
    tree = etree.parse(src, parser=PARSER)
    robot = tree.getroot()

    base_link_name = f"{side}_root"
    base_link = etree.Element("link", name=base_link_name)
    inertial = etree.SubElement(base_link, "inertial")
    etree.SubElement(inertial, "origin", xyz="0 0 0", rpy="0 0 0")
    etree.SubElement(inertial, "mass", value="0.01")
    etree.SubElement(
        inertial, "inertia", ixx="1e-4", ixy="0", ixz="0", iyy="1e-4", iyz="0", izz="1e-4"
    )

    fixed_joint = etree.Element("joint", name="fixed", type="fixed")
    etree.SubElement(fixed_joint, "parent", link=base_link_name)
    etree.SubElement(fixed_joint, "child", link=f"{side}_hand_C_MC")
    # Scaffold-level fixed joint stays identity. The 180° Z rotation for the
    # right side is applied AFTER the forearm chain by `_rotate_right_wrist_frame`
    # — keeping the forearm translation axes world-aligned. Applying the rotation
    # here flipped the prismatic axes for the right side and confused
    # dex_retargeting's local optimizer (both hands ended up on +X).
    etree.SubElement(fixed_joint, "origin", xyz="0 0 0", rpy="0 0 0")

    robot.insert(0, base_link)
    robot.insert(1, fixed_joint)
    tree.write(dst, pretty_print=True, xml_declaration=True, encoding="utf-8")
    return dst


def _rotate_right_wrist_frame(urdf_path: str, rotation_rpy: str = "0 0 3.14159265") -> None:
    """Insert an intermediate `R_wrist_pre_link` between the yaw joint and
    `right_hand_C_MC`, with a fixed-rotation joint carrying the body-frame
    correction. This keeps the 6 forearm tx/ty/tz/roll/pitch/yaw joints
    world-axis-aligned (so dex_retargeting's optimizer sees a normal
    Cartesian chain) while still rotating the wrist body frame to match
    left-hand convention.
    """
    tree = etree.parse(urdf_path, parser=PARSER)
    robot = tree.getroot()
    # Re-target the existing yaw joint's child to the new intermediate link.
    for joint in robot.findall("joint"):
        if joint.get("name") == "R_forearm_yaw_link_joint":
            joint.find("child").set("link", "R_wrist_pre_link")
            break
    else:
        raise RuntimeError("R_forearm_yaw_link_joint not found in right 6dof URDF")

    pre_link = etree.Element("link", name="R_wrist_pre_link")
    inertial = etree.SubElement(pre_link, "inertial")
    etree.SubElement(inertial, "origin", xyz="0 0 0", rpy="0 0 0")
    etree.SubElement(inertial, "mass", value="0.001")
    etree.SubElement(
        inertial, "inertia", ixx="1e-6", ixy="0", ixz="0", iyy="1e-6", iyz="0", izz="1e-6"
    )
    robot.append(pre_link)

    rot_joint = etree.Element("joint", name="R_wrist_rotation_joint", type="fixed")
    etree.SubElement(rot_joint, "parent", link="R_wrist_pre_link")
    etree.SubElement(rot_joint, "child", link="right_hand_C_MC")
    etree.SubElement(rot_joint, "origin", xyz="0 0 0", rpy=rotation_rpy)
    robot.append(rot_joint)

    tree.write(urdf_path, pretty_print=True, xml_declaration=True, encoding="utf-8")


def main() -> None:
    dof_order = [
        "forearm_yaw",
        "forearm_pitch",
        "forearm_roll",
        "forearm_tz",
        "forearm_ty",
        "forearm_tx",
    ]
    for side in ("left", "right"):
        scaffolded = _scaffold(side)
        out_path = os.path.join(ASSETS, f"{side}_sharpa_wave_6dof.urdf")
        new_joints = add_forearm_dof(
            input_fname=scaffolded,
            output_fname=out_path,
            dof_choices=dof_order,
            base_link_name=f"{side}_hand_C_MC",
            left_hand=(side == "left"),
            skip_side_prefix=False,
        )
        if side == "right":
            _rotate_right_wrist_frame(out_path)
        print(f"[{side}] {out_path}")
        print(f"        added joints: {new_joints}")


if __name__ == "__main__":
    main()
