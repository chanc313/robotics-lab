"""G1 pick-and-place with a fixed third-person camera, for synchronized recording.

The upstream G1 embodiment only carries the head camera. This module adds a static
world camera to the same camera rig, so ``--record_camera_video`` writes both views
frame by frame in simulation time. The policy still reads only the head camera.

Load it with::

    --external_environment_class_path robotics_lab_sim.g1_recording:G1RecordingEnvironment
    g1_locomanip_recording --object brown_box --embodiment g1_wbc_joint_recording
"""

from __future__ import annotations

import numpy as np

import isaaclab.sim as sim_utils
from isaaclab.sensors import CameraCfg
from isaaclab.utils import configclass

from isaaclab_arena.assets.register import register_asset
from isaaclab_arena.embodiments.g1.g1 import G1CameraCfg, G1WBCJointEmbodiment
from isaaclab_arena_environments.galileo_g1_locomanip_pick_and_place_environment import (
    GalileoG1LocomanipPickAndPlaceEnvironment,
)

# Environment-frame look-at for the third-person view, chosen from rendered candidates:
# it sees the shelf, the robot's whole path and the bin table. The robot starts at
# (0, 0.18), the box sits on the shelf at (0.58, 0.18), the bin is at (-0.25, -1.63) and
# the floor is at about z = -0.8. Points further out (e.g. x < -1.3 or y > 1) are
# outside the room walls and render black.
THIRD_PERSON_EYE = (-0.9, 0.7, 1.4)
THIRD_PERSON_TARGET = (0.1, -0.7, -0.3)


def look_at_quat_xyzw(eye: tuple[float, float, float], target: tuple[float, float, float]) -> tuple:
    """Quaternion (x, y, z, w) of a camera at ``eye`` looking at ``target``, in the world
    convention (forward +X, up +Z)."""
    forward = np.asarray(target, dtype=float) - np.asarray(eye, dtype=float)
    forward /= np.linalg.norm(forward)
    left = np.cross([0.0, 0.0, 1.0], forward)
    left /= np.linalg.norm(left)
    up = np.cross(forward, left)
    m = np.stack([forward, left, up], axis=1)
    w = np.sqrt(max(0.0, 1.0 + m[0, 0] + m[1, 1] + m[2, 2])) / 2.0
    x = np.copysign(np.sqrt(max(0.0, 1.0 + m[0, 0] - m[1, 1] - m[2, 2])) / 2.0, m[2, 1] - m[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1.0 - m[0, 0] + m[1, 1] - m[2, 2])) / 2.0, m[0, 2] - m[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1.0 - m[0, 0] - m[1, 1] + m[2, 2])) / 2.0, m[1, 0] - m[0, 1])
    return (float(x), float(y), float(z), float(w))


@configclass
class G1RecordingCameraCfg(G1CameraCfg):
    """Head camera plus a static third-person camera."""

    third_person_cam: CameraCfg = CameraCfg(
        prim_path="{ENV_REGEX_NS}/ThirdPersonCam",
        update_period=0.0,
        height=720,
        width=1280,
        data_types=["rgb"],
        spawn=sim_utils.PinholeCameraCfg(focal_length=14.0, clipping_range=(0.1, 20.0)),
        offset=CameraCfg.OffsetCfg(
            pos=THIRD_PERSON_EYE,
            rot=look_at_quat_xyzw(THIRD_PERSON_EYE, THIRD_PERSON_TARGET),
            convention="world",
        ),
    )


@register_asset
class G1WBCJointRecordingEmbodiment(G1WBCJointEmbodiment):
    """The upstream ``g1_wbc_joint`` embodiment with the recording camera rig."""

    name = "g1_wbc_joint_recording"

    def __init__(self, enable_cameras: bool = False, initial_pose=None, lock_waist: bool = False):
        super().__init__(enable_cameras, initial_pose, lock_waist)
        self.camera_config = G1RecordingCameraCfg()


class G1RecordingEnvironment(GalileoG1LocomanipPickAndPlaceEnvironment):
    """Same scene and task as upstream; registered under its own name so that importing
    this module (via --external_environment_class_path) also registers the embodiment."""

    name: str = "g1_locomanip_recording"
