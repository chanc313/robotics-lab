# Arena × GR00T 项目启动

2026-10-09。根据三份共享记录中已经确定的方向，本项目先复现 **Isaac Lab-Arena × GR00T N1.6 的 G1 移动双臂流程**：从货架取棕色盒子，放入右侧桌面的蓝色箱子。先使用官方预训练权重完成闭环评估，再安排云端训练。机器人形态、支撑腿和部署到实物的研究在基线完成后另立实验。

2026-10-11 学习计划修订与全面容器迁移：用户授权制定和调整学习计划。重启后驱动、CUDA 与 200 步 Kit GUI 运行复核通过，见 [环境检查记录](archive/ENVIRONMENT_CHECK_2026-10-11.md)。学习顺序为 [核心理论导读](CORE_CONCEPTS.md) → [GUI 操作说明](ISAAC_GUI_AND_POLICY_RUNNER.md) → 下文动手与验收。10 月 9 日确定的项目目标与固定版本沿用。

## 工程边界

| 部分 | 职责与环境 |
|---|---|
| 本仓库 | `src/` 下 AI、ROS、仿真模块独立；实验层组合 Arena × GR00T；顶层保留 C++ / Python 学习沙盒 |
| Isaac Lab-Arena | `sim` 镜像内固定源码与独立 Python 环境，负责场景、物理、机器人控制、RL 训练与评估客户端 |
| Isaac-GR00T | `policy` 镜像内固定源码与独立环境，提供策略服务与模型开发；本机或远程容器运行由显存测量决定 |
| 底层控制 | 当前由上游 G1 WBC 承担；自研控制核心在真机阶段以动态库形式加入，见 [路线图](ROADMAP.md) |
| ROS 2 Jazzy | `dev` 中开发与验证节点，并运行 RViz；官方 GR00T 评估保留客户端/服务端接口 |
| 数据与产物 | 新权重与数据使用 `output/storage`，日志与报告使用 `output/runs`，绑定到运行容器；Git 保存配置与结果摘要 |

本项目使用 `dev`、`sim`、`policy` 三个镜像；组件职责见 [README](../README.md)。主机原有框架与历史记录保留，新入口不使用主机 ROS / Isaac / 模型环境。

## 容器启动与日常开发

首次在 Linux 主机终端、项目根目录执行 `./scripts/lab prepare` 和 `./scripts/lab build`。本地 `.env` 记录 UID/GID、ROS domain 与本人已接受的 Isaac Sim 许可状态；详见 [容器指南](CONTAINERS.md)。

默认 VS Code Dev Container 承担通用代码和 ROS 开发；已有旧容器先执行 **Dev Containers: Rebuild Container**。在两个容器终端分别运行 `ros2 run demo_nodes_cpp talker` 与 `ros2 run demo_nodes_py listener`。

从 Linux 主机终端启动容器化 GUI：

```bash
./scripts/lab sim-gui
./scripts/lab rviz
```

分别运行、结束前一个窗口后再进行下一项。仿真、RViz 和模型均在容器内运行，主机终端只是 Docker 启动入口。源码由本仓库绑定到 `/workspace`，上游源码安装在镜像 `/opt/arena`。

依赖 Isaac 的源码与断点调试选择 `Robotics lab sim` Dev Container 配置；模型代码选择 `Robotics lab policy`。各环境中的解释器与依赖独立，不混用虚拟环境。

## 固定的起点

以下上游状态于 2026-10-09 只读复核，与 2026-10-08 工作站验收记录一致；Arena 工作树干净。

| 项目 | 当前值 |
|---|---|
| Arena | `release/0.3.0`，`8737b4ceb25f99f81a81786b7fde73139b52f324` |
| Isaac Lab 子模块 | `af1bab4dc173ba69b08fab779c14ead61d13fd33` |
| Isaac-GR00T 子模块 | `e29d8fc50b0e4745120ae3fb72447986fe638aa6` |
| Arena `uv.lock` SHA-256 | `19dd4875d632b4e66fdeba27adec408623cae2270b21cd912b57b4f9cf420a6d` |
| 已安装包元数据 | Isaac Sim `6.0.1.0`；Isaac Lab `6.1.17`；Arena `0.3.0`；Torch `2.11.0+cu128` |
| 本机 GPU | RTX 4080 Laptop，12282 MiB 显存 |
| 官方目标权重 | `nvidia/GN1x-Tuned-Arena-G1-Loco-Manipulation`，revision `gn1_6` |

容器迁移沿用此前已验收的 source 组、固定提交与锁文件。文档中的 Lab 3.0 系列称呼与 source 包元数据不同，重建时以固定提交和锁文件为准。上游环境在镜像内按已验证的 `--frozen` 安装流程复建，不因其 `--locked` 重新解析失败而改写上游锁文件；本仓库仍使用自己的 `uv sync --locked`。

此前主机运行验收包括 CUDA 运算、Arena 零策略 20 步、Kit GUI 200 步，以及 Isaac → ROS `/clock`。这些记录证明基础运行链路，不代表 G1 策略复现成功。GR00T 独立容器环境纳入迁移；策略权重和训练数据准备仍属于后续步骤。容器安装历史与本轮精简状态见 [迁移记录](archive/CONTAINER_MIGRATION_2026-10-11.md)。

## 第一阶段与完成条件

1. **理解运行链路。** 能说明场景、机器人、任务、策略、评估器各自的职责；亲手完成基础仿真并保留日志。
2. **完成单环境闭环。** 使用上述 N1.6 权重和 `g1_wbc_joint`，启动独立策略服务；保存配置、视频、实际 episode 数与成功/失败结果。进入这一步前记录仿真和推理的峰值显存，确定服务运行位置。
3. **形成可比较的基线。** 固定权重 revision、物理设备、任务参数和种子，运行多个完整 episode；记录成功率、超时、异常与推理延迟。短运行或单次成功不作为统计结论。
4. **安排训练与研究。** 基线完成后确定数据、训练配方、云端 GPU 和预算；结构变化与策略变化分别设计实验。

官方闭环任务使用 `g1_wbc_joint`；遥操作/数据生成使用 `g1_wbc_pink`。N1.6 输出上半身关节目标以及基座高度、导航命令，由下层 WBC 完成全身控制。复现时保留原任务、关节映射和 CPU 物理设置，并记录任何偏离。

## 第一次工作：3–4 小时（2026-10-11 修订）

目标是你能亲手操作 GUI，并用自己的话解释运行链路。按顺序完成，时间为估计，可以分段进行；稍晚提交材料后再验收。第一轮先完成理论导读与基础练习，验收通过后安排 GR00T 环境和权重准备。

### 0. 理论导读，约 20–30 分钟

阅读 [核心理论](CORE_CONCEPTS.md)，先回答其中的理解检查。重点掌握：状态与观测、策略与控制器、物理与控制时钟、episode 与成功条件、训练与推理。第一轮只要求解释概念和找到代码依据。

### 0.5. ROS 容器入门，约 10 分钟

按本页启动入口重建 Dev Container。在两个容器终端运行 talker / listener，记录 `ros2 pkg prefix demo_nodes_cpp` 的输出及收到 `I heard` 的截图或终端文本。分别用 Ctrl+C 停止；解释发布者、订阅者和 topic 各自是什么。此步骤使用已安装的官方示例，自己的 ROS 包后续在本仓库开发。

### 1. 记录环境与创建材料目录，约 10–15 分钟

以下命令在 **Linux 主机终端**执行，提示符应是 shell 的 `$`。它们通过 Docker 使用容器内的框架；使用同一个终端保留本次材料目录变量。

```bash
cd /home/channing/projects/robotics-lab
export LEARNING_RUN_NAME="learning-$(date +%Y%m%d-%H%M%S)"
export ARENA_RUN_DIR="$PWD/output/runs/$LEARNING_RUN_NAME"
export CONTAINER_RUN_DIR="/runs/$LEARNING_RUN_NAME"
mkdir -p "$ARENA_RUN_DIR"
set -o pipefail
```

记录主机 GPU 与容器环境信息，保存为材料目录的 `versions.txt`：

```bash
nvidia-smi
./scripts/lab sim python -c 'import sys, torch, gymnasium, pandas; print(sys.executable); print(sys.version); print(torch.__version__, gymnasium.__version__, pandas.__version__)'
./scripts/lab sim git rev-parse HEAD
```

解释主机材料路径与容器 `/runs` 路径如何对应，以及开发、仿真、模型三种解释器为什么分开。

### 2. 熟悉 GUI 与 Arena 场景，约 30–45 分钟

先运行最简单的官方方块教程：

```bash
./scripts/lab tutorial basic
```

完成聚焦、旋转、平移、缩放；找到 `/World/Object`，在 Property 中查看位置与尺寸；暂停、继续并关闭窗口。保存一张显示 Viewport、Stage、Property 的截图。

然后打开持续运行的 Arena 场景：

```bash
./scripts/lab sim-gui 2>&1 | tee "$ARENA_RUN_DIR/interactive.log"
```

在 Stage 找到 `/World/envs/env_0` 下的机器人和方块；用 Shift + 左键拖动物体，观察接触、重力和重置。截图后关闭窗口。解释为什么这个入口持续运行，而 policy_runner 会按预算退出。详细界面操作见 [GUI 指南](ISAAC_GUI_AND_POLICY_RUNNER.md)。

### 3. 观察机械臂控制，约 20–30 分钟

关闭前一个窗口后运行官方 IK 教程：

```bash
./scripts/lab tutorial ik 2>&1 | tee "$ARENA_RUN_DIR/ik.log"
```

观察三个末端目标、当前末端坐标轴和机械臂运动。保存截图，并解释“末端目标 → IK → 关节目标 → 物理运动”。说明这个教程是否使用神经网络。观察完后关闭窗口。

### 4. 完成一次可记录的 episode，约 20–30 分钟

用零策略完成一个 episode，而非只跑 20 步：

```bash
./scripts/lab evaluate --viz kit --device cpu --policy_type zero_action --num_episodes 1 --output_base_dir "$CONTAINER_RUN_DIR/evaluation" cube_goal_pose 2>&1 | tee "$ARENA_RUN_DIR/evaluation.log"
```

观察初始化、物体运动和结束。保存 GUI 截图、日志和生成的 HTML / JSONL 报告；记录实际 episode 数、结束原因和成功率。该任务当前最长 70 秒仿真时间，墙钟时间会不同。

零策略的任务成功不作为本轮验收要求。验收看的是你能确认运行完成、正确读取结果，并解释奖励与评估指标的区别。若运行报错，保存原始日志和命令，先定位再继续。

### 5. 读 G1 的数据契约与任务判定，约 45–60 分钟

按下表找到对应配置，先进行源码阅读：

| 文件 | 要找出的内容 |
|---|---|
| [G1 环境](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena_environments/galileo_g1_locomanip_pick_and_place_environment.py) | 对象、目标、30 秒 episode、50 Hz 控制 |
| [GR00T 闭环配置](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena_gr00t/policy/config/g1_locomanip_gr00t_closedloop_config.yaml) | 语言指令、头部相机、动作块和关节映射 |
| [G1 模态配置](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena_gr00t/embodiments/g1/g1_sim_wbc_data_config.py) | video / state / language 输入与 action 输出 |
| [任务](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena/tasks/pick_and_place_task.py)和[放置判定](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena/tasks/predicates/object_on_destination_term.py) | 结束、成功、几何、接触与速度检查 |
| [官方评估流程](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/docs/pages/example_workflows/locomanipulation/step_5_evaluation.rst) | 仿真客户端与独立 GR00T 服务如何连接 |

### 6. 提交验收，约 20–30 分钟

本次材料统一放在 `$ARENA_RUN_DIR`。提交该目录的绝对路径，并附下面四部分：

1. **环境证据**：主机版本输出、容器 ROS 包路径与示例通信输出、实际执行的命令。
2. **运行证据**：交互场景、IK、完整 episode 的日志；至少三张能辨认场景的 GUI 截图；HTML / JSONL 结果路径。
3. **一页理解说明**：约 800–1500 中文字，用自己的话回答下列问题，并附对应源码位置。
   - 状态、观测、动作和控制器各自是什么？
   - policy_runner 与 Policy 适配器分别负责什么？为什么当前没有训练更新？
   - 什么是 episode？为什么 20 步空样本和 1 个 episode 都不足以证明稳定成功？
   - G1 的 GR00T 输入、输出是什么？50 个动作在 50 Hz 下覆盖多久？
   - GR00T 与 WBC 分别承担什么？`g1_wbc_pink` 与 `g1_wbc_joint` 为什么不能随意互换？怎样判定盒子放置成功？
4. **问题记录**：遇到的问题、原始错误、自己的判断与处理；没有问题也说明运行结果。

验收检查：GUI 操作可完成、episode 有实际结果、职责划分正确、数据契约有源码依据、证据能对应到本次运行。缺项时反馈具体补做内容；通过后再进入 GR00T 单环境闭环。

## 依据

- 项目决定与学习节奏：[机械臂学习记录](https://chatgpt.com/s/cx_6ac387d20c1c8191b9d0b97358958026)、[研究方向记录](https://chatgpt.com/s/cx_6ac3880b7a4c8191b351b1046de69799)、[职业规划记录](https://chatgpt.com/s/cx_6ac38816c9a48191ba1b1226b753d5f1)。
- 操作以[固定提交的官方闭环教程](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/docs/pages/example_workflows/locomanipulation/step_5_evaluation.rst)及同一 checkout 的源码为准；[在线教程](https://isaac-sim.github.io/IsaacLab-Arena/main/pages/example_workflows/locomanipulation/step_5_evaluation.html)用于对照更新。
- 工作站已通过项目保存在独立的 `workstation-config` 验收记录中；本页仅保存项目所需的版本起点。
