# 配置导读：GR00T 闭环配置与 G1 模态配置

2026-10-19，配合 [学习计划](LEARNING_PLAN.md) Day 0 第 3 步。两份文件都来自 Arena 固定提交 `8737b4c`，在 sim 容器里位于 `/opt/arena/isaaclab_arena_gr00t/`（VS Code 的 sim 窗口用 **File: Open File...** 打开）：

- [G1 模态配置](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena_gr00t/embodiments/g1/g1_sim_wbc_data_config.py) `embodiments/g1/g1_sim_wbc_data_config.py`
- [GR00T 闭环配置](https://github.com/isaac-sim/IsaacLab-Arena/blob/8737b4ceb25f99f81a81786b7fde73139b52f324/isaaclab_arena_gr00t/policy/config/g1_locomanip_gr00t_closedloop_config.yaml) `policy/config/g1_locomanip_gr00t_closedloop_config.yaml`

## 一句话分工

- **模态配置**写的是模型这一侧：GR00T 吃哪些输入、吐哪些输出、每样取几个时间步。它必须和训练时完全一致，否则权重和归一化统计对不上。
- **闭环配置**写的是仿真这一侧：怎样把 Isaac 的观测翻译成 GR00T 的输入，再把 GR00T 的输出翻译回 Isaac 的动作，以及多久请求一次。

## 一次请求里，两份配置各管哪一段

```text
仿真观测
  camera_obs["robot_head_cam_rgb"]   头部相机图像        ← 闭环配置 pov_cam_name_sim
  policy["robot_joint_pos"]          43 个关节，仿真顺序  ← 闭环配置 state_joints_config_path
        │ 按关节名重排成 GR00T 分组                       ← 闭环配置 policy_joints_config_path
        ▼
GR00T 请求：video.ego_view、state 五组关节、language   ← 模态配置 video / state / language
        │ ZMQ → policy 容器推理
        ▼
GR00T 输出：7 个动作键 × 50 步，每步 35 个数           ← 模态配置 action
        │ 关节放回仿真顺序，再追加行走、高度、躯干姿态   ← 闭环配置 action_joints_config_path、task_mode_name
        ▼
50 步 × 每步 50 维的动作块，每个控制步取一行执行，取完再请求  ← 闭环配置 action_chunk_length
```

## 一、G1 模态配置

文件定义一个字典 `unitree_g1_sim_wbc_config`，四个键对应四种模态。每个 `ModalityConfig` 有两个核心字段：

- `delta_indices`：相对"当前时刻"取哪些时间步。`[0]` 只取当前这一步；`list(range(50))` 取当前及之后共 50 步（t, t+1, …, t+49）。
- `modality_keys`：这一模态包含哪些数据键，名字沿用训练数据集里的叫法。

| 模态 | `delta_indices` | `modality_keys` | 含义 |
|---|---|---|---|
| `video` | `[0]` | `ego_view` | 只看当前一帧头部相机画面，不叠历史帧 |
| `state` | `[0]` | `left_arm`、`right_arm`、`left_hand`、`right_hand`、`waist` | 当前的上身关节位置，维度 7、7、7、7、3，共 31 个数 |
| `action` | `0…49` | 上面五组 + `base_height_command`、`navigate_command` | 未来 50 步，每步 7+7+7+7+3+1+3 = 35 个数 |
| `language` | `[0]` | `annotation.human.task_description` | 数据集里人工标注的任务描述，推理时填入语言指令 |

在 50 Hz 控制下，50 步动作覆盖 1 秒。state 里没有腿：腿由 WBC 的下身强化学习策略负责，模型既不看腿的状态，也不输出腿的目标。

`action_configs` 与动作键一一对应，七项都一样：

- `rep=ABSOLUTE`：输出的是绝对目标值，例如"左肘转到 0.8 rad"。另外两种是 `RELATIVE`、`DELTA`，表示相对当前状态的量。
- `type=NON_EEF`：关节空间或指令量，不是末端位姿（`EEF`）。
- `format=DEFAULT`：不做旋转表示转换。`XYZ_ROT6D`、`XYZ_ROTVEC` 用于末端位姿类动作。

最后一行 `register_modality_config(..., embodiment_tag=EmbodimentTag.NEW_EMBODIMENT)` 把这套配置登记到 `NEW_EMBODIMENT` 形态标签上。GR00T 为每种机器人形态保留一组独立的输入输出投影层，标签决定用哪一组。官方 G1 微调权重训练在 `new_embodiment` 槽位上（权重目录 `embodiment_id.json` 中为 10）；GR00T 另有预置的 `unitree_g1` 标签（8），这次没有用。

**和权重核对**：权重目录 `output/storage/models/arena-g1/checkpoint-20000/experiment_cfg/dataset_statistics.json` 中，action 各键维度正好是 7、7、7、7、3、1、3，state 是 7、7、7、7、3，与本文件一致。归一化统计也按这些键存储，所以键名和维度都不能随意改。

同一文件还给出训练数据中指令量的范围，可以顺便看出这个任务"教"了机器人什么（推断，Day 3、Day 5 观察时验证）：

| 指令 | 含义 | 训练数据范围 |
|---|---|---|
| `navigate_command` | 前后速度、左右速度（m/s）、转向角速度（rad/s） | 前后 0 到 0.4；左右 −0.13 到 0.16；转向 −0.4 到 0.1 |
| `base_height_command` | 骨盆高度目标（m） | 0.60 到 0.75（WBC 默认 0.75，即直立） |

前后速度从不为负，说明示范里只向前走；转向大多为负，按 z 轴向上的约定是向右转，和"箱子在货架右侧"一致；高度最低到 0.60，可能是在货架前屈膝下蹲取盒子。

## 二、GR00T 闭环配置

YAML 的每个字段对应 `isaaclab_arena_gr00t/policy/config/gr00t_closedloop_policy_config.py` 里 `Gr00tClosedloopPolicyCfg` 的同名字段，由 `gr00t_remote_closedloop_policy.py` 读取。

| 字段 | 值 | 含义 |
|---|---|---|
| `language_instruction` | "Pick up the brown box…" | 默认指令。policy_runner 运行时优先用 `--language_instruction` 或任务自带的描述，都没有时才用这里的值 |
| `action_horizon` | 50 | 模型每次预测多少步，必须等于模态配置里 action 的 `delta_indices` 长度 |
| `embodiment_tag` | `NEW_EMBODIMENT` | 必须与模态配置登记的标签相同；代码在 G1 任务模式下强制要求这个值 |
| `video_backend` | `decord` | 视频解码库，用于读取数据集里的视频。闭环里的图像直接来自仿真，Arena 的代码只定义了这个字段、没有使用它 |
| `modality_config_path` | 指向上面的模态配置 | 仿真侧据此知道 video、state、language 的键名 |
| `policy_joints_config_path` | `gr00t_43dof_joint_space.yaml` | GR00T 的关节分组与组内顺序：左腿、右腿、腰、左臂、左手、右臂、右手 |
| `action_joints_config_path`、`state_joints_config_path` | `43dof_joint_space.yaml` | Isaac 里 G1 的关节顺序：左右交替、从躯干向末端排列，例如 0 号是 `left_hip_pitch_joint`，2 号是 `waist_yaw_joint` |
| `action_chunk_length` | 50 | 每次请求后实际执行多少步再重新请求，可以小于 `action_horizon`；这里等于 50，所以每 50 个控制步（1 秒）推理一次 |
| `pov_cam_name_sim` | `robot_head_cam_rgb` | 头部相机在仿真观测 `camera_obs` 里的名字；它的图像被填进模态配置的 `ego_view`，两个名字指同一路画面 |
| `task_mode_name` | `g1_locomanipulation` | 决定动作怎样拼装：在 43 个关节之后追加行走、高度、躯干姿态指令 |

YAML 没写的字段用默认值，例如图像尺寸 480×640、种子 10。

**为什么要两份关节表**：同一个关节在两边编号不同。例如 `left_shoulder_pitch_joint` 在仿真顺序里是 11 号，在 GR00T 的 `left_arm` 组里是第 0 个。所以观测时按名字把仿真的 43 个值拆成 GR00T 分组，动作时再按名字放回仿真顺序（`isaaclab_arena_gr00t/utils/joints_conversion.py`）。

## 三、50 维动作从哪里来

`gr00t_core.py` 的 `build_gr00t_action_np` 把每一步的输出拼成 50 维，顺序如下：

| 槽位 | 内容 | 来源 |
|---|---|---|
| 0–42 | 43 个关节目标，仿真顺序 | 手臂、手、腰共 31 个来自 GR00T；12 个腿部关节填 0 |
| 43–45 | `navigate_command` | GR00T |
| 46 | `base_height_command` | GR00T |
| 47–49 | 躯干姿态（横滚、俯仰、偏航） | GR00T 不输出，固定填 0 |

这 50 维交给 WBC 动作项 `g1_decoupled_wbc_joint_action.py`：上身关节目标直接做位置控制，行走速度和高度交给 AGILE 下身策略生成腿部动作。按代码，G1 当前使用的 AGILE 配置 `enable_waist=False`，腰被划在下身组里，所以 GR00T 预测的 3 个腰部目标实际不会被执行，腰由下身策略控制。

执行由 `ActionChunkScheduler` 负责：缓存一块 50×50 的动作，每个 `env.step()` 取一行；50 行取完后再向服务端请求下一块。

## 四、读完可以回答

- GR00T 一次请求的输入有几样、各多大？输出每步多少个数，为什么到仿真里变成 50 个？
- `action_chunk_length` 改成 25 会怎样？推理次数和对环境变化的反应各有什么变化？
- 如果把 `pov_cam_name_sim` 换成另一个相机，模型还会正常工作吗？为什么？
