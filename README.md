# Robotics lab

长期维护的 Embodied AI 研究骨架：上层 AI 与强化学习、Isaac 仿真、中层 ROS，全部在容器中开发和运行。当前起点是复现 **Isaac Lab-Arena × GR00T N1.6 的 Unitree G1 移动双臂**流程，再在其上优化与迭代。底层控制核心在接入真机时以动态库形式加入，推进顺序见 [路线图](ws/docs/ROADMAP.md)。

## 目录

仓库分两层：根目录放 Git、编排与基础设施，只在主机上使用；`ws/` 是开发工作区，各容器只挂载其中属于自己的部分。

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

容器里的 `/workspace` 只有该容器用到的目录，跨容器的协作由编排器负责；Git 操作在主机上进行。模块约定与挂载规则见 [开发指南](ws/docs/DEVELOPMENT.md)。

## 容器

| 镜像 | 内容 | 用途 |
|---|---|---|
| `dev` | Ubuntu 24.04、ROS 2 Jazzy、RViz、Clang 20 / CMake / GDB、学习沙盒依赖 | ROS 与 C++ 开发、RViz |
| `sim` | Isaac Sim 6.0.1 / Isaac Lab / Arena 0.3.0（Python 3.12），Isaac 自带 Jazzy bridge | 仿真、GUI、RL 训练、评估、数据转换 |
| `policy` | GR00T N1.6（Python 3.10、Torch 2.7.1 + CUDA 12.6、FlashAttention） | 模型推理服务、微调、自研模型 |

主机只需要 Linux x86_64、Docker / Compose、NVIDIA 驱动与 NVIDIA Container Toolkit；GUI 另需 X11 与可读的会话 Xauthority。Python 包只通过 Dockerfile 与锁文件进入镜像，不在容器里手工安装。

在 Linux 主机终端进入仓库：

```bash
./scripts/lab prepare         # 创建 output 目录与 .env
./scripts/lab build           # 构建 dev / sim / policy
./scripts/lab help            # 全部入口
```

也可以直接拉取已发布的私有镜像（当前 `v0.1.0`），免去本地构建：先 `docker login ghcr.io`，在 `.env` 写入 `IMAGE_PREFIX=ghcr.io/chanc313/robotics-lab` 与 `IMAGE_TAG=v0.1.0`，再执行 `./scripts/lab pull`。

运行 Isaac 前，本人接受 Isaac Sim 许可后，在 `.env` 取消注释 `OMNI_KIT_ACCEPT_EULA=YES`、`ACCEPT_EULA=Y`。VS Code 用户在 **Dev Containers: Reopen in Container** 中选择 dev、sim 或 policy 配置。

常用入口：

```bash
./scripts/lab ros-shell       # ROS / C++ 开发 shell
./scripts/lab sim-gui         # 持续保留 Arena GUI
./scripts/lab rviz            # RViz
./scripts/lab train           # Isaac Lab RL 训练（默认短 Cartpole）
./scripts/lab policy-server   # GR00T G1 推理服务
./scripts/lab g1-evaluate     # G1 闭环评估，连接已运行的推理服务
```

这些入口提供启动方式，不代表对应流程已经验收；当前进度见 [路线图](ws/docs/ROADMAP.md)。

## 文档

- [容器指南](ws/docs/CONTAINERS.md)：构建、IDE、启动、跨容器通信、数据与缓存、镜像发布
- [开发指南](ws/docs/DEVELOPMENT.md)：模块约定、依赖规则、接口与测试的时机
- [路线图](ws/docs/ROADMAP.md)：闭环推进顺序与已定的长期决定
- [学习沙盒工具链](ws/docs/TOOLCHAIN.md)：`cppsrc/`、`pythonsrc/`、`rossrc/`
- 学习材料：[G1 Demo 学习计划](ws/docs/LEARNING_PLAN.md)、[核心理论](ws/docs/CORE_CONCEPTS.md)、[ROS 2 入门](ws/docs/ROS_BASICS.md)、[Isaac GUI 与 policy_runner](ws/docs/ISAAC_GUI_AND_POLICY_RUNNER.md)、[项目启动与第一阶段](ws/docs/PROJECT_START.md)
- [历史记录](ws/docs/archive/)：环境检查、驱动诊断、容器迁移、骨架审查

许可证：[LICENSE](LICENSE)。
