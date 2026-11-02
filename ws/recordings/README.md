# recordings

挑选出来、值得保存的仿真录像，随仓库推送。运行产物默认留在 `output/runs/`（不进 Git）；想保存某一集时，把 `output/runs/arena-g1/recordings/<时间>/` 整个目录复制到这里再提交。dev 容器里挂载为 `/workspace/recordings`。

视频以二进制形式进 Git，仓库会随之变大：单个文件不要超过 50 MB，只放有代表性的片段；数量多了再考虑 Git LFS。

| 目录 | 内容 |
|---|---|
| `2026-11-02_02-15-54/` | 项目起点：上游 G1 基线（官方 GR00T N1.6 权重、HOMIE v2 下身策略）一集成功的取放，第 947 步完成。`side-by-side-episode-0.mp4` 左为固定第三人称相机、右为头部相机，按仿真时间逐帧对齐；另有两路原始视频和 Arena 的结果记录。由 `./scripts/lab g1-record` 录制 |
