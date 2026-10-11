#!/usr/bin/env bash
# Usage: fetch_arena.sh <submodule>...
# Clone the pinned Arena commit plus only the requested, pinned submodules.
set -euo pipefail
source /tmp/versions.env

git init /opt/arena
git -C /opt/arena remote add origin https://github.com/isaac-sim/IsaacLab-Arena.git
git -C /opt/arena fetch --depth 1 origin "$ARENA_COMMIT"
git -C /opt/arena checkout --detach FETCH_HEAD
git -C /opt/arena -c url.https://github.com/.insteadOf=git@github.com: \
    submodule update --init --depth 1 "$@"

test "$(git -C /opt/arena rev-parse HEAD)" = "$ARENA_COMMIT"
for submodule in "$@"; do
    case "$submodule" in
        submodules/IsaacLab) expected=$ISAACLAB_COMMIT ;;
        submodules/Isaac-GR00T) expected=$GR00T_COMMIT ;;
        *) echo "No pinned commit for $submodule" >&2; exit 1 ;;
    esac
    test "$(git -C "/opt/arena/$submodule" rev-parse HEAD)" = "$expected"
done
printf '%s\n' "$ARENA_LOCK_SHA256  /opt/arena/uv.lock" | sha256sum --check -
