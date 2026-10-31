# Arena × GR00T 项目启动

> 已归档（2026-10-31）：早期材料，只作历史参考。当前文档见 [文档索引](../README.md)。

2026-10-09。根据三份共享记录中已经确定的方向，本项目先复现 **Isaac Lab-Arena × GR00T N1.6 的 G1 移动双臂流程**：从货架取棕色盒子，放入右侧桌面的蓝色箱子。先使用官方预训练权重完成闭环评估，再安排云端训练。机器人形态、支撑腿和部署到实物的研究在基线完成后另立实验。

2026-10-11 学习计划修订与全面容器迁移：用户授权制定和调整学习计划。重启后驱动、CUDA 与 200 步 Kit GUI 运行复核通过，见 [环境检查记录](ENVIRONMENT_CHECK_2026-10-11.md)。学习安排见 [G1 Demo 学习计划](LEARNING_PLAN.md)。10 月 9 日确定的项目目标与固定版本沿用。

## 工程边界

| 部分 | 职责与环境 |
|---|---|
| 本仓库 | `src/` 下 AI、ROS、仿真模块独立；实验层组合 Arena × GR00T；顶层保留 C++ / Python 学习沙盒 |
| Isaac Lab-Arena | `sim` 镜像内固定源码与独立 Python 环境，负责场景、物理、机器人控制、RL 训练与评估客户端 |
| Isaac-GR00T | `policy` 镜像内固定源码与独立环境，提供策略服务与模型开发；本机或远程容器运行由显存测量决定 |
| 底层控制 | 当前由上游 G1 WBC 承担；自研控制核心在真机阶段以动态库形式加入，见 [路线图](ROADMAP.md) |
| ROS 2 Jazzy | `dev` 中开发与验证节点，并运行 RViz；官方 GR00T 评估保留客户端/服务端接口 |
| 数据与产物 | 新权重与数据使用 `output/storage`，日志与报告使用 `output/runs`，绑定到运行容器；Git 保存配置与结果摘要 |

本项目使用 `dev`、`sim`、`policy` 三个镜像；组件职责见 [容器指南](../CONTAINERS.md) 与 [开发指南](../DEVELOPMENT.md)。主机原有框架与历史记录保留，新入口不使用主机 ROS / Isaac / 模型环境。

## 容器启动与日常开发

首次在 Linux 主机终端、项目根目录执行 `./scripts/lab prepare` 和 `./scripts/lab build`。本地 `.env` 记录 UID/GID、ROS domain 与本人已接受的 Isaac Sim 许可状态；详见 [容器指南](../CONTAINERS.md)。

默认 VS Code Dev Container 承担通用代码和 ROS 开发；已有旧容器先执行 **Dev Containers: Rebuild Container**。在两个容器终端分别运行 `ros2 run demo_nodes_cpp talker` 与 `ros2 run demo_nodes_py listener`。

从 Linux 主机终端启动容器化 GUI：

```bash
./scripts/lab sim-gui
./scripts/lab rviz
```

分别运行、结束前一个窗口后再进行下一项。仿真、RViz 和模型均在容器内运行，主机终端只是 Docker 启动入口。每个容器只把 `ws/` 中自己的目录挂载到 `/workspace`，上游源码安装在镜像 `/opt/arena`。

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

此前主机运行验收包括 CUDA 运算、Arena 零策略 20 步、Kit GUI 200 步，以及 Isaac → ROS `/clock`。这些记录证明基础运行链路，不代表 G1 策略复现成功。GR00T 独立容器环境纳入迁移；策略权重和训练数据准备仍属于后续步骤。容器安装历史与本轮精简状态见 [迁移记录](CONTAINER_MIGRATION_2026-10-11.md)。

## 第一阶段与完成条件

1. **理解运行链路。** 能说明场景、机器人、任务、策略、评估器各自的职责；亲手完成基础仿真并保留日志。
2. **完成单环境闭环。** 使用上述 N1.6 权重和 `g1_wbc_joint`，启动独立策略服务；保存配置、视频、实际 episode 数与成功/失败结果。进入这一步前记录仿真和推理的峰值显存，确定服务运行位置。
3. **形成可比较的基线。** 固定权重 revision、物理设备、任务参数和种子，运行多个完整 episode；记录成功率、超时、异常与推理延迟。短运行或单次成功不作为统计结论。
4. **安排训练与研究。** 基线完成后确定数据、训练配方、云端 GPU 和预算；结构变化与策略变化分别设计实验。

官方闭环任务使用 `g1_wbc_joint`；遥操作/数据生成使用 `g1_wbc_pink`。N1.6 输出上半身关节目标以及基座高度、导航命令，由下层 WBC 完成全身控制。复现时保留原任务、关节映射和 CPU 物理设置，并记录任何偏离。

## 学习安排

2026-10-13 官方 G1 demo 跑通后，学习按 [G1 Demo 学习计划](LEARNING_PLAN.md) 分天进行。10 月 11 日版“第一次工作”中的 GUI 操作、IK 教程、零策略 episode 与 G1 数据契约阅读，已分别并入其中的 Day 1–4，最后的一页理解说明放在 Day 5。

## 依据

- 项目决定与学习节奏：[机械臂学习记录](https://chatgpt.com/s/cx_6ac387d20c1c8191b9d0b97358958026)、[研究方向记录](https://chatgpt.com/s/cx_6ac3880b7a4c8191b351b1046de69799)、[职业规划记录](https://chatgpt.com/s/cx_6ac38816c9a48191ba1b1226b753d5f1)。
- 操作以[固定提交的官方闭环教程](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/docs/pages/example_workflows/locomanipulation/step_5_evaluation.rst)及同一 checkout 的源码为准；[在线教程](https://isaac-sim.github.io/IsaacLab-Arena/main/pages/example_workflows/locomanipulation/step_5_evaluation.html)用于对照更新。
- 工作站已通过项目保存在独立的 `workstation-config` 验收记录中；本页仅保存项目所需的版本起点。
