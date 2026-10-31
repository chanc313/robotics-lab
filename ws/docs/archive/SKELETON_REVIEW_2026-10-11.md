# 骨架审查与后续路线

> 历史记录。同日后续处理：清理项已全部完成；`src/control` 移除，控制核心推迟到真机阶段；学习沙盒移到顶层 `cppsrc/`、`pythonsrc/`；测试与 CI 推迟到全栈打通后；"下次重建时一起改"各项已随镜像重建完成。推进顺序与长期决定见 [项目计划](../PROJECT_PLAN.md)。

2026-10-11。审查对象：当前工作树（含未提交改动）。目标对照：全面容器化、上层 AI / RL、Isaac 仿真、中层 ROS、底层电机控制组成的纯净闭环骨架，起点是复现 Isaac Lab-Arena × GR00T N1.6 的 G1 移动双臂流程，并为后续迭代留出扩展空间。

## 结论

1. **容器化与环境隔离是扎实的。** 三个镜像职责清楚；上游提交、锁文件与 Python 版本固定；容器以非 root 用户运行；GUI 不改 `xhost`；结果目录在容器退出后保留。下文的静态检查全部通过。
2. **它目前是"分层开发环境 + 上游闭环"，还不是"自己的闭环骨架"。** 唯一能跑通的回路是 Arena `policy_runner`（`sim`）经 ZMQ 连接 GR00T 服务（`policy`），G1 的 WBC 在 `sim` 进程内运行。ROS 与 `src/control` 都不在回路中，`src/ai`、`src/ros`、`src/control`、`src/simulation` 只有 README。这与此前"不预建接口、不放假节点"的决定一致，但意味着闭环接口尚未设计。
3. **本轮修复了 11 处问题。** 最影响日常开发的是：`dev` 容器里的 `python3` 实际是学习用 venv，连 `import rclpy` 都会失败。
4. **扩展性上最该提前定的三件事**：控制层的硬件抽象（G1 真机底层走 `unitree_sdk2` 的 DDS 话题，而不是 MCU / PWM）、闭环接口契约、ROS 中间件（Unitree 生态使用 Cyclone DDS）。详见"闭环与扩展"。

## 检查范围与结果

| 检查 | 结果 |
|---|---|
| `docker compose config`：基础、全部 profile、GUI 叠加、Dev Container 叠加 | 通过（修改前后各一次） |
| `docker build --check`：`Dockerfile`、`docker/Dockerfile.sim`、`docker/Dockerfile.policy` | 无警告（只做 lint，不构建） |
| `bash -n`（`scripts/lab`、`docker/*.sh`）、编辑器 JSON（`jq`）、`git diff --check` | 通过 |
| Ruff check / format（`src/pythonsrc`、`scripts`） | 通过 |
| `dev` 内 C++26 Release 构建并运行 `main` | 通过 |
| `dev` 内 ROS Python 探针 | **修改前失败**（见修复 1），修改后通过 |
| `./scripts/lab check-installation ros`、`dev` 内 talker / listener | 修改后通过，收到 `I heard: [Hello World: 1]` |
| `policy` 内 `CUDA_CACHE_PATH` 是否生效 | 驱动在缓存卷中创建了 `nv/ComputeCache` 目录 |
| 启动器参数与固定上游对照（主机 `~/projects/vendor/IsaacLab-Arena`，提交 `8737b4c`） | `g1-evaluate` 与官方 step 5 一致；`policy-server` 省略 `--modality-config-path`，在 `--model-path` 模式下该参数不被读取，不影响 |

**未执行**：`sim` / `policy` 镜像构建、`check-installation sim|policy`、任何 GPU 仿真、G1 权重下载与闭环评估。`dev` 镜像已按修复 1 重建（只有最后一层变化）。

## 本轮已修复

| # | 问题与证据 | 修改 |
|---|---|---|
| 1 | `dev` 镜像把 `/workspace/.venv/bin` 放在 `PATH` 最前，`python3` 指向学习 venv。实测 `python3 -c "import rclpy"` 报 `No module named 'yaml'`，`sensor_msgs.msg.Imu()` 报缺 `numpy`。直接 `python3 node.py` 会失败，构建时自动发现 Python 也可能选错解释器 | `Dockerfile` 去掉该 `PATH`；`.vscode/settings.json` 关闭终端自动激活；默认 Dev Container 为 Pylance 加 ROS 包路径。学习代码照旧用 `uv run` |
| 2 | 绑定目录缺失时 Docker 以 root 创建。证据：`output/control/` 为 `root:root`，`output/` 属组为 root。`sim` / `policy` 的 Dev Container 不经过 `scripts/lab prepare` | 三个 `devcontainer.json` 增加 `initializeCommand: ./scripts/lab prepare` |
| 3 | `.env.example` 预填 `OMNI_KIT_ACCEPT_EULA=YES` / `ACCEPT_EULA=Y`，与"不代替新使用者接受许可"的说明矛盾 | 改为注释，需本人取消注释 |
| 4 | `TRITON_CACHE_DIR` 指向 `~/.cache` 根目录，Triton 的哈希目录与 HF、uv 等缓存混在一起 | 改为 `~/.cache/triton` |
| 5 | CUDA JIT 缓存默认在 `~/.nv/ComputeCache`，镜像中没有该目录，`--rm` 容器每次丢失；NVIDIA 的 Isaac Sim 容器说明会单独挂载它 | `sim`、`policy` 设置 `CUDA_CACHE_PATH` 到各自缓存卷子目录（无需重建镜像） |
| 6 | Compose 项目名随克隆目录名变化，卷名与容器名随之变化 | `compose.yaml` 固定 `name: robotics-lab`，与现有卷名相同，已有数据不受影响 |
| 7 | ROS 变量两处定义：`dev` 在 compose，`sim` 在 `Dockerfile.sim` 的 ENV | 新增 `x-ros-env` 锚点供 `dev`、`sim` 共用，`RMW_IMPLEMENTATION` 等可在 `.env` 覆盖；默认值不变。已确认 Isaac 自带 `librmw_fastrtps_cpp` 与 `librmw_cyclonedds_cpp` |
| 8 | `dev` 没有 `/data`、`/runs`，与 `sim`、`policy` 路径不一致（例如 rosbag 输出位置） | `dev` 增加两个绑定目录 |
| 9 | `check_installation.py` 写死 `clang++-20`，与可配置的 `LLVM_VERSION` 脱节 | 改用 `$CXX` |
| 10 | CI 只验证学习入口；容器配置无任何自动检查 | `ci.yml` 新增 `config` 作业（三套 Compose 叠加、`bash -n`、JSON）；Ruff 覆盖 `scripts/`，VS Code lint 任务同步 |
| 11 | `.dockerignore` 的 `__pycache__` 等模式只匹配根目录 | 改为 `**/` 前缀 |

同步更新了 [容器指南](../CONTAINERS.md)、[开发指南](../DEVELOPMENT.md)、[通用工具链](../TOOLCHAIN.md) 的对应段落。

**刻意没改**：`docker/Dockerfile.sim`、`docker/Dockerfile.policy`、`docker/versions.env`、`docker/fetch_arena.sh`。这些文件在构建早期被复制，任何改动都会让 44.7 GB 的 `sim` 和 26.1 GB 的 `policy` 镜像从头重建。相关发现放在"下次重建时一起改"。

## 分层对照

| 层 | 目标 | 现状 | 判断 |
|---|---|---|---|
| 容器与环境 | 主机只负责 Docker、驱动、显示、存储 | 三镜像、固定上游、非 root、GPU / X11、命名卷缓存、镜像发布入口 | 达标 |
| 上层 AI / RL | 模型训练与推理、RL 算法 | `policy` 固定 GR00T N1.6（Python 3.10、Torch 2.7.1+cu126、FlashAttention）；RL 用 `sim` 内 Isaac Lab 的 RSL-RL；有微调与服务入口 | 基线就绪；`src/ai` 为空。自有 Python 包如何进入 `sim` / `policy` 环境尚无约定 |
| Isaac 仿真 | 场景、任务、评估、数据生成 | Arena 0.3.0 / Isaac Lab / Isaac Sim 6.0.1 固定；GUI、教程、评估、训练入口齐全；HDF5 → LeRobot 转换按官方说明在 Arena 环境（即 `sim`）执行，依赖已在镜像内 | 达标 |
| 中层 ROS | 编排、感知、状态消息、设备集成 | `dev` 提供 Jazzy + RViz；`sim` 有 Isaac 自带的 Jazzy bridge 库；主机网络、同一 domain | 环境就绪，未接入任何数据流 |
| 底层控制 | 关节 / 电机控制律、限幅、硬件接口 | `src/control` 为空；G1 的 WBC 在上游 Python 中 | 未开始；定位描述需要调整（见下） |
| 闭环 | 观测 → 决策 → 控制 → 物理 → 观测 | 只有上游回路：`sim`（WBC + 物理）↔ ZMQ ↔ `policy` | 接口契约未定义 |

## 闭环与扩展：建议的推进顺序

每一步都在上一步可运行的基础上增加一层，避免一次性引入 ROS、控制和真机三类不确定性。

1. **跑通上游基线回路。** 下载权重，`policy-server` + `g1-evaluate`，记录成功率与延迟。本机 GPU 为 12 GB：带相机的 Isaac 渲染与 GR00T 3B 推理同卡运行可能不够，评估时用 `nvidia-smi` 记录峰值；不够时把 `policy` 放到远程 GPU，启动器已支持 `--remote_host`。
2. **先写接口契约，再写代码。** 以 G1 为例，契约至少包括：43 自由度关节顺序（上游 `isaaclab_arena_gr00t/embodiments/g1/43dof_joint_space.yaml`）、单位与坐标系、50 Hz 控制频率与 50 步动作块、时间戳与 `use_sim_time`、超时与失效语义。放在 `docs/` 即可，与"不预建空包"的原则不冲突。
3. **ROS 先做旁路观察者。** 让 Isaac 的 ROS 2 bridge 发布 `/clock`、`/joint_states`、`/tf` 和头部相机，`dev` 中用 RViz 查看、用 rosbag 记录到 `/runs`。这不改变回路时序，是 ROS 第一次产生真实价值。优先使用标准消息：自定义消息需要在 `dev` 中构建，再通过 `LD_LIBRARY_PATH` / `PYTHONPATH` 交给 `sim` 中 Isaac 自带的 ROS 库加载，链路更长。
4. **控制核心做成纯 C++ 库，再分别封装。** 核心不依赖 ROS、Isaac、模型 SDK（与现有 README 一致），对外是"硬件抽象接口"：读关节状态，写关节目标与增益。仿真中通过 pybind11 或 nanobind 绑定加载进 `sim` 进程，保证 RL 训练和评估的确定性；部署时再加 ROS / DDS 封装。RL 训练的内层循环不要经过 ROS。
5. **ROS 进入回路（部署形态）。** 把策略输出改走 ROS 话题，引入真实的异步与延迟，与第 1 步的指标对比，量化通信带来的性能损失。
6. **真机。** Unitree G1 的底层接口是 `unitree_sdk2`（C++，基于 Cyclone DDS 的 `LowCmd` / `LowState` 话题）或 `unitree_ros2`（要求 `rmw_cyclonedds_cpp`）。第 7 项修复已让 RMW 可切换，届时在 `dev` 镜像加装 `ros-jazzy-rmw-cyclonedds-cpp` 即可。G1 开发版机载计算单元为 aarch64 的 Jetson Orin（接入前需核实具体型号），控制与 ROS 镜像届时需要多架构构建。

关于"底层电机控制"的定位：`src/control/README.md` 现在写的是"原生嵌入式 C++"，并以 MCU、RTOS、PWM 作为未来内容。对 G1 而言，电机驱动板与 MCU 固件不对用户开放，用户能写的最底层是运行在 Linux 上、通过 DDS 下发关节位置 / 速度 / 力矩与 PD 增益的控制进程。建议把该目录的定位改为"硬件无关的 C++ 控制核心 + 硬件抽象层（仿真 / unitree_sdk2）"，MCU / PWM 只在将来接入自制硬件时再考虑。这是方向性判断，README 未改动，由你决定。

## 下次重建 sim / policy 时一起改

- `docker/versions.env` 中的 `UV_VERSION` 没有任何地方读取；实际的 uv 版本来自 `compose.yaml` / Dockerfile 的 `ARG`、CI 和 `pyproject.toml`。删除它，或改为由它驱动构建参数。
- `Dockerfile.sim` 的 `ubuntu:24.04` 与三处 `ghcr.io/astral-sh/uv` 只按 tag 固定，`policy` 的 CUDA 基础镜像已按摘要固定；统一按摘要固定。
- `fetch_arena.sh` 在 `policy` 镜像里也拉取 Isaac Lab 子模块，而 `policy` 只需要 GR00T 子模块和 `isaaclab_arena_gr00t`。
- `Dockerfile`（dev）中 RViz 单独一层 `apt-get update`，可并入 ROS 安装层；这项改动只需重建 `dev`，成本很低，但不影响功能，留给你决定。

## 仓库与主机清理（需你确认后再删）

| 对象 | 说明 | 处理方式 |
|---|---|---|
| `output/control/` | 已淘汰的 control 镜像留下，属主 root | `sudo rm -rf output/control` |
| Docker 卷 `robotics-lab_control-build` | 已淘汰镜像的构建卷 | `docker volume rm robotics-lab_control-build` |
| 主机 `.venv/`、`output/build/`、`output/dist/`、`output/local-artifacts/` | 容器化之前的主机产物；容器内 `.venv`、`output/build` 是命名卷，主机这几份已不被使用 | 确认无用后删除 |
| 根目录空目录 `.agents/`、`.aws/`、`.codex/`、`data/`、`tests/` | 项目不使用，可能由其他工具的沙箱创建 | 确认来源后删除 |
| `docs/mermaid-diagram.png` | 未被任何文档引用 | 引用或删除 |
| 已退出的 `robotics-lab-sim-1`、`robotics-lab-policy-1` | 早先 Dev Container 留下 | 无害，可 `docker container prune` |

## 其他建议（低优先级）

- 学习入口 `src/cppsrc`、`src/pythonsrc` 与业务模块并列在 `src/` 下。若希望 `src/` 只含业务模块，可整体移到 `learning/`，需同步根 CMake、`pyproject.toml` 的 `module-root`、CI 与文档。
- 在共享网络上，`ROS_DOMAIN_ID=0` 加主机网络会发现局域网里其他人的 ROS 图。Jazzy 可设 `ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST` 限制在本机；因为未复测 `sim` ↔ `dev` 桥接，本轮没有改默认值。
- Arena 官方 G1 微调命令使用 16 个 dataloader worker，`shm_size: 2gb` 在训练机上大概率不够；训练时按机器调大或使用 `ipc: host`。
- 第一个业务模块出现时，同时确定测试入口：`sim` / `policy` 内的 pytest、`dev` 内的 `colcon test`、控制核心的 CTest，并纳入 CI。
- 自有 Python 包进入 `sim` / `policy` 环境的方式（`PYTHONPATH`、或在容器启动时 editable 安装）在第一个包出现时确定，不要手工 `pip install` 进镜像环境。
- 文档中"当前不……"的范围声明较多，分散在各页。可考虑用一页架构图（目标闭环 + 各模块未来位置）替代，正文只保留操作说明。
- `CMakeLists.txt` 注释称 CMake 3.24–3.28 不能用 `CXX_STANDARD` 选 C++26；实际 3.28 已支持 Clang ≥17，GCC 需要更新的 CMake。手动 `-std=c++2c` 仍然可用，只是注释不准确。

## 需要你做的

1. 在 VS Code 对默认开发容器执行 **Dev Containers: Rebuild Container**。正在运行的 `robotics-lab-dev-1` 仍使用旧镜像和旧挂载，修复 1、2、7、8 重建后才生效。
2. 决定"仓库与主机清理"中的哪些项目可以删除。
3. 决定是否按上文调整 `src/control` 的定位描述。
