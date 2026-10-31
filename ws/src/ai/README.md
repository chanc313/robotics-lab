# src/ai：上层 AI

职责：模型结构、推理、模仿学习与 RL 算法、训练配方、模型适配。在 `policy` 容器开发，当前环境是 GR00T N1.6 的依赖基线（Python 3.10、PyTorch、Gymnasium、pandas 与训练依赖）。

- 不导入 `src/ros` 或 Isaac 运行时；与机器人和环境的交互通过项目计划中接口契约确定的观测 / 动作契约，或 Gymnasium 环境适配器完成。
- 新模型需要不同环境时新建镜像，不强行沿用 GR00T 的依赖配方。
- RL 算法属于本模块，Isaac 环境适配属于 `src/simulation`；需要同进程向量化训练时，算法包可以装进 `sim` 镜像，源码边界不变。
- 当前 Arena × GR00T 的机器人映射与启动组合属于 `experiments/arena_g1`，不作为所有模型的默认行为。

目前没有自研代码。模块约定与依赖规则见 [开发指南](../../docs/DEVELOPMENT.md)。
