# src/ros：中层 ROS

职责：ROS 2 包与节点、任务编排、感知与状态消息、AI 与仿真接口的 ROS 适配。在 `dev` 容器开发（ROS 2 Jazzy + RViz，系统 Python `/usr/bin/python3`）。

- 本目录是独立 colcon 工作区的源码根，构建产物放 `/build/ros`（主机 `output/build/ros`），不在 `/workspace` 根目录运行 colcon。命令见 [容器指南](../../docs/CONTAINERS.md#4-ros-与跨容器通信)。
- 不导入模型或仿真的内部实现；适配器只做消息转换与接口调用。
- 业务消息与 QoS 在项目计划中的接口契约确定后再定义，优先使用标准消息。
- ROS C++ 使用与官方二进制包一致的 libstdc++。

目前没有自有 ROS 包；最小的 C++ / Python 收发示例在学习沙盒 `rossrc/`，见 [学习沙盒工具链](../../docs/TOOLCHAIN.md#ros-2rossrc)。模块约定与依赖规则见 [开发指南](../../docs/DEVELOPMENT.md)。
