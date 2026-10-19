# sim 容器：Isaac 仿真与强化学习

> 本文件在容器里显示为 `/workspace/README.md`（只读挂载），源文件在主机仓库的 `.devcontainer/sim/README.md`，修改请在主机上进行。

## 定位

一个独立、内部闭环的仿真与强化学习容器：不依赖 dev 与 policy，自己就能搭建场景、训练强化学习策略、运行和评估任务。它目前服务于 G1 项目（见最后一节），也可以单独拿到其他项目中复用。与其他容器只通过数据交互：共享的 `/data`、`/runs` 和网络端点（例如连接 policy 的推理服务、通过 Isaac 自带的桥接与 ROS 2 通信）。

## 镜像内容

| 类别 | 内容 |
|---|---|
| 仿真 | Isaac Sim 6.0.1（PhysX、RTX 渲染、Kit GUI） |
| 环境框架 | Isaac Lab、Isaac Lab-Arena 0.3.0（固定提交 `8737b4c`，按上游锁文件安装） |
| 强化学习 | RSL-RL，PyTorch 2.11 + CUDA 12.8 |
| Python | 3.12.15，环境在 `/opt/arena/.venv`；上游源码在 `/opt/arena` |
| ROS 2 | Isaac 自带的 Jazzy 桥接库（Fast DDS 与 Cyclone DDS） |
| 镜像结构 | 安装结果均分为 16 个镜像层，便于推送到 GHCR |

运行前需要本人接受 Isaac Sim 许可，并在主机 `.env` 中设置 `OMNI_KIT_ACCEPT_EULA=YES`、`ACCEPT_EULA=Y`。

## 闭环功能与自检

以下入口在主机执行（`scripts/lab` 会启动本容器）；在 VS Code 的 sim 窗口里，也可以直接在终端运行对应的 `python` 命令：

| 功能 | 回路 | 自检 |
|---|---|---|
| 仿真与渲染 | 场景 → 物理步进 → 渲染 | `./scripts/lab tutorial basic`；无窗口检查 `./scripts/lab check-installation sim`，带窗口加 `--gui` |
| 交互场景 | 零动作 → 物理 → 环境重置 | `./scripts/lab sim-gui`（Arena `cube_goal_pose`，可拖动物体） |
| 强化学习训练 | 环境 ↔ 策略 ↔ 训练更新 | `./scripts/lab train`（Cartpole，32 个环境、2 次迭代），日志在 `/runs/rl/logs/` |
| 任务评估 | 策略 → 环境 → 任务判定 → 指标与报告 | `./scripts/lab evaluate`（零策略，一个 episode），报告写入 `/runs` |
| 数据 | 示范扩增、格式转换 | Isaac Lab Mimic 数据生成，`isaaclab_arena_gr00t/lerobot/convert_hdf5_to_lerobot.py` 转为 LeRobot 格式 |

带 GPU 渲染的运行占用显存较多；首次运行会从 NVIDIA 资产库下载场景模型，耗时较长。

## 工作区与挂载

| 路径 | 内容 |
|---|---|
| `/workspace/docs` | 项目文档（三个容器共享） |
| `/workspace/src/simulation` | 项目的仿真模块：任务、环境、仿真适配 |
| `/workspace/experiments` | 实验组合配置（与 policy 共享） |
| `/workspace/.vscode` | 本容器的 VS Code 设置与调试配置 |
| `/data`、`/runs` | 共享的模型数据与运行记录 |
| `/workspace/output/storage`、`/workspace/output/runs` | 同上两个目录，仅在 VS Code 窗口中挂载，方便在资源管理器里浏览 |
| `/opt/ruff` | 共享 Ruff 规则（只读） |

Kit 的缓存、配置与日志保存在命名卷中，重建容器不会丢失。只往挂载目录写文件；容器里没有 `.git`，Git 在主机上操作。

## 组成文件（单独复用时需要带走）

- `docker/Dockerfile.sim`、`docker/sim_entrypoint.sh`、`docker/fetch_arena.sh`、`docker/split_layers.py`、`docker/versions.env`、`docker/check_installation.py`
- `compose.yaml` 中的 `sim` 服务、相关命名卷及 `x-build-args`、`x-ros-env`；`compose.gui.yaml` 中的 `sim` 部分
- `.devcontainer/sim/`（`devcontainer.json`、`vscode/`、本文件）、`.devcontainer/compose.devcontainer.yaml` 中的 `sim` 部分、`.devcontainer/ruff/`
- `scripts/lab` 中的 `sim`、`sim-gui`、`tutorial`、`evaluate`、`train`、`check-installation sim` 入口

## 目前在 G1 项目中的角色

运行 Isaac Lab-Arena 的 G1 移动操作任务：Galileo 仓库场景、G1 机器人与全身控制器（WBC）、"放进箱子"的判定。作为 GR00T 推理服务的客户端，通过 `127.0.0.1:5555` 向 policy 容器请求动作块，执行闭环评估（`./scripts/lab g1-evaluate`），结果写入 `/runs/arena-g1/`。
