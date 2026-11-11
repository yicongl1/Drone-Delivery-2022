# 联调录屏（2022）

智能配送无人机赛项备赛期间的屏幕录制，VMware 里的 Ubuntu 地面站，画面是 ROS 终端与视觉调试窗口。

全部为 **2512×1440 / 30 fps / H.264**，文件名前缀是当时的自评结果：
`final` = 最终版、`right` = 定点/识别正常、`fail` = 失败记录。

## 本次发布

| # | 日期 | 时长 | 大小 | 文件 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 2022-10-14 | 01:34 | 203.2 MB | `[fail]Ubuntu - VMware Workstation 2022-10-14 18-55-44.mp4` | 早期联调，失败记录 |
| 2 | 2022-10-15 | 01:37 | 210.0 MB | `[right]Ubuntu - VMware Workstation 2022-10-15 16-02-43.mp4` | 定点与识别正常 |
| 3 | 2022-11-04 | 01:50 | 238.6 MB | `[right]Ubuntu - VMware Workstation 2022-11-04 14-37-23.mp4` | 定点与识别正常 |
| 4 | 2022-11-21 | 00:17 | 36.7 MB | `[fail]Ubuntu - VMware Workstation 2022-11-21 14-50-14.mp4` | 投放异常 |
| 5 | 2022-12-03 | 01:14 | 161.1 MB | `[fail]Ubuntu - VMware Workstation 2022-12-03 22-28-14.mp4` | 赛前故障 |
| 6 | 2022-12-17 | 03:42 | 483.5 MB | `[final]Ubuntu - VMware Workstation 2022-12-17 00-45-42.mp4` | 最终版，流程完整 |

合计 **6 段 / 10 分 14 秒 / 1.33 GB**。

## 未发布的 8 段

`[useful]` × 7（10-21、10-28、11-04、11-06、11-08、11-09、11-17 的过程记录）与
`[nodetected]` × 1（11-18，相机没检测到目标）仅本地保留，用来还原每天的调试现场。
完整清单（14 段，含时长、分辨率、SHA256）见仓库里的 `README.md` 与 `SHA256SUMS.txt`。

## 完整性校验

```bash
sha256sum -c SHA256SUMS.txt        # Linux / macOS
Get-FileHash -Algorithm SHA256 *   # Windows PowerShell，逐条比对
```

## 这些录屏能看出什么

- 地面站 5 个终端：航点输入、模式切换、状态显示、串口舵机、视觉识别
- MAVROS 打印的 `/mavros/local_position/pose` 随飞机移动变化（T265 定点是否正常）
- 识别节点输出的圆心偏差 `The change is x:... y:...`，以及偶尔的误检
- 降落、舵机投放、`AUTO.LAND` 与上锁的完整时序
