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
    etree.SubElement(fixed_joint, "origin", xyz="0 0 0", rpy="0 0 0")

    robot.insert(0, base_link)
    robot.insert(1, fixed_joint)
    tree.write(dst, pretty_print=True, xml_declaration=True, encoding="utf-8")
    return dst


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
        print(f"[{side}] {out_path}")
        print(f"        added joints: {new_joints}")


if __name__ == "__main__":
    main()
