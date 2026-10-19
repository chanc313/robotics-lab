# dev 容器：ROS 2、控制与规划

> 本文件在容器里显示为 `/workspace/README.md`（只读挂载），源文件在主机仓库的 `.devcontainer/dev/README.md`，修改请在主机上进行。

## 定位

一个独立、内部闭环的机器人软件开发容器：不依赖 sim 与 policy，自己就能完成 ROS 2 开发、控制闭环、机械臂规划和导航。它目前服务于 G1 项目（见最后一节），也可以单独拿到其他项目中复用。与其他容器只通过数据交互：共享的 `/data`、`/runs` 和网络（ROS 2 / DDS）。

## 镜像内容

| 类别 | 内容 |
|---|---|
| 系统与编译 | Ubuntu 24.04、Clang 20（C++26 / libc++）、CMake、Ninja、GDB |
| ROS 2 | Jazzy（ros-base、开发工具、示例节点）、RViz 2、Fast DDS（UDPv4） |
| 控制 | ros2_control、ros2_controllers |
| 仿真 | MuJoCo 3.12.0，mujoco_ros2_control 及示例 |
| 规划与导航 | MoveIt 2（含 Panda 示例配置）、Nav2 核心（不含依赖 Gazebo 的 nav2_bringup） |
| Python | 系统 Python 3.12（ROS 用）；学习环境 `/opt/learning-venv`（numpy、matplotlib、MuJoCo 3.12.0、Ruff、debugpy、ipykernel） |

## 闭环功能与自检

以下命令在本容器终端运行，每一项都在容器内部形成完整回路：

| 功能 | 回路 | 自检 |
|---|---|---|
| ROS 2 通信 | 发布者 → DDS → 订阅者 | 两个终端分别运行 `ros2 run demo_nodes_cpp talker`、`ros2 run demo_nodes_py listener` |
| 控制闭环 | 控制器 ↔ ros2_control ↔ MuJoCo 物理 | `ros2 launch mujoco_ros2_control_demos 01_basic_robot.launch.py headless:=true`，另开终端 `ros2 control list_controllers`，4 个控制器应为 active |
| 机械臂规划 | 目标 → MoveIt 2 规划 → 轨迹执行 | `ros2 launch moveit_resources_panda_moveit_config demo.launch.py`，在 RViz 中拖动末端标记并 Plan & Execute（需要显示） |
| 导航组件 | 地图服务等 Nav2 生命周期节点 | `ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=<地图.yaml>`，再依次 `ros2 lifecycle set /map_server configure`、`activate` |
| 原生开发 | 编辑 → 构建 → 运行 / 调试 | VS Code 任务 `C++: build (Debug)`、`ROS sandbox: self-check`，以及 `uv run python -m robotics_lab` |

整体安装检查在主机执行 `./scripts/lab check-installation ros`。各学习沙盒的用法见 `docs/TOOLCHAIN.md`。

## 工作区与挂载

| 路径 | 内容 |
|---|---|
| `/workspace/docs` | 项目文档（三个容器共享） |
| `/workspace/src/ros` | 项目的 ROS 2 包（colcon 源码根） |
| `/workspace/cppsrc`、`pythonsrc`、`rossrc` | C++ / Python / ROS 2 学习沙盒 |
| `/workspace/.vscode` | 本容器的 VS Code 设置、任务与调试配置 |
| `/build` | 构建产物（cppsrc、rossrc、ros 各一个子目录） |
| `/data`、`/runs` | 共享的模型数据与运行记录 |
| `/workspace/output` | 主机的整个 `output/`（即 `/build`、`/runs`、`/data` 三个目录），仅在 VS Code 窗口中挂载，方便在资源管理器里浏览 |
| `/opt/ruff` | 共享 Ruff 规则（只读） |

只往上述挂载目录写文件；直接写在 `/workspace` 根目录或 `/workspace/src/` 下的内容只留在容器内部，重建即丢失。容器里没有 `.git`，Git 在主机上操作。

## 组成文件（单独复用时需要带走）

- `docker/Dockerfile.dev`、`docker/ros_entrypoint.sh`、`docker/check_installation.py`
- `compose.yaml` 中的 `dev` 服务及 `x-build-args`、`x-ros-env`；`compose.gui.yaml` 中的 `dev` 部分
- `.devcontainer/dev/`（`devcontainer.json`、`vscode/`、本文件）、`.devcontainer/compose.devcontainer.yaml` 中的 `dev` 部分、`.devcontainer/ruff/`
- `ws/pythonsrc/pyproject.toml` 与 `uv.lock`（学习环境依赖，构建时复制进镜像）
- `scripts/lab` 中的 `ros-shell`、`dev-gui`、`rviz`、`check-installation ros` 入口

## 目前在 G1 项目中的角色

尚未进入 G1 回路。`src/ros` 预留给 ROS 适配层：按路线图先旁路观察 sim 中 Isaac 发布的状态，再让 ROS 进入回路。ros2_control、MoveIt 2、Nav2、MuJoCo 目前服务于个人技术栈的学习。
