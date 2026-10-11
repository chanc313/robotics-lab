"""Move directory trees into N bucket trees of similar size.

The sim image installs ~28 GB under /opt. A single RUN makes that one layer, but GHCR
rejects layers over 10 GB and times out uploads after 10 minutes, so Dockerfile.sim
copies each bucket back as its own layer.

Usage: split_layers.py ROOT DEST BUCKETS SOURCE...
Every SOURCE lies under ROOT and is emptied (the directory itself stays). Bucket
DEST/<i> mirrors part of ROOT's tree, so `COPY DEST/<i>/ ROOT/` restores it.
Run it in the same RUN that created the files, so most moves stay cheap renames;
overlayfs refuses to rename directories from earlier layers (EXDEV), and
shutil.move copies those instead.
"""

import os
import shutil
import sys
from pathlib import Path

# Directories above this size are split into their children.
UNIT_LIMIT = 256 * 1024 * 1024


def tree_size(path: Path) -> int:
    if path.is_symlink() or not path.is_dir():
        return path.lstat().st_size
    total = 0
    for root, dirs, files in os.walk(path):
        links = [d for d in dirs if os.path.islink(os.path.join(root, d))]
        for name in files + links:
            total += os.lstat(os.path.join(root, name)).st_size
    return total


def units(path: Path):
    """Yield (path, size) pieces strictly inside `path`, splitting large directories."""
    for child in sorted(path.iterdir()):
        size = tree_size(child)
        if size > UNIT_LIMIT and child.is_dir() and not child.is_symlink():
            yield from units(child)
        else:
            yield child, size


def remove_empty_tree(source: Path) -> None:
    for root, dirs, files in os.walk(source, topdown=False):
        if files:
            raise SystemExit(f"unexpected files left in {root}")
        for name in dirs:
            full = os.path.join(root, name)
            if os.path.islink(full):
                raise SystemExit(f"unexpected symlink left: {full}")
            os.rmdir(full)


def main() -> None:
    root, dest, count = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    sources = [Path(arg) for arg in sys.argv[4:]]
    pieces = [piece for source in sources for piece in units(source)]
    pieces.sort(key=lambda item: (-item[1], str(item[0])))
    loads = [0] * count
    for piece, size in pieces:
        bucket = loads.index(min(loads))
        loads[bucket] += size
        target = dest / str(bucket) / piece.relative_to(root)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(piece, target)
    for bucket, load in enumerate(loads):
        (dest / str(bucket)).mkdir(parents=True, exist_ok=True)
        print(f"bucket {bucket}: {load / 2**30:.2f} GiB", flush=True)
    for source in sources:
        remove_empty_tree(source)


if __name__ == "__main__":
    main()
