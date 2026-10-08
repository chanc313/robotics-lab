# 开发骨架指南

## 适用范围

这是 Linux 上 C++/Python 开发起点，适合原生算法、Python 编排与两者集成。不包含运行时、数据库、Web、ROS 节点或训练框架的业务设计。开发工具已经准备好；具体框架除了安装，还需要项目依赖、接口、构建和运行配置。Windows/macOS 项目需调整工具链、系统路径和编译选项。

## 每一个保留文件

| 文件 | 为什么保留 | 复用到新项目时 |
|---|---|---|
| Dockerfile | 可选 ROS Jazzy/Gazebo 容器配方，沿用已有仓库内容，不等同于本机环境 | 根据实际容器需求调整 |
| .dockerignore | 排除容器构建上下文里的虚拟环境、源码历史和产物 | 按需要调整 |
| LICENSE | 仓库已有 MIT 许可证 | 新项目按作者要求选择许可证 |
| README.md | 项目首页：说明用途、布局与常用命令 | 改项目名称、用途和真实运行入口 |
| docs/DEVELOPMENT.md | 解释骨架与扩展方式，区别环境配置和业务开发 | 理解后可按项目需要精简 |
| CMakeLists.txt | 定义 C++ 工程、产物路径和通用选项接口 robotics_options | 改工程名；为实际源码增加目标，并链接选项接口 |
| CMakePresets.json | 固定 Ninja、Debug 目录与独立 C++26 工具链，避免每次手敲参数 | 按目标平台调整编译器，按需增加 Release；不用 C++26 可删除对应 preset |
| pyproject.toml | Python 包元数据、版本范围、依赖组、包构建后端与 Ruff 规则 | 改名称、描述、Python 范围；添加真实依赖。默认无业务运行依赖 |
| uv.lock | 记录解析后的确切版本、来源和校验信息，供 uv sync --locked 重建 | 依赖未变可直接使用；修改 pyproject 后执行 uv lock 并保存新锁，不手改 |
| .vscode/settings.json | 选择项目解释器、CMake 配置提供者、代码分析、格式化与搜索排除 | 大部分可复用；Linux 工具链/终端路径按平台调整 |
| .vscode/tasks.json | 把 uv/CMake/Ruff 命令连接到 IDE；默认 build 供 Ctrl+Shift+B 使用 | 新目标仍复用同一构建管线，新增实际需求才加任务 |
| .vscode/extensions.json | 推荐 Python、C++、CMake、Ruff、Notebook 与远程开发扩展 | 扩展建议而非自动安装；按所用语言裁剪 |
| .editorconfig | 统一 UTF-8、LF、缩进与末尾空白，兼容不同编辑器 | 通常原样复用，不依赖 VS Code |
| .gitignore | 排除虚拟环境、构建产物、缓存、实验数据和 .env，保持源码仓库干净 | 按项目增删。不要存放密码；可重建依赖不提交 |
| src/pythonsrc/robotics_lab/__init__.py | 空包声明，使模块可作为包被 uv 可编辑安装；没有业务逻辑 | 包目录与项目名规范化后的名称保持一致，或设置 module-name |
| src/cppsrc/.gitkeep | Git 不记录空目录，空占位保留原生源码位置 | 有真实源码后可删 |
| include/robotics_lab/.gitkeep | 同上，保留公共头文件目录 | 有真实头文件后可删 |

.vscode、.editorconfig、.gitignore、.gitkeep 为隐藏内容，使用 tree -a 查看；排除 .venv 和 .git 可用 tree -a -I '.venv|.git|__pycache__'。

## 配置的边界

CMake 的 robotics_options 是 INTERFACE 目标：只提供编译选项、头文件目录和语言模式，不编译库、不产生可执行文件。普通 debug 使用 C++20；debug-cpp26 使用 Clang20、-std=c++2c 和 libc++，只支持该编译器已实现的 C++26 特性。两个产物目录分开。

真正新增 C++ 程序时，需要在 CMakeLists.txt 中显式注册，例如：

```cmake
add_executable(my_app src/cppsrc/main.cpp)
target_link_libraries(my_app PRIVATE robotics_options)
```

这只是扩展说明，骨架中没有 main.cpp 或 my_app。CMake 不会自动扫描所有 cpp；有实际编译目标后才生成可用的 compile_commands.json。VS Code 通过 CMake Tools 获取选中模式的分析配置。

Python 使用 uv_build 进行纯 Python 包安装；本地源码 editable 安装到 .venv，不需要手工 PYTHONPATH。它不会顺便编译、安装或打包 C++ 库。以后要发布包含原生库的 Python 包，再选适合原生扩展的打包方式。

Python3.12 是当前基线，不是未来所有项目的要求。改变 requires-python 时，同时调整 Ruff target-version，并为新项目选择对应解释器。dev 组保留 Ruff、debugpy 和 ipykernel，用于检查、调试与 Notebook；science 是可选的 NumPy/Matplotlib，不默认启用。

## 复用到新项目

1. 复制可见配置、隐藏配置和源码目录；不复制 .git、.venv、output、缓存或机器安装历史。
2. 修改 CMake project、选项/目标名称、pyproject 项目名及 Python/头文件命名空间。项目名 new-project 默认对应 Python 包 new_project；不要只改文件夹名称。
3. 修改依赖后运行 uv lock，再 uv sync --locked；新项目得到独立 .venv。
4. 在项目根目录执行 cmake --preset debug 和 cmake --build --preset debug，或 Ctrl+Shift+B。
5. 添加真实程序与测试；有入口后才创建 .vscode/launch.json。没有业务进程时无需空的 launch.json。
6. 初始化自己的 Git 历史，按项目选择远端、许可证、CI 与发布方式。

纯 Python 项目可以删 CMake 文件、include、src/cppsrc 和对应 C++ IDE 配置；纯 C++ 项目可以删 Python 包、pyproject/uv.lock 和对应 Python IDE 配置。骨架可裁剪，不要求每个项目同时用两种语言。

## 框架接入

新增 ROS 自有节点采用 ros_ws/src/<包名> 和标准 colcon 包布局；ROS 与 Isaac 使用各自环境，不把依赖无条件混入根 .venv。Web、数据库或容器同样按业务增加配置；不因为工具已安装就自动添加服务。

安装、磁盘、备份、源密钥和验收记录属于 workstation-config；它们已归档，不占用通用项目骨架。skills 空目录、空 launch.json、验收文档副本和本机 Isaac 绝对路径设置均已从骨架移除。
