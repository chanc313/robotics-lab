# policy 容器：模型推理与训练

> 本文件在容器里显示为 `/workspace/README.md`（只读挂载），源文件在主机仓库的 `.devcontainer/policy/README.md`，修改请在主机上进行。

## 定位

一个独立、内部闭环的模型容器：不依赖 dev 与 sim，自己就能加载模型、提供推理服务、微调和开发新模型。它目前服务于 G1 项目（见最后一节），也可以单独拿到其他项目中复用。与其他容器只通过数据交互：共享的 `/data`（权重、数据集）、`/runs`（训练产物）和网络端点（推理服务）。

## 镜像内容

| 类别 | 内容 |
|---|---|
| 模型框架 | Isaac-GR00T N1.6（固定提交 `e29d8fc`），源码在 `/opt/arena/submodules/Isaac-GR00T` |
| 深度学习 | PyTorch 2.7.1 + CUDA 12.6、FlashAttention 2.7.4、DeepSpeed、Transformers |
| 数据 | LeRobot 格式读取、pandas、视频解码 |
| Python | 3.10.19，环境在 `/opt/policy-venv`，依赖由 `docker/policy/uv.lock` 锁定 |

## 闭环功能与自检

以下入口在主机执行（`scripts/lab` 会启动本容器）；在 VS Code 的 policy 窗口里，也可以直接在终端运行对应的 `python` 命令：

| 功能 | 回路 | 自检 |
|---|---|---|
| 安装与 GPU | CUDA 张量运算、FlashAttention 算子 | `./scripts/lab check-installation policy` |
| 推理服务 | 客户端请求 → 模型推理 → 返回动作块 | 一个终端 `./scripts/lab policy-server`，另一个终端 `./scripts/lab policy-ping`（服务端与客户端都在本容器内）；需要先把权重下载到 `/data/models/` |
| 训练与微调 | 数据 → 训练 → checkpoint → 推理服务 | `./scripts/lab policy-train` 无参数时显示官方帮助；完整微调需要数据集和更大显存的 GPU，尚未在本机运行 |
| 离线评估 | 数据集 → 模型预测 → 与真实动作对比 | GR00T 自带示例数据 `demo_data/` 与 `gr00t/eval/open_loop_eval.py`，尚未在本机运行 |

推理一个 3B 模型约占 6 GB 显存。

## 工作区与挂载

| 路径 | 内容 |
|---|---|
| `/workspace/docs` | 项目文档（三个容器共享） |
| `/workspace/src/ai` | 项目的模型与算法模块 |
| `/workspace/experiments` | 实验组合配置（与 sim 共享） |
| `/workspace/.vscode` | 本容器的 VS Code 设置与调试配置 |
| `/data`、`/runs` | 共享的权重、数据集与运行记录 |
| `/opt/ruff` | 共享 Ruff 规则（只读） |

Hugging Face、Triton、CUDA 编译缓存保存在命名卷中。只往挂载目录写文件；容器里没有 `.git`，Git 在主机上操作。

## 组成文件（单独复用时需要带走）

- `docker/Dockerfile.policy`、`docker/policy/pyproject.toml` 与 `uv.lock`、`docker/fetch_arena.sh`、`docker/versions.env`、`docker/check_installation.py`
- `compose.yaml` 中的 `policy` 服务、`policy-cache` 卷及 `x-build-args`
- `.devcontainer/policy/`（`devcontainer.json`、`vscode/`、本文件）、`.devcontainer/compose.devcontainer.yaml` 中的 `policy` 部分、`.devcontainer/ruff/`
- `scripts/lab` 中的 `policy-shell`、`policy-train`、`policy-server`、`policy-ping`、`check-installation policy` 入口

## 目前在 G1 项目中的角色

加载官方 G1 微调权重 `nvidia/GN1x-Tuned-Arena-G1-Loco-Manipulation`（revision `gn1_6`，放在 `/data/models/arena-g1/checkpoint-20000`），在 `127.0.0.1:5555` 提供推理服务，为 sim 中的 G1 任务返回每次 50 步的动作块。
