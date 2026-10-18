# 学习沙盒工具链

`cppsrc/`、`pythonsrc/`、`rossrc/` 是独立的 C++、Python、ROS 2 学习沙盒，`src/` 下的项目模块不依赖它们。三者都在 `dev` 容器中构建和运行（VS Code 的 dev 配置，或 `./scripts/lab ros-shell`），位于 `/workspace` 下；构建产物统一放在 `/build`（主机 `output/build`），不会出现在工作区里。

## C++：`cppsrc/`

`cppsrc/` 是独立的 CMake 项目，需要 CMake ≥ 3.24、Ninja 和支持 `-std=c++2c` 的编译器。`dev` 镜像提供 Clang 20 + libc++、GDB，并设置 `CXX=clang++-20`、`DEBUGGER=gdb`；镜像没有全局 `CXXFLAGS`，C++26 与 libc++ 只作用于学习目标 `main`，不影响 ROS 包。C++26 的实际支持程度取决于编译器与标准库版本。

```bash
# Debug
cmake -S cppsrc -B /build/cppsrc/Debug -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build /build/cppsrc/Debug --target main
/build/cppsrc/Debug/bin/main

# Release
cmake -S cppsrc -B /build/cppsrc/Release -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build /build/cppsrc/Release --target main
/build/cppsrc/Release/bin/main
```

两种模式使用独立构建目录，切换时无需清理。Debug 保留调试信息、通常不优化；Release 启用优化并通常定义 `NDEBUG`，不要让程序逻辑依赖 `assert` 的副作用。新增源码需要在 `add_executable` 中显式列出，CMake 不自动扫描。

VS Code：

- Ctrl+Shift+B 运行默认任务 `C++: build (Debug)`；`C++: build (Release)` 在 **Tasks: Run Task** 中。两个任务直接调用 `cmake`，不依赖 CMake Tools，因此在 sim / policy 容器中打开同一仓库也不会报缺少 `cmake` 任务类型。
- Run and Debug 选择 `C++: main (Debug)`，F5 先构建再用 GDB 调试。
- CMake Tools 只负责为 C/C++ 扩展提供编译配置（IntelliSense），打开 dev 容器时会自动配置 `/build/cppsrc/Debug`。`CMake: Select a Kit` 选择 `[Unspecified]`，让 CMake 从 `CXX` 选择编译器。
- 不要用 C/C++ 扩展的“构建活动文件”，它绕过 CMake 的标准与头文件设置。
- 更换编译器或标准库后删除对应的 `/build/cppsrc/<模式>` 目录再构建。

## Python：`pythonsrc/`

`pythonsrc/` 是独立的 uv 项目（扁平布局，包名 `robotics_lab`），要求 Python ≥ 3.12。它的依赖（Ruff、debugpy、ipykernel，以及 `science` 可选组的 numpy、matplotlib）在构建 `dev` 镜像时安装到 `/opt/learning-venv`；源码通过 `.pth` 直接从 `/workspace/pythonsrc` 导入，修改即时生效。

```bash
uv run python -m robotics_lab
uv run ruff check --config /opt/ruff/ruff.toml .
uv run ruff format --config /opt/ruff/ruff.toml .
```

`dev` 镜像设置了 `UV_PROJECT=/workspace/pythonsrc` 与 `UV_NO_SYNC=1`，`uv run` 在任意目录都使用学习环境，并且不会在运行时安装任何东西。这个环境不在 `PATH` 中，`dev` 的 `python3` 始终是带 ROS 依赖的系统 Python。

VS Code 默认解释器为 `/opt/learning-venv/bin/python`，终端不自动激活虚拟环境。若编辑器保存过旧选择，执行 `Python: Select Interpreter` 重新选择。

修改依赖：编辑 `pythonsrc/pyproject.toml`，执行 `uv lock --project pythonsrc`，然后重建 `dev` 镜像。Ruff 规则在主机 `.devcontainer/ruff/ruff.toml`，只读挂载为 `/opt/ruff/ruff.toml`，三个容器共用。

## ROS 2：`rossrc/`

`rossrc/` 是一个 colcon 工作区的源码根，包含最小的跨语言收发示例：

| 包 | 构建类型 | 内容 |
|---|---|---|
| `hello_cpp` | ament_cmake | `talker`：以 `rate_hz`（默认 2）在 `/hello` 发布 `std_msgs/String` |
| `hello_py` | ament_python | `listener`：订阅 `/hello`，参数 `max_messages > 0` 时收满即退出；`hello.launch.py` 同时启动两者，listener 退出时整体结束 |

ROS 包使用系统 Python 与 libstdc++、C++17，与 `cppsrc/` 的 libc++ / C++26 设置无关。构建产物放 `/build/rossrc`，`--symlink-install` 让 Python 与 launch 文件的修改无需重新构建：

```bash
colcon --log-base /build/rossrc/log build --base-paths rossrc \
  --build-base /build/rossrc/build --install-base /build/rossrc/install --symlink-install
source /build/rossrc/install/setup.bash

ros2 launch hello_py hello.launch.py max_messages:=5   # 自检：收发 5 条后退出，返回 0
ros2 launch hello_py hello.launch.py                   # 持续运行，Ctrl+C 结束
```

也可以在两个终端分别运行 `ros2 run hello_cpp talker`、`ros2 run hello_py listener`，再用 `ros2 node list`、`ros2 topic info /hello`、`ros2 topic echo /hello` 观察。VS Code 任务 `ROS sandbox: build` 与 `ROS sandbox: self-check` 执行同样的命令；默认 Dev Container 为 C/C++ 扩展加入了 `/opt/ros/jazzy/include`，ROS 头文件可以被识别。

这里只验证 `dev` 容器内的 ROS 通信；与 `sim`、`policy` 的连接属于路线图后续步骤。项目自己的 ROS 包放 `src/ros`，构建到 `/build/ros`。
