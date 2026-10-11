# 开发指南

目录总览见 [README](../README.md)，容器的进入与运行方式见 [容器指南](CONTAINERS.md)，阶段安排见 [路线图](ROADMAP.md)。

## 模块约定

`src/` 只放项目开发源码。每个子目录是一个独立模块，自带依赖声明与构建文件，不共用根目录的 CMake 或 Python 包。

| 模块 | 职责 | 容器与构建 |
|---|---|---|
| `src/ai` | 模型结构、推理、模仿学习与 RL 算法、训练配方 | `policy`；新模型需要不同环境时另建镜像 |
| `src/ros` | ROS 2 包、节点、编排、消息适配 | `dev`；colcon 源码根，产物放 `output/ros` |
| `src/simulation` | Isaac 任务与场景、传感器、奖励与结束条件、Gymnasium 环境、仿真适配 | `sim` |

- 模块之间不导入彼此的内部实现。AI 不导入 ROS 或 Isaac 运行时；ROS 适配器只做消息转换与调用；仿真场景不依赖特定模型的内部代码。
- RL 算法属于 AI，Isaac 环境适配属于 simulation。需要同进程向量化训练时，可以在 `sim` 镜像中安装算法包，源码边界不变。
- 当前实验的组合（任务、策略配置、机器人适配、端点）放 `experiments/<实验名>`，不写进通用模块。现有实验为 `arena_g1`。
- 没有实际代码的模块只保留职责说明，不为补目录创建空节点、空消息包或占位服务。新模块（例如真机阶段的控制核心）在开始编写时再建立。
- `cppsrc/`、`pythonsrc/` 是学习沙盒，`src/` 模块不依赖它们，见 [学习沙盒工具链](TOOLCHAIN.md)。

## 依赖规则

**Python 包只通过 Dockerfile 与锁文件进入镜像。** 新增或升级依赖时，先讨论放在哪个镜像、怎样安装，再修改对应文件并重建镜像；不在容器终端里 `pip install` 或 `uv sync`。

| 环境 | 依赖声明 | 安装位置 |
|---|---|---|
| `sim` | 上游 Arena 的 `uv.lock`（固定提交，`--frozen`），少量补充包写在 `docker/Dockerfile.sim` | `/opt/arena/.venv` |
| `policy` | `docker/policy/pyproject.toml` 与 `uv.lock` | `/opt/policy-venv` |
| `dev`（ROS） | apt 包写在 `docker/Dockerfile.dev`，ROS 包的系统依赖同时写进各包的 `package.xml` | 系统 Python `/usr/bin/python3` |
| `dev`（学习沙盒） | `pythonsrc/pyproject.toml` 与 `uv.lock` | `/opt/learning-venv` |

自有模块的源码在运行时绑定挂载，不安装进环境。需要让某个环境导入 `src/` 下的 Python 模块时，在对应 Dockerfile 中向该环境写入一个指向 `/workspace/src/<模块>` 的 `.pth` 文件（`dev` 的学习沙盒就是这样接入 `/workspace/pythonsrc` 的）；源码修改即时生效，依赖变化才需要重建。

上游版本统一在 `docker/versions.env` 修改（Arena / Isaac Lab / GR00T 提交、Arena 锁的 SHA-256、两个 Python 版本），共享基础镜像的摘要在 `compose.yaml` 的 `x-build-args` 修改。升级后复核子模块与锁文件，并重新执行 `uv pip check --python /opt/arena/.venv/bin/python`：`sim` 当前有两项已知的上游元数据差异（coverage、websockets，见 [迁移记录](archive/CONTAINER_MIGRATION_2026-10-11.md)），新出现的差异不能忽略。`sim` 安装后移除了当前不用的 `openpi-client`、`simready-search`，未来启用这些路线需要先处理依赖。

ROS C++ 使用 Clang 20 的默认 libstdc++，与 Ubuntu 的 ROS 二进制包一致；学习沙盒的 libc++ 选项只作用于其自身目标。

## 接口与测试的时机

观测、动作、单位、坐标系、关节顺序、时间与失效语义在路线图第 2 步统一写成契约文档，之后再写适配代码；不预建公共接口包。跨模块确需共享的纯接口包，应有独立版本与兼容范围，且不依赖 ROS、Isaac 或模型库。

测试与 CI 在全栈打通后配置。在此之前，验证方式是 `./scripts/lab check-installation ros|sim|policy`（只检查框架安装、导入与 GPU 可用性）以及各阶段的实际运行记录。

## 数据与提交

运行结果和数据放 `output/`（Git 忽略），不提交模型、数据集、缓存或凭据。根目录 `.env` 被忽略，`.env.example` 只是样例。
