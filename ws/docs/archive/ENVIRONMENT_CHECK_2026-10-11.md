# 历史：重启后环境复核

此记录保留迁移前的主机环境事实，不作为当前项目启动方式。当前架构见 [开发指南](../DEVELOPMENT.md)，容器迁移历史与本轮精简状态见 [迁移记录](CONTAINER_MIGRATION_2026-10-11.md)。

日期：2026-10-11，Australia/Sydney。用户要求确认环境后开始学习。

## 结果

基础 Isaac / Arena 学习环境可用。此次复核没有验收 G1 / GR00T 任务模型，也未通过截图核对用户看到的具体画面；GUI 视角与交互作为动手学习的提交项。

| 检查 | 实际结果 |
|---|---|
| NVIDIA 驱动 | 加载模块、磁盘模块、NVML 均为 `595.99.02`；`nvidia-smi` 正常 |
| GPU | RTX 4080 Laptop，12282 MiB |
| Torch 主机 CUDA 检查 | `cuda_available=True`，能识别 GPU；4×4 矩阵运算及同步完成，结果总和 `3680.0` |
| Python / 安装包 | Python 3.12.15；Sim 6.0.1.0；Lab 6.1.17；Arena 0.3.0；Torch 2.11.0+cu128 |
| ROS 2 | 加载 Jazzy 环境后，`rviz2` 包和 `rclpy` 可找到；本次未重复消息或时钟桥接验收 |
| Arena 固定版本 | `8737b4ceb25f99f81a81786b7fde73139b52f324`，工作树干净 |
| 子模块与锁文件 | 与 [项目启动](PROJECT_START.md) 的固定值一致 |
| GUI / GPU 物理检查 | Vulkan 中 NVIDIA GPU 标记 Active；Kit 应用启动完成；cuda:0 环境运行 200/200 步；进程退出码 0 |
| 错误扫描 | `[Error]`、`Traceback`、NVML 版本不匹配、设备创建失败的匹配数均为 0 |

初次在文件访问沙箱内检查 Torch 时返回 CUDA 不可用；在主机权限下复核成功。真实 GPU 与桌面运行检查使用主机权限。

## 命令与产物

从 `/home/channing/projects/vendor/IsaacLab-Arena` 执行：

```bash
OMNI_KIT_ACCEPT_EULA=YES ACCEPT_EULA=Y ./.venv/bin/python isaaclab_arena/evaluation/policy_runner.py --viz kit --policy_type zero_action --num_steps 200 --output_base_dir /tmp/robotics-lab-gui-check-2026-10-11 cube_goal_pose
```

完整日志与报告已从临时目录归档到本仓库忽略的 `output/runs/setup/2026-10-11/`：

- [完整 GUI 日志](/home/channing/projects/robotics-lab/output/runs/setup/2026-10-11/arena-gui-200.log)
- [HTML 报告](/home/channing/projects/robotics-lab/output/runs/setup/2026-10-11/arena-gui-200/2026-10-11_14-59-01/index.html)

Kit 初始化约 92 秒，200 个控制步约 33 秒；本次完成 episode 数为 0。空样本的 `object_moved_rate=NaN` 不用于判断任务能力。

日志仍有上游扩展、弃用、渲染间隔等警告，均保存在完整日志中；未阻止本次运行。CPU 电源配置为 powersave，本次墙钟性能不作为后续性能基线。此次未修改系统电源配置或上游源码。

## ROS 开发容器增补验证

同日按用户要求，将 ROS 2 Jazzy Base、ros-dev-tools、C++ / Python 示例及系统 debugpy 加入开发镜像，初始化 rosdep 系统源配置。`robotics-lab-dev` 镜像构建成功；Compose 配置检查通过。最终镜像 ID：`sha256:d6a95b23f2febce20652af4fe8698708a7875377214c9e1283005c3b36d0e3c9`。

- `/opt/ros/jazzy` 下示例包可找到，系统 Python 能导入 `rclpy` 和 `debugpy`；colcon、rosdep 可用。
- 交互 Bash 自动加载 ROS；开发用户为 UID / GID 1000。
- 临时容器内 C++ talker → Python listener 通信通过。
- 同一发布者 → 主机 Python listener 通信通过。
- 通信验证使用主机网络、Fast DDS UDPv4、`ROS_DOMAIN_ID=71` 与独立 topic `/robotics_lab_container_check/chatter`。只清理此次启动的临时容器与节点。

日志：

- [容器示例通信](/home/channing/projects/robotics-lab/output/runs/setup/2026-10-11/ros-container/container-demo.log)
- [主机订阅者](/home/channing/projects/robotics-lab/output/runs/setup/2026-10-11/ros-container/host-listener.log)

此次验证覆盖 ROS 基础环境与消息通信，尚未新增自有 ROS 包或复核容器节点到 Isaac 桥接的链路。用户当前已运行的旧 Dev Container 未被停止或重建；需在 VS Code 执行 `Dev Containers: Rebuild Container` 应用新镜像。
