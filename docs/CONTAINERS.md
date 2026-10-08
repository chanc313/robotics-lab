# 通用容器开发

## 文件分工

| 文件 | 负责什么 |
|---|---|
| Dockerfile | 安装容器系统工具与编译器，提供非 root 开发用户；没有业务代码或数据库 |
| compose.yaml | 启动 dev 服务，绑定源码目录，管理 Python 环境和编译产物卷 |
| .dockerignore | 排除构建上下文中的虚拟环境、Git 历史、缓存和数据 |
| .devcontainer/devcontainer.json | 让 VS Code 连接 dev 服务，安装开发扩展并执行 uv sync --locked |
| pyproject.toml / uv.lock | 在容器或本机分别重建 Python 依赖 |

原仓库的 ROS Jazzy/Gazebo Dockerfile 已移除，通用镜像不包含 ROS/Isaac。当前仍是无业务逻辑的开发骨架，没有生产服务入口。Dockerfile/Compose/Dev Containers 是声明式开发配置，没有恢复安装脚本或业务脚本。

## 启动与停止

在项目根目录执行：

```bash
docker compose up -d --build dev
docker compose exec dev uv sync --locked
docker compose exec dev bash
```

容器中仍使用 uv、CMake 与相同任务：

```bash
cmake --preset debug
cmake --build --preset debug
# 学习 C++26 时选独立构建模式
cmake --preset debug-cpp26
cmake --build --preset debug-cpp26
```

没有业务目标时，构建不会生成程序。需要科学计算依赖时执行 uv sync --locked --extra science。

```bash
docker compose down
```

正常停止保留命名卷，下次启动可复用环境与编译缓存。down -v 会删除本项目命名卷，重建 Python 环境和编译产物才需要它；后续数据库卷也应独立管理。

## VS Code

已安装 Dev Containers 扩展后，在命令面板选择 Dev Containers: Reopen in Container。VS Code 使用 /workspace，首次创建后执行 uv sync --locked，之后 Ctrl+Shift+B 和 Python: lint 在容器中执行。F5 在出现真实业务入口后再配置。

CLI 构建/运行与命令行 GDB 可验证容器环境；首次 VS Code 界面连接、扩展下载和 GUI 断点需要实际打开后确认。

## 源码与环境隔离

源码从本机绑定到 /workspace，编辑双方看到同一份文件。容器 .venv 被 python-env 命名卷覆盖，output 被 cpp-build 命名卷覆盖；宿主机 .venv 与构建产物不会被容器复用。Git 历史不会进入镜像，但本地开发的绑定挂载包含工作区历史，以便在开发终端使用 Git。

默认开发 UID/GID=1000，与当前宿主用户一致。其他 Linux 用户应在首次构建前设置自己的 UID/GID，例如：

```bash
LOCAL_UID=$(id -u) LOCAL_GID=$(id -g) docker compose up -d --build dev
```

Dev Containers 设置不自动改用户 UID，避免改变已有命名卷的所有权。对已有卷改变 UID 时应同时迁移其权限。

镜像固定 Ubuntu 发布系列和 uv 版本，apt 安全更新随源变化；这不是逐字节完全相同的系统快照。Python 依赖受 uv.lock 控制。[uv 官方 Docker 集成](https://docs.astral.sh/uv/guides/integration/docker/)。

## 以后接入数据库与消息队列

确定实际技术栈后，在 compose.yaml 添加独立 db、cache 或 broker 服务。每项只在真实需要时加入，不提前启动空数据库或放入示例凭据。

- 每个服务使用明确版本的镜像，配置自己的持久卷。
- 程序通过 Compose 服务名连接，例如服务名 db 对应容器内主机 db；localhost 指程序自身所在容器。
- 用 healthcheck 检测真正就绪；需要强制依赖顺序时使用 depends_on 的 service_healthy 条件。仅容器启动不代表数据库可接受连接。[Docker 官方就绪与启动顺序说明](https://docs.docker.com/compose/how-tos/startup-order/)。
- 应用还要支持连接重试，处理服务运行期间的重启。
- 只发布本机或应用实际需要的端口，按需求设置可选 profiles。
- 敏感配置用本地 .env 或 secrets，不进入 Git。数据迁移、备份和恢复属于具体业务设计。

Compose 默认提供本项目网络；当前仅有 dev，没有监听业务端口、数据库或消息队列。未来添加服务时复用这一入口，不需要为每个中间件在宿主机全局安装软件。

## 2026-10-08 验收

通用镜像实际构建完成；dev UID/GID=1000；uv0.12.23 使用系统 Python3.12.3 按原锁安装本地包与开发依赖。普通 GCC/C++20、Clang20/libc++ C++26 实际编译并运行成功；GDB 命中加法断点，读到0.25/0.5，程序正常退出。CMake 两种模式配置通过，Ruff 通过。

容器停止、移除后重新创建，Python 包/开发依赖和构建卷标记仍存在，证明卷持久化。验收后开发容器停止，卷和镜像保留供使用。本轮没有打开 VS Code 容器窗口，也没有安装或验收数据库、消息队列、ROS/Isaac 容器。测试源码只在已移除容器的 /tmp 中，没有提交进仓库。
