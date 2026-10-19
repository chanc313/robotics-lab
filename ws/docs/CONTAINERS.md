# 容器指南

ROS、Isaac、模型与训练都在容器中运行；主机只负责 Docker、GPU 驱动、显示和文件存储，主机原生的 ROS、Isaac、模型 Python 环境不参与项目。下文的 `./scripts/lab` 命令都在 **Linux 主机终端**、仓库根目录执行，它们启动对应容器并在其中运行程序。

## 三个容器

三个容器相互独立，各自在内部形成闭环：不依赖另外两个，也能单独构建、运行和验证，因此可以分别复用到其他项目。它们之间只通过数据交互：共享的 `/data`（模型、数据集、资产）、`/runs`（日志、checkpoint、报告），以及网络端点（目前只有 sim 与 policy 之间的 GR00T 推理服务）。跨容器的接口还没有设计，见 [路线图](ROADMAP.md) 第 2 步。

每个容器有自己的 README，打开该容器时显示为 `/workspace/README.md`（主机源文件在 `.devcontainer/<容器>/README.md`），内容包括镜像内容、闭环功能与自检命令、挂载约定、单独复用时需要带走的文件，以及目前在 G1 项目中的角色。概览如下：

| 容器 | 闭环功能（纯净骨架） | 目前在 G1 项目中的角色 |
|---|---|---|
| dev | ROS 2 开发与通信、RViz；控制器 ↔ ros2_control ↔ MuJoCo 的控制闭环；MoveIt 2 规划、Nav2 导航；C++26 / Python 原生开发 | 尚未进入回路，`src/ros` 预留给 ROS 适配层 |
| sim | Isaac Sim 物理与渲染、Isaac Lab 环境、RSL-RL 强化学习训练、Arena 任务评估、数据生成与转换 | 运行 G1 移动操作任务，作为推理服务的客户端执行闭环评估 |
| policy | GR00T 推理服务、模型微调与训练、自研模型开发 | 加载官方 G1 微调权重，为 sim 提供动作块 |

每个容器只挂载 `ws/` 中属于自己的目录，具体见 [开发指南](DEVELOPMENT.md#仓库与工作区)。

## 1. 准备与构建

```bash
./scripts/lab prepare
./scripts/lab build             # 或只构建其中一个：./scripts/lab build dev
```

`prepare` 创建 `output/storage/{models,datasets,assets}` 与 `output/runs/rl`，并在 `.env` 不存在时写入当前 UID/GID 和默认 ROS domain，已有 `.env` 不覆盖。这些目录必须由当前用户创建：缺失的绑定目录会被 Docker 以 root 身份自动创建，容器内的 `dev` 用户随后无法写入。

构建配置集中在 `compose.yaml`：

- `x-build-args` 按摘要固定共享基础镜像（uv、Ubuntu 24.04），并传入 `.env` 中的 UID/GID；`policy` 的 CUDA 基础镜像只在 `docker/Dockerfile.policy` 使用，也按摘要固定。三个 Dockerfile 的基础镜像参数没有默认值，需经 compose 构建。
- `docker/versions.env` 固定 Arena / Isaac Lab / GR00T 提交、Arena 锁的 SHA-256 和两个 Python 版本。`sim` 拉取 Isaac Lab 与 GR00T 子模块，`policy` 只拉取 GR00T。
- `sim` 安装的约 28 GB 文件在构建时由 `docker/split_layers.py` 均分为 16 个镜像层。GHCR 拒绝超过 10 GB 的层，单次上传 10 分钟超时，整块一层既推不上去，也难以在超时内传完。上游依赖增长后若单层接近 2 GB，增加 `Dockerfile.sim` 中的分层数。
- 构建期 uv 下载缓存保存在 BuildKit 缓存中，重建时复用；不要随意清理 Docker 构建缓存，否则下一次重建要重新下载数十 GB 依赖。

apt 包未逐个固定版本，因此可以复建，但不保证逐字节相同。

运行 Isaac 前，本人接受 Isaac Sim 许可后，在 `.env` 取消注释：

```dotenv
OMNI_KIT_ACCEPT_EULA=YES
ACCEPT_EULA=Y
```

`prepare` 不会替新使用者接受许可。

### 安装检查

```bash
./scripts/lab check-installation ros
./scripts/lab check-installation sim
./scripts/lab check-installation policy
```

- `ros`：rclpy、debugpy、ROS 示例包、RViz、controller_manager、mujoco_ros2_control、MoveIt 2 的 move_group、Nav2、rosdep、编译工具，以及学习沙盒环境（含 MuJoCo Python 跑一步仿真）；
- `sim`：Python 依赖、CUDA 小算子、Isaac 自带 Jazzy 库、Isaac / Lab / Arena / RSL-RL 版本、GR00T 客户端源码导入，以及无界面空 Kit 启动；
- `policy`：Python 依赖、CUDA 小算子、GR00T 与 DeepSpeed 导入、FlashAttention 小算子。

检查不创建 ROS 通信图、训练环境或模型服务，也不下载权重。GUI 版本的 `sim` 检查：`./scripts/lab check-installation sim --gui`，空窗口自动退出。检查脚本 `docker/check_installation.py` 属于环境工具，只在检查时临时挂进容器。`sim` 的 `uv pip check` 仍报告 coverage、websockets 两项上游元数据差异（见 [迁移记录](archive/CONTAINER_MIGRATION_2026-10-11.md)），安装检查通过不代表上游元数据完全一致。

## 2. IDE

在 VS Code 执行 **Dev Containers: Reopen in Container**（已有容器时用 **Rebuild Container**），选择配置：

| 配置 | 用途 | 默认解释器 |
|---|---|---|
| Robotics lab dev | ROS、RViz、C++、学习沙盒 | `/opt/learning-venv/bin/python` |
| Robotics lab sim | Isaac 任务开发、调试与 RL | `/opt/arena/.venv/bin/python` |
| Robotics lab policy | GR00T 与模型代码 | `/opt/policy-venv/bin/python` |

- 三个配置分别在 `.devcontainer/dev|sim|policy/`，打开时选择其一。打开前都在主机执行 `./scripts/lab prepare`，三者共用 `.devcontainer/compose.devcontainer.yaml`：它为每个容器挂载各自的 VS Code 配置（`.devcontainer/<容器>/vscode/` → `/workspace/.vscode`）和 README，并把该容器用到的 `output/` 子目录同时挂到 `/workspace/output/`，让资源管理器能看到运行产物（dev 是整个 `output/`，sim 与 policy 是 `runs/`、`storage/`）；并把 VS Code 生成临时 Dockerfile 的目录 `${TMPDIR:-/tmp}/devcontainercli-${USER}/container-features` 声明为附加构建上下文，绕开 [Compose / Buildx 读取外部 Dockerfile 的问题](https://github.com/docker/compose/pull/14286)。该目录不会进入镜像，`scripts/lab build` 也不加载这个文件。
- 日常只需要 dev 窗口：ROS、C++、学习沙盒和文档都在这里。编辑或调试依赖 Isaac、GR00T 的代码时再另开窗口（**File: New Window** → **Dev Containers: Open Folder in Container...** → 选择仓库根目录与 sim 或 policy 配置），以获得对应环境的补全和断点调试；只运行仿真、训练或推理服务时不必开窗口，直接在主机执行 `./scripts/lab` 入口。各窗口只看到本容器挂载的目录，共同挂载的 `docs/`、`experiments/` 在任何一处修改都会立即同步。容器里没有 `.git`，提交、推送在主机上进行。三个配置都设置 `shutdownAction: "none"`，关闭窗口后容器继续空转（只占少量内存，不占 GPU），不用时可在主机执行 `docker compose --profile sim --profile policy stop sim policy` 停止。
- 每个容器只装自己的依赖，Pylance 因此只诊断已打开的文件：依赖缺失的提示只出现在你打开的文件上。所有服务使用主机网络，端口本来就在主机上，三个配置都关闭了 VS Code 的自动端口转发。
- sim、policy 镜像没有系统 Python，只有镜像内固定的解释器。VS Code 的 Python Environments 扩展可能弹出“No Python found… install Python using uv”，选 **Don't ask again** 即可，不要让它在运行时安装解释器。
- `dev` 的 `python3` 是带 ROS 依赖的系统 Python，ROS 节点直接用它运行；学习沙盒环境不在 `PATH` 中，终端也不自动激活，见 [学习沙盒工具链](TOOLCHAIN.md)。Pylance 额外加载 ROS 的 Python 包路径。
- 各容器的 `launch.json` 只包含本容器的调试配置：dev 有 C++、学习沙盒与 ROS 节点，sim 有 Isaac 当前文件，policy 有 GR00T 当前文件。Ruff 规则在 `.devcontainer/ruff/ruff.toml`，只读挂载为 `/opt/ruff/ruff.toml`，编辑器通过 `ruff.configuration` 读取，命令行用 `ruff check --config /opt/ruff/ruff.toml`；Ruff 缓存写在容器内部，不回到主机。
- `dev`、`sim` 配置都加载 GUI 叠加文件（显示与 GPU），在容器终端里可以直接打开 RViz、MuJoCo、Isaac 窗口；这要求 VS Code 进程拿到当前的 `DISPLAY`、`XAUTHORITY` 并能读取会话 cookie，必要时从 Linux 桌面终端启动 VS Code。不用 IDE 时，主机上的 `./scripts/lab dev-gui`、`./scripts/lab rviz`、`./scripts/lab sim-gui` 提供同样的窗口。
- IDE 打开容器时可能触发镜像构建；Docker Compose 需 ≥ 2.30 以支持 [`gpus` 配置](https://docs.docker.com/reference/compose-file/services/#gpus)。

## 3. 启动与停止

```bash
./scripts/lab sim-gui                 # 持续保留 Arena 场景窗口
./scripts/lab tutorial basic          # Isaac 入门方块教程
./scripts/lab tutorial ik             # Franka IK 教程
./scripts/lab evaluate                # 一次零策略 episode，评估结束后 GUI 关闭
./scripts/lab rviz                    # RViz
./scripts/lab sim                     # sim 容器 shell，或在后面接任意命令
./scripts/lab ros-shell               # dev 容器 shell
```

自定义 GUI 评估与无界面评估：

```bash
./scripts/lab evaluate --viz kit --device cpu --policy_type zero_action \
  --num_episodes 1 --output_base_dir /runs/my-experiment cube_goal_pose

./scripts/lab sim python isaaclab_arena/evaluation/policy_runner.py \
  --headless --device cpu --policy_type zero_action --num_steps 20 \
  --output_base_dir /runs/headless-check cube_goal_pose
```

这些命令在前台运行，Ctrl+C 停止，关闭 Kit 窗口也会结束 GUI 程序。`--rm` 容器退出后即删除，绑定目录与命名卷保留。需要保留日志时追加 `2>&1 | tee output/runs/<名称>.log`。不要用 `docker compose down -v` 停止日常工作，它会删除项目的命名卷。开发容器不挂载 Docker socket。

## 4. ROS 与跨容器通信

在 `dev` 的两个终端分别运行 `ros2 run demo_nodes_cpp talker` 和 `ros2 run demo_nodes_py listener`，看到 `I heard` 即通信正常。交互式 Bash 自动加载 `/opt/ros/jazzy/setup.bash`，入口脚本也会加载；`docker compose exec` 的非交互命令需显式加载：

```bash
docker compose exec dev bash -c 'source /opt/ros/jazzy/setup.bash && ros2 pkg prefix demo_nodes_cpp'
```

- 所有服务使用主机网络，默认 `ROS_DOMAIN_ID=0`，Fast DDS 只用 UDPv4。
- ROS 变量在 `compose.yaml` 的 `x-ros-env` 中统一定义，`dev` 与 `sim` 共用；`ROS_DOMAIN_ID`、`RMW_IMPLEMENTATION`、`FASTDDS_BUILTIN_TRANSPORTS` 可在 `.env` 覆盖。Isaac 自带 Fast DDS 与 Cyclone DDS 两种 RMW，`dev` 目前只装 Fast DDS，改用 Cyclone DDS 前需在 `docker/Dockerfile.dev` 加 `ros-jazzy-rmw-cyclonedds-cpp`。
- `sim` 使用 Isaac 自带的 Jazzy bridge 库，不安装 ROS apt 包，也不加载 `dev` 的 `/opt/ros`。桥接双方需要匹配 domain、消息类型与 QoS。

项目的 ROS 包放在 `src/ros`，构建产物放 `/build/ros`（主机 `output/build/ros`），不在 `/workspace` 根目录运行 colcon（最小收发示例见学习沙盒 `rossrc/`，[学习沙盒工具链](TOOLCHAIN.md#ros-2rossrc)）：

```bash
rosdep update
colcon --log-base /build/ros/log build \
  --base-paths src/ros \
  --build-base /build/ros/build \
  --install-base /build/ros/install
source /build/ros/install/setup.bash
```

镜像已初始化 rosdep 系统源，`rosdep update` 只更新个人索引。新增系统依赖写入 `docker/Dockerfile.dev` 与包的 `package.xml` 后重建镜像。

## 5. RL 训练与模型服务

`sim` 按 Arena 锁文件提供 Gymnasium、pandas、PyTorch / CUDA 与 RSL-RL。默认训练入口是 32 个 Cartpole 环境、2 次迭代，用于确认链路；自定义参数会替换默认参数：

```bash
./scripts/lab train
./scripts/lab train --task Isaac-Cartpole-v0 --num_envs 128 \
  --max_iterations 100 --headless --viz none physics=physx
```

训练工作目录是 `/runs/rl`，上游写入相对路径 `logs/`，因此结果在主机 `output/runs/rl/logs/`。正式实验需固定任务、种子、训练参数与模型版本。

`policy` 使用 GR00T 要求的 Python 3.10 与独立的 Torch / CUDA。模型开发用 `./scripts/lab policy-shell`；微调入口 `./scripts/lab policy-train` 无参数时只显示官方帮助，默认产物目录 `/runs/gr00t/train`。权重与数据集不进入镜像，需要时在 `policy` shell 中下载官方固定 revision：

```bash
hf download nvidia/GN1x-Tuned-Arena-G1-Loco-Manipulation \
  --revision gn1_6 --local-dir /data/models/arena-g1/checkpoint-20000
```

这是上游的官方命令，会下载整个仓库（约 50 GB），其中约 44 GB 是续训用的优化器与 DeepSpeed 状态。只做推理时可以加 `--exclude "global_step*/*" optimizer.pt scheduler.pt "rng_state_*.pth" training_args.bin`，只下载约 6.6 GB；之后需要续训时再执行官方命令补齐。

然后在两个主机终端分别运行：

```bash
./scripts/lab policy-server
```

```bash
./scripts/lab policy-ping
./scripts/lab g1-evaluate
```

默认模型路径 `/data/models/arena-g1/checkpoint-20000`，embodiment `NEW_EMBODIMENT`，端点 `127.0.0.1:5555`，可用 `POLICY_MODEL_PATH`、`POLICY_PORT` 覆盖（默认值在 `experiments/arena_g1/experiment.env`）。不要把身份未确认的已有服务当作兼容服务。G1 评估保留 CPU 物理、官方配置与 `g1_wbc_joint`，与上游说明一致。

`g1-evaluate` 打开 Kit 窗口运行一个 episode。不需要窗口时，在 `sim` 中运行同一条 `policy_runner.py` 命令并把 `--viz kit` 换成 `--headless`。

本机（RTX 4080 Laptop 12 GB、30 GB 内存）2026-10-13 的实测：GR00T 服务约 30 秒就绪、占显存约 6.2 GB；无界面评估时整机显存峰值约 10.7 GB、内存峰值约 20 GB，一个 episode（最长 1500 步、30 秒仿真时间）墙钟约 12 分钟，首次运行还要从 NVIDIA 资产库下载场景模型。`--record_viewport_video` 会把整段画面留在内存里，录满 1500 步的 episode 时进程涨到约 18 GB 并被系统 OOM 杀掉，在本机录像只适合短运行。

仿真与模型共享本机约 12 GB 显存；需要时把 `policy` 放到远程 GPU，评估端用 `--remote_host`、`--remote_port` 指向它。`sim`、`policy` 使用 `ipc: host`，满足 dataloader 与分布式训练的共享内存需求。

## 6. 数据、缓存与身份

- `/workspace` 只包含本容器挂载的 `ws/` 子目录；`output/storage` 为 `/data`，`output/runs` 为 `/runs`，三个容器路径一致；dev 另有 `/build`（主机 `output/build`）。脚本和命令一律使用这些短路径；VS Code 窗口里的 `/workspace/output/` 只是同一批目录的浏览入口。容器退出后结果仍在主机的 `output/` 中，可直接查看。
- `dev` 没有命名卷：学习沙盒依赖在镜像内，C++ 与 ROS 的构建产物都在 `/build` 下（`cppsrc`、`rossrc`、`ros` 各一个子目录）。
- `sim`、`policy` 各有缓存卷；Kit 的 `data`、`cache`、`logs` 另有命名卷，保留窗口布局、着色器缓存与应用日志。CUDA JIT 缓存（`CUDA_CACHE_PATH`）与 Triton 缓存放在各自缓存卷的子目录。
- 镜像用户的 UID/GID 在构建时由 `.env` 决定；更换身份需要重建镜像，并处理已有卷的权限。

## 7. 镜像发布与拉取

发布端在 `.env` 或命令行指定 registry 前缀与版本，构建后登录 registry 并推送：

```bash
docker login ghcr.io
IMAGE_PREFIX=ghcr.io/chanc313/robotics-lab IMAGE_TAG=<版本> ./scripts/lab build
IMAGE_PREFIX=ghcr.io/chanc313/robotics-lab IMAGE_TAG=<版本> ./scripts/lab publish
```

已构建的镜像再次 `build` 会完全命中缓存，只是增加 registry 名称的标签。GHCR 新推送的包默认私有。镜像中包含 Isaac Sim 等 NVIDIA 软件，改为公开前先确认相应许可是否允许再分发。

使用端克隆仓库，把相同的 `IMAGE_PREFIX`、`IMAGE_TAG` 写入 `.env`。镜像是私有的，拉取前需用有读取权限的账号登录：

```bash
docker login ghcr.io
./scripts/lab prepare
./scripts/lab pull
./scripts/lab check-installation ros
```

拉取模式不需要在主机安装 ROS、Isaac 或 Torch，也不重新编译上游；权重、数据与许可仍由使用者准备。拉取的镜像用户固定为发布时的 UID/GID（当前为 1000），使用机器需让该身份可读写源码与数据目录，或由发布端提供匹配身份的镜像；不要对整个项目使用 `chmod 777`。镜像 tag 视为不可覆盖的版本，每次发布在下表记录 tag、源码版本与 registry 返回的 digest。

### 发布记录

| 镜像 | 日期 | 源码 | digest |
|---|---|---|---|
| `ghcr.io/chanc313/robotics-lab-dev:v0.1.0` | 2026-10-12 | `e129f9e` | `sha256:936982f59eeeada9ab39fa9f1800aba47e75a21d1f8f1d3568b225b308939a9c` |
| `ghcr.io/chanc313/robotics-lab-policy:v0.1.0` | 2026-10-12 | `e129f9e` | `sha256:26609907c492809220b0fb228c5b0662bdf3f4ce66981050189a78abd4675183` |
| `ghcr.io/chanc313/robotics-lab-sim:v0.1.0` | 2026-10-12 | `e129f9e` | `sha256:4036798b6643404379a850849e21810a382aa4bcc95c75d82413300b00c5426b` |

## 依据

- [固定提交的 Arena 安装说明](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/docs/pages/quickstart/installation.rst)：官方 uv 锁文件安装与 Docker 路线，本项目在镜像内用锁文件安装。
- [Isaac Sim 容器 GUI](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/installation/install_container.html)、[Isaac Lab Docker](https://isaac-sim.github.io/IsaacLab/main/source/deployment/docker.html)：GPU 与 X11 显示。
- [Fast DDS 2.14 环境变量](https://fast-dds.docs.eprosima.com/en/2.14.x/fastdds/env_vars/env_vars.html)：UDPv4 内置传输。
