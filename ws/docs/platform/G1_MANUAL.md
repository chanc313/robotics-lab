# 平台：G1 闭环操作手册

本页是实验平台（上游 Isaac Lab-Arena × GR00T N1.6 的 G1 移动操作 demo）的使用说明：它由什么组成、怎么运行、在本机的实测表现、已知局限，以及要改行为时从哪里接入。参数和代码位置放在文末的细节索引里，需要时再查。

上游固定版本为 Arena `8737b4c`、GR00T `e29d8fc`（见 `docker/versions.env`）。

## 骨架

![G1 闭环：分层与时间尺度](../images/g1-closed-loop.svg)

基线由三层现成部件拼成，都来自 NVIDIA，可以直接运行：

- **上层：GR00T N1.6 视觉-语言-动作模型。** 已在这个任务上微调好。它看头部相机的一帧画面、读上身关节角、接收一句英文指令，每秒给出接下来 1 秒的上身动作和行走指令（往哪走、走多快、身体多高）。
- **下层：全身控制器。** 手臂和手直接跟随 GR00T 给的目标；腿交给 AGILE，一个已训练好的强化学习行走策略，它按行走指令迈步并保持平衡。
- **仿真：Isaac Sim。** 模拟 Unitree G1（43 个自由度，带三指手）和仓库场景，并判定任务是否完成：从货架取下棕色盒子，放进右侧桌上的蓝色箱子，限时 30 秒。

GR00T 运行在 policy 容器，控制器与仿真运行在 sim 容器，两者经本机端口通信。上层慢（1 Hz）、下层快（50 Hz）、物理更快（200 Hz），这是整个基线的核心分工。

## 运行

两个终端，先启动推理服务，再启动评估：

```bash
./scripts/lab policy-server     # GR00T 服务，约 30 秒就绪
./scripts/lab g1-evaluate       # 打开 Kit 窗口，跑 1 个 episode
```

不需要窗口、要批量跑或录头部相机视频时，在 sim 容器里直接调用同一个评估程序：

```bash
source ws/experiments/arena_g1/experiment.env
./scripts/lab sim env PYTHONPATH=/opt/arena/submodules/Isaac-GR00T \
  python isaaclab_arena/evaluation/policy_runner.py --headless --device cpu --enable_cameras \
  --policy_type isaaclab_arena_gr00t.policy.gr00t_remote_closedloop_policy.Gr00tRemoteClosedloopPolicy \
  --policy_config_yaml_path "$G1_POLICY_CONFIG" --remote_host 127.0.0.1 --remote_port 5555 \
  --num_episodes 5 --output_base_dir /runs/arena-g1/evaluation \
  "$G1_TASK" --object brown_box --embodiment "$G1_EMBODIMENT"
```

加 `--record_camera_video` 会把头部相机画面逐帧写成 mp4，不占额外内存。结果在主机的 `output/runs/arena-g1/evaluation/<时间>/`：`episode_results_rank0.jsonl` 每行一个 episode，`index.html` 是汇总报告。

场景资产第一次运行时从 NVIDIA 资产库下载，缓存在 `output/storage/assets/downloads/`，之后的运行直接复用。

## 本机实测

RTX 4080 Laptop 12 GB、30 GB 内存，官方权重，无界面：

| 项 | 结果 |
|---|---|
| 成功率 | 2026-10-31 的 6 个 episode 成功 2 个（第 978、944 步）；3 个掉落盒子而提前终止，其中 2 个在早期（第 109、230 步），1 个在松手放入时盒子被弹出箱外（第 972 步，有头部相机录像）；1 个超时，盒子始终没抬起。连同 2026-10-13 的 2 次，8 次成功 3 次，95% 置信区间约 14%–69% |
| 仿真速度 | 约 7–8 个控制步每秒，约 0.15 倍实时；跑满 1500 步的 episode 约 3 分钟 |
| 显存与内存 | GR00T 服务约 6 GB；两边同时运行时整机显存约 10 GB / 12 GB，内存约 17 GB / 30 GB |
| 启动 | 资产缓存后约 40 秒；未缓存时 15–30 分钟，几乎全部花在下载场景（约 1.4 GB） |

## 已知局限

这些是上游设计的取舍，也是二次开发最直接的切入点：

1. **推理时仿真暂停。** 等效于推理零延迟；真机上推理期间机器人仍在运动，所以这里的成功率不能直接推到部署。
2. **动作整块开环执行。** 每块 1 秒内不看新的观测，块与块之间没有平滑。
3. **腰被锁定。** 取放全靠手臂和行走，模型给出的腰部目标没有用上。
4. **感知很窄。** 只用当前一帧头部 RGB，没有深度、历史帧和腕部相机。
5. **结果不可完全复现。** 固定种子只固定仿真一侧，GR00T 采样的噪声没有固定，同样的设置两次运行结果可以不同。
6. **评估很贵。** 单个 episode 墙钟数分钟，少量 episode 的成功率置信区间很宽；比较两个方案前要先定好每组的样本量。

## 从哪里接入

都不需要修改上游代码，自研部分放在本仓库 `ws/src/` 下（约定见 [开发指南](../DEVELOPMENT.md)）：

| 想做的事 | 接入方式 |
|---|---|
| 在 GR00T 外面加一层（安全审计、指令过滤、记录） | 写一个自己的策略类，内部调用原来的 GR00T 客户端，评估时用 `--policy_type` 指定 |
| 改变动作块的执行方式（异步推理、块间平滑） | 写一个自己的动作调度器，由上面的策略类使用 |
| 换下身控制器、放开腰 | 上游控制器支持两种行走策略，腰的开关在控制器配置里 |
| 加扰动（推力、外力） | 写自己的环境类，加入 Isaac Lab 的事件项，评估时用 `--external_environment_class_path` 加载 |
| 改光照、相机、物体质量 | Arena 自带变化项与敏感性分析工具，`--list_variations` 列出当前环境可调的项 |
| 换物体、换目标、换任务 | 环境参数，或自己的环境类 |
| 微调或换模型 | 生成示范数据 → 转换为 LeRobot 格式 → `scripts/lab policy-train`；3B 模型微调需要云端 GPU。上游已附带 GR00T N1.7 的 G1 配置 |

## 细节索引

需要追到参数和代码时查这里。路径相对于 sim 容器里的 `/opt/arena`，可在 `scripts/lab sim` 中查看。

| 环节 | 细节 | 代码 |
|---|---|---|
| 主循环 | 每个控制步 `policy.get_action(env, obs)` 后 `env.step(actions)` | `isaaclab_arena/evaluation/policy_runner.py:92` |
| 观测 | 头部 RGB 480×640；43 个关节角 | `isaaclab_arena/embodiments/g1/g1.py` |
| 何时推理 | 上一块 50 步用完才请求新的一块 | `isaaclab_arena/policy/action_scheduling/action_chunk_scheduler.py:54` |
| 请求内容 | 图像缩放填充；状态为左右臂各 7、左右手各 7、腰 3，共 31 维；指令文本 | `isaaclab_arena_gr00t/policy/gr00t_core.py`（`build_gr00t_policy_observations`） |
| 推理 | 同步 ZMQ 请求-应答；Eagle 2B 视觉语言骨干 + DiT 动作头，4 步 flow matching 去噪；输出 50 步 × 35 维（31 个关节 + 行走 vx、vy、ωz + 身高） | `isaaclab_arena_gr00t/policy/gr00t_remote_closedloop_policy.py:198`；权重 `config.json` |
| 映射到仿真动作 | 35 维改排为 50 维：43 个关节位置 + 行走 3 + 身高 1 + 躯干姿态 3（GR00T 不输出，填 0） | `gr00t_core.py:335` |
| 全身控制 | 手臂与手 28 个关节直接作位置目标；AGILE（带 LSTM 的 ONNX 学生策略）读 29 个身体关节状态，输出 12 个腿关节目标；腰 3 个关节固定为 0（`enable_waist=False`） | `isaaclab_arena_g1/g1_env/mdp/actions/g1_decoupled_wbc_joint_action.py:185`；`isaaclab_arena_g1/g1_whole_body_controller/wbc_policy/policy/g1_agile_policy.py:146`；同目录 `config/configs.py:95` |
| 物理 | 每个控制步 4 个 PhysX 步（`dt=0.005`、`decimation=4`），关节 PD 驱动 | 环境配置 |
| 判定 | 依次满足：物体落稳 → 盒子抬过一定高度 → 盒子稳定落在箱子里；盒子掉落提前终止；1500 步（30 秒）超时 | `isaaclab_arena/tasks/pick_and_place_task.py`；`isaaclab_arena_environments/galileo_g1_locomanip_pick_and_place_environment.py:169` |
| 资产下载 | 远程 USD 镜像到 `tempfile.gettempdir()`；sim 容器的 `TMPDIR` 指向 `/data/assets/downloads` | `submodules/IsaacLab/source/isaaclab/isaaclab/utils/assets.py`（`retrieve_file_path`） |

### GR00T N1.6 模型与训练

设计思想见 [平台设计](G1_DESIGN.md)。下面是本地源码（policy 容器 `/opt/arena/submodules/Isaac-GR00T`）与权重 `output/storage/models/arena-g1/checkpoint-20000` 中的数值。

| 部件 | 细节 | 位置 |
|---|---|---|
| 视觉语言骨干 | Eagle（`nvidia/Eagle-Block2A-2B-v2`）：SigLIP-2 视觉编码器（27 层，patch 14）+ 两层 MLP 连接器（pixel shuffle 下采样 0.5）+ Qwen3-1.7B 语言模型，只保留前 16 层（共 28 层），输出 2048 维特征 | `gr00t/model/modules/eagle_backbone.py`；权重 `config.json` 的 `select_layer=16` |
| 动作头 | AlternateVLDiT：32 层，奇数层自注意力（状态 token + 50 个动作 token），偶数层交叉注意力，在图像 token 与文字 token 之间轮换；时间步经 AdaLN 注入；约 1.09B 参数 | `gr00t/model/modules/dit.py:289` |
| 机器人插头 | 状态编码器、动作编码器、动作解码器均按 embodiment 选取参数（最多 32 种）；动作维度补齐到 128 | `gr00t/model/modules/embodiment_conditioned_mlp.py` |
| 训练目标 | flow matching：时间 t 取自 Beta 分布，`x_t = (1-t)·噪声 + t·动作`，回归速度 `动作 - 噪声` 的 MSE | `gr00t/model/gr00t_n1d6/gr00t_n1d6.py`（`Gr00tN1d6ActionHead.forward`） |
| 推理 | 从高斯噪声出发，欧拉积分 4 步（`num_inference_timesteps=4`）；噪声未设种子 | 同上，`get_action_with_features` |
| 微调设置 | 语言模型冻结但放开最后 4 层（`tune_top_llm_layers=4`）；视觉编码器、连接器、动作头、embodiment 插头全部训练；8 GPU、全局 batch 96、学习率 1e-4、2 万步 | 权重 `experiment_cfg/conf.yaml` |
| 微调数据 | VR 遥操作示范 → Isaac Lab Mimic 扩增（上游教程 `--generation_num_trials 100`；发布权重所用条数未在权重文件中注明）→ LeRobot 格式；Hugging Face 数据集 `nvidia/Arena-G1-Loco-Manipulation-Task` | Arena 文档 `docs/pages/example_workflows/locomanipulation/` |
| AGILE | WBC-AGILE 的速度-身高学生策略（`unitree_g1_velocity_height_recurrent_student.onnx`，固定提交 `7259792`）；指令 `[vx, vy, ωz, h]`，默认身高 0.72 m | `isaaclab_arena_g1/g1_whole_body_controller/wbc_policy/config/g1_agile.yaml` |
