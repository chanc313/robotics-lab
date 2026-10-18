# 容器迁移与骨架复审

此文件是迁移检查历史记录；之后 `src/control` 已移除、学习入口移到顶层，现状以 [开发指南](../DEVELOPMENT.md) 与 [路线图](../ROADMAP.md) 为准。按用户后续要求，当前配置已精简为 `dev`、`sim`、`policy` **三个镜像**：原生嵌入式 C++ 控制源码保留在 `src/control`，使用 `dev` 的现有工具链；ROS GUI 合入 `dev`，Isaac GUI 继续使用 `sim`。旧的独立 `control` / `gui` 镜像与四套 IDE 方案已淘汰，`interfaces` 占位目录和独立架构文档已移除。当前架构见 [开发指南](../DEVELOPMENT.md)。

## 本轮精简状态

| 项目 | 状态 |
|---|---|
| 镜像与入口 | 统一为 `dev` / `sim` / `policy`；控制使用默认开发环境，GUI 不独立建镜像 |
| 新 `dev` / RViz 安装检查 | 合并镜像构建完成；rclpy / debugpy、ROS 示例包 / RViz / rosdep、Clang 20 / CMake / Ninja / GDB 安装检查通过；同一镜像中 RViz 空窗口启动、OpenGL 4.6 初始化与正常关闭返回 0 |
| `sim` / `policy` | 以下保留先前安装检查事实；本轮不改变对应框架依赖 |
| 目录与工具链 | 删除 control 容器配置、interfaces 占位与 AI 空目录的 Ruff 预设；libc++ 限定到原有学习目标 main，不再通过环境变量影响所有 C++ 构建 |
| 静态复核 | 三服务 Compose / GUI / IDE 配置、JSON、Bash / Python 语法、文档链接与 diff 空白检查通过；开发镜像没有全局 CXXFLAGS，也没有挂入 Isaac 环境 |

本轮日志与三个镜像标识在 `output/runs/setup/2026-10-11/container-simplification/`。仅验证安装与 GUI，无完整通信、控制或训练闭环测试；旧 control / gui 镜像标签已移除。

后续按用户删除决定移除了预构建镜像覆盖文件的全部 IDE 引用；当前三份开发配置直接使用 `compose.yaml`，不再禁用 IDE 镜像构建。以下历史记录中的“取消 IDE 自动构建”不适用于当前配置。

以下内容记录精简前的五镜像迁移，不作为当前目录与命令要求。

2026-10-11。验收范围：全面容器化配置、模块解耦、目录与依赖边界、框架安装。按用户澄清，允许安装检查，不测试未实现的通信、Python / C++ 数据交互或完整训练闭环。

## 骨架调整

| 项目 | 调整与结论 |
|---|---|
| 模块 | 新增 `src/ai`、`src/ros`、`src/control`、`src/simulation`，分别说明职责与依赖禁区 |
| 控制环境 | 独立 `control` 镜像；无 ROS / Isaac / 模型 SDK，未引入真机设备或 PWM 实现 |
| 实验层 | `experiments/arena_g1` 保存当前 G1 / GR00T 配置，不作为通用模块默认行为 |
| 接口层 | `interfaces` 仅定义设计边界；没有伪造消息、空业务节点或宣称通信已实现 |
| 容器 | ROS、仿真、AI、控制与可选 RViz 独立；Python 3.12 / 3.10 和 Torch 环境不混用 |
| 开发入口 | 四种 Dev Container 使用已构建 / 拉取镜像，取消 IDE 自动构建；关闭 IDE 不自动关闭全项目服务 |
| 存储 | `output/storage` / `output/runs` 与各环境缓存分开，容器退出后结果保留 |
| 分发 | 支持 `IMAGE_PREFIX` / `IMAGE_TAG` 与 build / publish / pull；尚未推送镜像 |
| 工具链 | 原有 C++ / Python 学习代码保留，退出业务公共依赖；C++26 不约束 ROS 与控制模块 |
| 文档 | README 改为当前架构；原生环境检查归档，GUI 命令改为容器入口 |
| 依赖纯净 | GR00T 完整包仅在 Python 3.10 模型镜像安装；G1 入口单独引用客户端源码，仿真环境不忽略 Python 要求强装整包 |
| 构建修正 | 隔离模型 uv 缓存，避免并行构建锁超时；Isaac Jazzy 路径改为 6.0 的 `isaacsim.ros2.core` |
| 镜像层与缓存 | 由开发用户直接安装大型依赖，避免整份 venv 的 chown 复制层；Kit 配置、缓存、日志持久化；模型 uv 环境路径只用于构建期 |
| 构建上下文 | 移除全局 `models` / `data` / `datasets` 排除项，避免误排除未来模型源码；大数据统一由 `output` 排除 |
| 路线清理 | 仿真镜像移除当前不用的 `openpi-client` / `simready-search`；对应未来路线需独立处理依赖 |
| GPU 驱动 | 移除镜像手工添加的 Vulkan ICD，使用 NVIDIA Container Toolkit 注入的唯一清单，避免 GPU 重复枚举 |

当前目录是开发骨架，不表示已经实现自研模型、ROS 通信层或电机控制服务。官方 Arena / GR00T / G1 WBC 保持固定上游基线。

## 框架安装状态

| 环境 | 状态 |
|---|---|
| `dev` / ROS | 镜像构建完成，rclpy / debugpy / ROS 示例包 / rosdep 安装检查通过 |
| `control` | 镜像构建完成，GCC 13.3、CMake 3.28.3、Ninja、GDB、Python debugpy 检查通过 |
| `gui` | 镜像构建完成；此前容器 RViz 启动与 OpenGL 4.6 初始化通过，无业务通信 |
| `sim` | 镜像构建完成；Python 3.12.15、Isaac Sim 6.0.1.0、Isaac Lab / Arena、RSL-RL、Gymnasium、pandas、GR00T 客户端源码导入与 CUDA 小算子通过；无界面及 X11 GUI 空 Kit 启动与默认退出均返回 0，GPU 唯一枚举为 RTX 4080；依赖元数据有下述两项上游例外 |
| `policy` | 镜像构建完成；Python 3.10.19、Torch 2.7.1+cu126、Gymnasium 1.2.2、pandas 2.2.3、GR00T / DeepSpeed 导入通过；CUDA 与 FlashAttention 小算子通过；124 个包的依赖一致性与官方推理 / 微调 CLI 帮助检查通过；最终镜像非 root 权限与环境隔离复查通过 |

静态复核：Bash 语法、编辑器 JSON、基础 / GUI / 控制 Compose 配置和 `git diff --check` 通过。没有运行完整通信或 RL 训练测试。

检查入口：`scripts/lab check-installation ros|control|sim|policy`。它只检查工具版本、依赖导入、CUDA 小张量 / FlashAttention 算子、空 Kit 启动；不加载模型权重、不创建 ROS 图或训练环境。

日志放本仓库 `output/runs/setup/2026-10-11/container-migration/`，不进入 Git。迁移前主机检查只保留在 [历史记录](ENVIRONMENT_CHECK_2026-10-11.md)，不作为容器安装证明。

## 仿真依赖的上游例外

固定 Arena 提交的 `pyproject.toml` 使用 `override-dependencies`，原始锁安装后 `uv pip check` 曾报告五项元数据冲突。当前不使用 OpenPI 或资产搜索，移除 `openpi-client` / `simready-search` 后剩余两项：

| 包的声明 | 实际安装 | 上游覆盖原因 |
|---|---|---|
| Isaac Lab：`coverage==7.6.1` | `7.4.4` | Isaac Sim 固定 7.4.4；coverage 是测试工具 |
| Isaac Sim kernel：`websockets==12.0` | `16.1.1` | Arena 固定 16.1.1，以兼容要求 >=14 的 Isaac Teleop CloudXR |

原因来自 [固定提交的官方配置](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/pyproject.toml)。本项目没有改写包元数据来消除报告，也没有验证 CloudXR 或这些版本的全部行为。保留原始 `sim-dependencies.log`；当前只能声明安装可用与依赖环境隔离，不能声明仿真依赖元数据零冲突。后续升级上游时重新审查这些覆盖规则。

额外检查曾使用 `fast_shutdown=False`：框架启动、导入与扩展卸载完成后，在 Python 进程退出阶段发生段错误，返回 139。日志保留为 `sim-shutdown-graceful.log`；切回 [Isaac 官方默认退出方式](https://docs.isaacsim.omniverse.nvidia.com/latest/py/source/extensions/isaacsim.simulation_app/docs/index.html) 后，无界面检查返回 0。尚未确认完整卸载崩溃的根因，不能声称该路径已修复。安装检查按默认运行方式验收，异常导入使用非零退出状态。

## 后续阶段

1. 选择镜像 registry / 版本并发布，才能进行新 Linux 机器的纯拉取验收；本机五个镜像已构建并记录标识。
2. 通信阶段定义单位、坐标系、关节顺序、时间与失效语义，添加实际适配代码与链路验收。
3. 准备官方 G1 权重，记录显存和任务配置，再运行模型推理闭环。
4. 添加自研模型 / 控制 / RL 实验及对应业务测试。

主机框架未删除，旧的正在使用的 Dev Container 未停止或重建；在 VS Code 执行 Rebuild Container 才应用新开发镜像。当前未自动下载权重、推送镜像或运行 G1 闭环。
