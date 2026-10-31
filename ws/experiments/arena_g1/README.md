# Arena × GR00T N1.6：G1 移动双臂

当前研究对象是官方 G1 从货架取棕色盒子、放入桌面蓝色箱子的移动操作流程。

`experiment.env` 由 `scripts/lab` 的 G1 / GR00T 入口读取，固定此实验的任务、官方策略配置、机器人适配和端点默认值。权重为 `nvidia/GN1x-Tuned-Arena-G1-Loco-Manipulation`，revision `gn1_6`，数据与权重单独保存到 `/data`。

这里负责组合模型、仿真任务、机器人控制接口（当前为上游 `g1_wbc_joint`）与未来的 ROS 适配，不把 G1 的约束写入通用模块。训练入口、实验参数、结果摘要随后放这里；大文件与运行结果放 `output/storage`、`output/runs`。

官方权重已下载，G1 闭环可运行（实测见 [操作手册](../../docs/platform/G1_MANUAL.md#本机实测)）；ROS 链路与自研控制尚未开始。
