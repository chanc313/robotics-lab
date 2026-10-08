# Robotics lab

Linux 上 C++ / Python 软件开发的通用起点。保留构建、依赖、编辑器配置与空源码目录；没有业务代码、安装脚本、测试脚本或业务服务。

```text
include/robotics_lab/       公共 C++ 头文件
src/cppsrc/                   C++ 实现
src/pythonsrc/robotics_lab/    Python 包
.vscode/                   IDE 开发配置
CMakeLists.txt             C++ 构建规则
CMakePresets.json          构建模式
pyproject.toml / uv.lock    Python 项目与依赖锁
```

每个保留文件的用途、复用时需要改哪里，以及构建与调试边界，见 [开发骨架指南](docs/DEVELOPMENT.md)。

## 日常入口

```bash
uv sync --locked
cmake --preset debug
cmake --build --preset debug
```

VS Code 中 Ctrl+Shift+B 执行 C++ 配置和构建；Tasks: Run Task 提供 Python: sync、Python: lint、C++26: build。Python 解释器选择本项目 .venv/bin/python。

当前没有可执行目标，构建成功只说明空骨架可配置，不会运行程序。新增业务入口后再设置 F5 调试配置。科学计算依赖是可选项：需要时执行 uv sync --locked --extra science；普通项目不必安装 NumPy/Matplotlib。

工作站安装历史单独保存在本机 workstation-config 中，不属于本仓库。新项目无需复制机器历史。

## 通用容器开发

Dockerfile 提供 Ubuntu24.04、GCC/CMake/Ninja/GDB、Clang20/libc++、Python3.12 和 uv0.12.23 的开发工具。Compose 管理开发容器、隔离的 Python 环境和编译产物；容器中使用普通 dev 用户。源码绑定挂载，保存即反映到本机。

```bash
docker compose up -d --build dev
docker compose exec dev uv sync --locked
docker compose exec dev bash
```

VS Code 命令面板选择 Dev Containers: Reopen in Container，打开后使用相同的 Ctrl+Shift+B 和 Python 开发配置。容器 .venv 与 output 使用独立命名卷，不混用宿主机对应目录。

```bash
docker compose down
```

停止容器保留卷。更多说明、UID 设置、数据库/消息队列扩展方式见 [容器开发指南](docs/CONTAINERS.md)。原 ROS/Gazebo 专用 Dockerfile 已移除；ROS/Isaac 按未来任务另选专用环境。当前镜像是开发环境，没有生产应用入口。

仓库沿用 MIT 许可证，见 LICENSE。
