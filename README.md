# Robotics lab

长期维护的 Embodied AI 研究骨架：上层 AI 与强化学习、Isaac 仿真、中层 ROS 与控制，全部在容器中开发和运行。当前起点是复现 **Isaac Lab-Arena × GR00T N1.6 的 Unitree G1 移动双臂**流程，再在其上优化与迭代；推进顺序见 [路线图](ws/docs/ROADMAP.md)。

## 三个容器

三个容器相互独立、各自在内部闭环，不依赖彼此即可单独运行和验证；它们之间只通过数据交互（共享的 `/data`、`/runs` 与网络端点），跨容器接口留待[路线图](ws/docs/ROADMAP.md)第 2 步设计。版本全部固定。

| 容器 | 闭环功能（纯净骨架） | 目前在 G1 项目中的角色 |
|---|---|---|
| `dev` | ROS 2 Jazzy 开发与通信、RViz；ros2_control + MuJoCo 控制闭环；MoveIt 2 规划、Nav2 导航；C++26 / Python 原生开发 | 尚未进入回路；`src/ros` 预留给 ROS 适配层，控制与规划工具目前服务于个人技术栈学习 |
| `sim` | Isaac Sim 物理与渲染、Isaac Lab 环境、RSL-RL 强化学习训练、Arena 任务评估、数据生成与转换 | 运行 G1 移动操作任务，作为 GR00T 推理服务的客户端执行闭环评估 |
| `policy` | GR00T N1.6 推理服务、模型微调与训练、自研模型开发 | 加载官方 G1 微调权重，为 sim 提供动作块 |

每个容器都有自己的 README（`.devcontainer/<容器>/README.md`，在该容器里显示为 `/workspace/README.md`），写明镜像内容、闭环功能与自检命令、单独复用时需要带走的文件；概览见 [容器指南](ws/docs/CONTAINERS.md#三个容器)。Gazebo 与 Open-RMF 不在规划内，涉及多机器人时再评估。

## 目录

仓库分两层：根目录放 Git、编排与基础设施，只在主机上使用；`ws/` 是开发工作区，每个容器只挂载其中属于自己的部分。

```text
compose.yaml, compose.gui.yaml   三个服务、各容器的挂载、共享构建参数、GUI 叠加
docker/                          三个 Dockerfile、入口与检查脚本、上游固定版本、模型依赖锁
.devcontainer/                   三个 VS Code 容器配置、各自的编辑器设置、共享 Ruff 规则
scripts/lab                      主机上的唯一启动器（构建、发布、各类运行入口）
output/                          运行产物（Git 忽略）：build → /build，runs → /runs，storage → /data
ws/                              开发工作区
  docs/                          指南、学习材料、路线图（三个容器都挂载）
  src/ai/                        模型、模仿学习与 RL 算法（policy）
  src/ros/                       ROS 2 包与节点（dev）
  src/simulation/                Isaac 任务、环境与仿真适配（sim）
  experiments/                   实验组合配置（sim、policy）
  cppsrc/, pythonsrc/, rossrc/   C++ / Python / ROS 2 学习沙盒（dev）
```

容器里的 `/workspace` 只有该容器用到的目录，跨容器的协作由编排器负责；Git 操作在主机上进行。挂载规则见 [开发指南](ws/docs/DEVELOPMENT.md#仓库与工作区)。

## 快速开始

主机需要 Linux x86_64、Docker / Compose（≥ 2.30）、NVIDIA 驱动与 NVIDIA Container Toolkit；显示窗口另需 X11 与可读的会话 Xauthority。Python 包只通过 Dockerfile 与锁文件进入镜像，不在容器里手工安装。

```bash
./scripts/lab prepare         # 创建 output 目录与 .env
./scripts/lab build           # 本地构建 dev / sim / policy
./scripts/lab help            # 全部入口
```

也可以拉取已发布的私有镜像，免去本地构建：先 `docker login ghcr.io`，在 `.env` 写入 `IMAGE_PREFIX=ghcr.io/chanc313/robotics-lab` 与 `IMAGE_TAG`（版本见 [发布记录](ws/docs/CONTAINERS.md#发布记录)），再执行 `./scripts/lab pull`。

运行 Isaac 前，本人接受 Isaac Sim 许可后，在 `.env` 取消注释 `OMNI_KIT_ACCEPT_EULA=YES`、`ACCEPT_EULA=Y`。VS Code 用户执行 **Dev Containers: Reopen in Container**，在 dev、sim、policy 三个配置中选择。

## 常用入口

```bash
./scripts/lab check-installation ros|sim|policy   # 检查各容器的框架安装
./scripts/lab ros-shell       # dev 容器 shell（ROS / C++ / 学习沙盒）
./scripts/lab dev-gui         # 带显示的 dev shell（MuJoCo 窗口、rqt）
./scripts/lab rviz            # RViz
./scripts/lab sim-gui         # 持续保留 Arena GUI
./scripts/lab train           # Isaac Lab 强化学习训练（默认短 Cartpole）
./scripts/lab policy-server   # GR00T G1 推理服务
./scripts/lab g1-evaluate     # G1 闭环评估，连接已运行的推理服务
```

这些入口提供启动方式，不代表对应流程已经验收；当前进度见 [路线图](ws/docs/ROADMAP.md)。

## 文档

- [容器指南](ws/docs/CONTAINERS.md)：构建、IDE、启动、跨容器通信、数据与缓存、镜像发布
- [开发指南](ws/docs/DEVELOPMENT.md)：仓库结构、模块约定、依赖规则、接口与测试的时机
- [项目目标与研究方向](ws/docs/PROJECT_GOALS.md)：长期目标、设计原则与分层架构设想
- [路线图](ws/docs/ROADMAP.md)：闭环推进顺序与已定的长期决定
- [学习沙盒工具链](ws/docs/TOOLCHAIN.md)：C++、Python、ROS 2、ros2_control、MuJoCo、MoveIt 2 与 Nav2
- 学习材料：[G1 Demo 学习计划](ws/docs/LEARNING_PLAN.md)、[核心理论](ws/docs/CORE_CONCEPTS.md)、[ROS 2 入门](ws/docs/ROS_BASICS.md)、[Isaac GUI 与 policy_runner](ws/docs/ISAAC_GUI_AND_POLICY_RUNNER.md)、[G1 / GR00T 配置导读](ws/docs/G1_GR00T_CONFIGS.md)、[项目启动与第一阶段](ws/docs/PROJECT_START.md)
- [历史记录](ws/docs/archive/)：环境检查、驱动诊断、容器迁移、骨架审查

许可证：[LICENSE](LICENSE)。
