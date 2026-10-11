#!/usr/bin/env bash
set -euo pipefail

# Isaac's bundled Jazzy bridge libraries are independent of the dev container's ROS.
bridge_lib=/opt/arena/.venv/lib/python3.12/site-packages/isaacsim/exts/isaacsim.ros2.core/jazzy/lib
if [[ -d "$bridge_lib" ]]; then
    export LD_LIBRARY_PATH="$bridge_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
fi
exec "$@"
