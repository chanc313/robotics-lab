# 学习沙盒工具链

`cppsrc/` 与 `pythonsrc/` 是独立的 C++ / Python 学习沙盒，`src/` 下的项目模块不依赖它们。两者都在 `dev` 容器中构建和运行（VS Code 默认 Dev Container，或 `./scripts/lab ros-shell`）。

## C++：`cppsrc/`

`cppsrc/` 是独立的 CMake 项目，需要 CMake ≥ 3.24、Ninja 和支持 `-std=c++2c` 的编译器。`dev` 镜像提供 Clang 20 + libc++、GDB，并设置 `CXX=clang++-20`、`DEBUGGER=gdb`；镜像没有全局 `CXXFLAGS`，C++26 与 libc++ 只作用于学习目标 `main`，不影响 ROS 包。C++26 的实际支持程度取决于编译器与标准库版本。

```bash
# Debug
cmake -S cppsrc -B output/build/Debug -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build output/build/Debug --target main
./output/build/Debug/bin/main

# Release
cmake -S cppsrc -B output/build/Release -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build output/build/Release --target main
./output/build/Release/bin/main
```

两种模式使用独立构建目录，切换时无需清理。Debug 保留调试信息、通常不优化；Release 启用优化并通常定义 `NDEBUG`，不要让程序逻辑依赖 `assert` 的副作用。新增源码需要在 `add_executable` 中显式列出，CMake 不自动扫描。

VS Code：

- Ctrl+Shift+B 运行默认任务 `C++: build (Debug)`；`C++: build (Release)` 在 **Tasks: Run Task** 中。两个任务直接调用 `cmake`，不依赖 CMake Tools，因此在 sim / policy 容器中打开同一仓库也不会报缺少 `cmake` 任务类型。
- Run and Debug 选择 `C++: main (Debug)`，F5 先构建再用 GDB 调试。
- CMake Tools 只负责为 C/C++ 扩展提供编译配置（IntelliSense），打开 dev 容器时会自动配置 `output/build/Debug`。`CMake: Select a Kit` 选择 `[Unspecified]`，让 CMake 从 `CXX` 选择编译器。
- 不要用 C/C++ 扩展的“构建活动文件”，它绕过 CMake 的标准与头文件设置。
- 更换编译器或标准库后删除对应的 `output/build/<模式>` 目录再构建。

## Python：`pythonsrc/`

`pythonsrc/` 是独立的 uv 项目（扁平布局，包名 `robotics_lab`），要求 Python ≥ 3.12。它的依赖（Ruff、debugpy、ipykernel，以及 `science` 可选组的 numpy、matplotlib）在构建 `dev` 镜像时安装到 `/opt/learning-venv`；源码通过 `.pth` 直接从 `/workspace/pythonsrc` 导入，修改即时生效。

```bash
uv run python -m robotics_lab
uv run ruff check .
uv run ruff format .
```

`dev` 镜像设置了 `UV_PROJECT=/workspace/pythonsrc` 与 `UV_NO_SYNC=1`，`uv run` 在任意目录都使用学习环境，并且不会在运行时安装任何东西。这个环境不在 `PATH` 中，`dev` 的 `python3` 始终是带 ROS 依赖的系统 Python。

VS Code 默认解释器为 `/opt/learning-venv/bin/python`，终端不自动激活虚拟环境。若编辑器保存过旧选择，执行 `Python: Select Interpreter` 重新选择。

修改依赖：编辑 `pythonsrc/pyproject.toml`，执行 `uv lock --project pythonsrc`，然后重建 `dev` 镜像。Ruff 规则在仓库根目录的 `ruff.toml`，对 `scripts/`、`src/`、`pythonsrc/` 统一生效。
