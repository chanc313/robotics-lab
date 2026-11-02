# src/simulation：Isaac 仿真

职责：Isaac Sim / Lab / Arena 场景与机器人配置、传感器、奖励与结束条件、Gymnasium 环境，以及其他层在仿真中的适配。在 `sim` 容器开发，上游版本固定；GUI 与无界面运行共用该镜像。

- 模型与 RL 算法位于 `src/ai`，ROS 消息转换位于 `src/ros`；场景不直接依赖特定模型的内部代码，由实验层选择适配器与策略。
- 官方 Arena × GR00T 客户端与 G1 WBC 作为当前基线保留在上游，不当作自研模块的通用接口。
- 真机阶段的控制核心动态库在仿真中由本模块加载，保证训练与评估在同一进程内确定地运行，见 [项目计划](../../docs/PROJECT_PLAN.md)。

## 内容

| 文件 | 作用 |
|---|---|
| `robotics_lab_sim/g1_recording.py` | 在上游 G1 取放场景里加一个固定的第三人称相机（1280×720），与头部相机一起逐帧录像；注册机器人配置 `g1_wbc_joint_recording` 和环境 `g1_locomanip_recording`，场景、任务与策略都与上游相同，策略仍只读头部相机 |

主机上运行 `./scripts/lab g1-record` 会以无界面方式跑一集，按仿真时间录下两路画面，并合成左右并排的视频，结果在 `output/runs/arena-g1/recordings/<时间>/`。相机位置在 `g1_recording.py` 顶部的 `THIRD_PERSON_EYE` / `THIRD_PERSON_TARGET` 调整。

模块通过 `--external_environment_class_path` 加载；在 sim 镜像下次重建、按开发指南写入 `.pth` 之前，`scripts/lab` 用 `PYTHONPATH=/workspace/src/simulation` 让 Arena 的环境导入本模块。模块约定与依赖规则见 [开发指南](../../docs/DEVELOPMENT.md)。
