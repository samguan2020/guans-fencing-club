# Guan's Fencing Club — UE 桌面漫游

此项目使用本机已安装并实际运行的 Unreal Engine **5.8.3**。不要使用旧版本引擎打开或保存这些 .uasset/.umap 文件。

## 进入场馆

双击 `Play.cmd`。它用本机 UE 启动独立的游戏窗口，无需手动导入模型或配置关卡。首次进入可能需要等待着色器编译。

本机显卡为 GTX 1050 Ti，驱动已更新为 582.66。运行问题可在项目的 `Saved/Logs` 中查看。

- 点击游戏窗口后，用 **W/A/S/D** 移动，**鼠标**转动视角，**空格**跳跃。
- **Alt+F4** 关闭独立游戏窗口。
- 这是依赖已安装 UE 的本地运行方式，不是可分发给其他电脑的打包 EXE。

## 在 UE 编辑

双击 `OpenEditor.cmd`。项目会打开 `/Game/GuansClub/FencingHall`，点击工具栏 **Play** 开始，**Esc** 停止；**Shift+F1** 释放鼠标。

场馆资产在 `Content/GuansClub`：组合场馆网格、11 个基础材质、室内灯光、固定曝光、玩家出生点以及两条剑道的比赛原点。组合场馆使用复杂碰撞作为简单碰撞，适用于这个静态桌面原型；后续可拆分模型并配置更轻量的碰撞。

比赛原点是 `ReplayOrigin_Piste_01` 和 `ReplayOrigin_Piste_02`，使用 UE 厘米单位。

## 剑道 1 比赛回放

剑道 1 已接入用户提供的两位剑手 FBX。进入场馆后自动同步循环播放约 10.42 秒的动作，仍可自由走动观看。两人的动画共用 `Content/GuansClub/Duel/LS_Piste01_Duel` 时间轴，24 fps；使用不带首帧 T-pose 的版本，关闭根运动提取，保留动画内的前后位移。

导入时整体沿剑道居中，另用时间轴上的角色位置轨道抵消源动画的横向漂移，使身体中心保持在剑道 1 中线上。原始姿势和前后位移不变，仍可能看到源动画中的姿势或脚部误差。两人采用浅蓝与浅金材质便于区分。

剑道 1 后方墙上增加了 6.4 × 3.6 米的大屏幕。参考 MP4 保存在 `Content/Movies/fencing_duel_clip.mp4`；实际播放使用由该视频转换的 1280 × 720 图像序列 `Content/Movies/FencingFrames`，避免本机 MP4 解码黑屏。视频与两人动作共用同一个 Sequencer 时间轴并循环，目前为静音。原视频有 249 帧，末尾补一帧静止画面，与动作的 250 帧循环对齐。图像序列由 `SourceAssets/extract_video_frames.py` 生成。

两人右手各绑定了一把带护手的佩剑。外形参考视频，剑随原 FBX 的右手骨骼运动；这不是逐帧重建的真实剑尖轨迹，不包含剑身弯曲或碰撞模拟。剑模型源文件位于 `SourceAssets/sabre.blend`。

两把剑的剑尖分别用蓝色、橙色标记，并显示最近 **1 秒** 的渐隐轨迹。剑尖保持实时位置；越旧的轨迹越淡，超过 1 秒隐藏，每次比赛循环清空历史。轨迹依据当前 UE 剑尖按 48 Hz 采样，与比赛共用时间轴。它展示当前三维动画的剑尖运动，不是从原视频额外测得的真实剑尖轨迹。

如果改变角色动画、位置或剑的长度，需要重新运行 `sample_sword_tips.py`，用 Blender 运行 `SourceAssets/build_tip_trails.py`，最后在 UE 运行 `add_tip_trails.py`。`tip_trails_setup.json` 和 `tip_trails_validation.json` 分别记录配置和实际运行检查。

`SourceAssets/Duel` 保存了两份原始 FBX 副本和位置计算参数；`duel_setup.json` 记录资产路径和放置变换；`tv_sabres_setup.json` 记录大屏和剑的设置，`tv_sabres_validation.json` 记录最近一次运行检查。重建回放时依次运行 `add_duel.py`、`align_duel.py`、`add_tv_sabres.py`；**不要重跑 `build_ue_hall.py`，它会重建整个基础场馆并移除新增角色**。

## 项目文件

- `GuansFencingClub.uproject`：UE 项目。
- `build_ue_hall.py`：导入并生成场馆的编辑器脚本。会重建 `/Game/GuansClub/FencingHall`，有手动修改后请不要直接重跑。
- `build_report.json`：模型尺寸、材质和场景构建记录。
- `validate_play.py`：编辑器内 Play 自动检查脚本。
- `play_validation.json`：最近一次运行检查结果，以 `status` 为准。

启动脚本中的引擎路径是 `D:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`。如果移动了引擎安装位置，需要修改两个 .cmd 文件里的 `UE_EDITOR`。
