# Robotics lab

Linux 上 C++ / Python 软件开发的通用起点。保留构建、依赖、编辑器配置与空源码目录；没有业务代码、安装脚本、测试脚本或预设服务。

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

## 可选 ROS / Gazebo 容器

Dockerfile 来自仓库已有历史，以 ros:jazzy-ros-base-noble 为基础，安装 ROS C++ demo 节点和 ros-gz。它是独立的 ROS/Gazebo 容器入口，没有配置完整的 CMake/uv/Isaac 开发环境；本机开发不依赖它。本轮没有构建或验收此镜像。

```bash
docker build -t robotics-lab:ros-jazzy .
docker run --rm -it robotics-lab:ros-jazzy
```

仓库沿用已有 MIT 许可证，见 LICENSE。
