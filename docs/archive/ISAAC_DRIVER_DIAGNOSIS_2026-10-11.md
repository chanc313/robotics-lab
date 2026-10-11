# 历史：Isaac GUI 故障诊断

本记录为迁移前故障；当前驱动已恢复，项目运行使用容器。

## 1. 为什么这次看不到 GUI

以下是容器迁移前的历史故障说明，驱动重启后已恢复。

**首先，NVIDIA 驱动与用户态库版本不一致，RTX 渲染器初始化失败。** 本次日志包含 `NVML_ERROR_LIB_RM_VERSION_MISMATCH`、`No device could be created` 和无效的 Hydra 渲染上下文。系统只读检查如下：

| 检查项 | 2026-10-11 实际结果 |
|---|---|
| 当前加载的内核驱动 `/proc/driver/nvidia/version` | `595.91.07` |
| 磁盘上的内核模块 `modinfo -F version nvidia` | `595.99.02` |
| NVML 库 `libnvidia-ml.so.1` 的真实目标 | `libnvidia-ml.so.595.99.02` |
| 主机 `nvidia-smi` | `Failed to initialize NVML: Driver/library version mismatch`，退出码 18 |
| 当前桌面会话 | X11，`DISPLAY=:1` |

这些证据说明磁盘上的驱动已经更新，当前系统仍加载旧模块。优先处理是**保存工作后重启电脑**，让内核加载已安装的新模块。此次没有重新安装驱动，也没有代你重启。NVIDIA 官方将错误码 18 定义为驱动与库版本不匹配，见 [NVML 错误定义](https://docs.nvidia.com/deploy/archive/R550/nvml-api/group__nvmlDeviceEnumvs.html)。

重启后，在 Linux 主机终端执行：

```bash
nvidia-smi
cat /proc/driver/nvidia/version
modinfo -F version nvidia
```

先确认 `nvidia-smi` 能列出 RTX 4080 Laptop，加载的模块与磁盘模块版本一致，再启动 GUI。若仍有错误，保留输出继续定位。之后的原生 GUI 验收见历史记录；当前项目改用容器入口。

**其次，policy_runner 跑完指定步数会主动关闭环境和应用。** 你这次的 1500 步已完成，日志随后进入关闭流程。即使驱动正常，有限预算结束后窗口也不会一直保留。增加步数只会延长实验时间。

当前版本没有 `--keep_open` 参数；`--serve_evaluation_report` 启动的是 HTML 报告服务，调用前环境已经关闭，不能用它保留交互仿真。

