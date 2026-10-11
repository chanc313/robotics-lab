"""Check one container's installed frameworks; no communication or training run."""

import argparse
import importlib
import importlib.metadata
import json
import os
import subprocess
import sys
import traceback
from pathlib import Path


def report(key, value):
    print(json.dumps({key: value}, ensure_ascii=False), flush=True)


def gpu_check():
    import torch

    report("torch", torch.__version__)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available in this container")
    report("gpu", torch.cuda.get_device_name(0))
    values = torch.ones((2, 2), device="cuda")
    total = (values @ values).sum().item()
    torch.cuda.synchronize()
    report("cuda_tensor_sum", total)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scope", choices=["ros", "sim", "policy"])
    parser.add_argument("--gui", action="store_true", help="Show the empty Isaac application")
    args = parser.parse_args()
    scope = args.scope
    if args.gui and scope != "sim":
        parser.error("--gui is available only for the sim installation check")
    report("python", sys.version)

    if scope == "ros":
        for module in ("rclpy", "debugpy"):
            report(module, importlib.import_module(module).__file__)
        subprocess.run(["ros2", "pkg", "prefix", "demo_nodes_cpp"], check=True)
        subprocess.run(["ros2", "pkg", "prefix", "rviz2"], check=True)
        subprocess.run(["rosdep", "--version"], check=True)
        for command in (os.environ["CXX"], "cmake", "ninja", "gdb"):
            subprocess.run([command, "--version"], check=True)
        # Learning sandbox: build-time dependencies plus the bind-mounted source via .pth.
        subprocess.run(
            [
                "/opt/learning-venv/bin/python",
                "-c",
                "import robotics_lab, numpy, matplotlib, ruff; print(robotics_lab.__file__)",
            ],
            check=True,
        )
    else:
        for module in ("numpy", "gymnasium", "pandas"):
            loaded = importlib.import_module(module)
            report(module, loaded.__version__)
        gpu_check()
        if scope == "policy":
            import torch
            from flash_attn import flash_attn_func

            for module in ("gr00t.model", "gr00t.policy.gr00t_policy", "deepspeed"):
                report(module, importlib.import_module(module).__file__)
            sample = torch.zeros((1, 16, 2, 64), device="cuda", dtype=torch.float16)
            result = flash_attn_func(sample, sample, sample)
            torch.cuda.synchronize()
            report("flash_attention_shape", list(result.shape))
        else:
            bridge = Path(
                "/opt/arena/.venv/lib/python3.12/site-packages/isaacsim/exts/"
                "isaacsim.ros2.core/jazzy/lib"
            )
            if not (bridge / "librcl.so").is_file():
                raise RuntimeError("Bundled Jazzy core libraries are missing")
            report("isaac_ros_core", str(bridge))
            for package in ("isaacsim", "isaaclab", "isaaclab-arena", "rsl-rl-lib"):
                report(package, importlib.metadata.version(package))
            # Kit must start before importing Isaac modules. No environment or ROS graph.
            from isaacsim import SimulationApp

            app = SimulationApp({"headless": not args.gui})
            try:
                for module in ("isaaclab", "isaaclab_arena", "rsl_rl"):
                    report(module, importlib.import_module(module).__file__)
                client_source = "/opt/arena/submodules/Isaac-GR00T"
                sys.path.insert(0, client_source)
                try:
                    report(
                        "gr00t_client_source",
                        importlib.import_module("gr00t.policy.server_client").__file__,
                    )
                finally:
                    sys.path.remove(client_source)
                for _ in range(5):
                    app.update()
                report("kit_startup", "complete")
            except BaseException:
                # Kit fast shutdown can terminate the process; preserve failures.
                traceback.print_exc()
                app.close(exit_code=1)
                raise
            else:
                report("installation_checks_complete", True)
                app.close()
    report("installation_check", "passed")


if __name__ == "__main__":
    main()
