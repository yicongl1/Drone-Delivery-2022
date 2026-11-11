2022 年备赛期间的屏幕录制：VMware 里的 Ubuntu 地面站，画面是 ROS 终端与视觉调试窗口。
全部 2512×1440 / 30 fps / H.264。文件名前缀是当时的自评结果 —— `final` 最终版、`right` 定点/识别正常、
`nodetected` 没检测到目标、`fail` 失败记录。

| 前缀 | 日期 | 时长 | 大小 | 文件 |
| --- | --- | --- | --- | --- |
| `fail` | 2022-10-14 | 01:34 | 203.2 MB | `[fail]Ubuntu - VMware Workstation 2022-10-14 18-55-44.mp4` |
| `right` | 2022-10-15 | 01:37 | 210.0 MB | `[right]Ubuntu - VMware Workstation 2022-10-15 16-02-43.mp4` |
| `right` | 2022-11-04 | 01:50 | 238.6 MB | `[right]Ubuntu - VMware Workstation 2022-11-04 14-37-23.mp4` |
| `nodetected` | 2022-11-18 | 02:53 | 375.0 MB | `[nodetected]Ubuntu - VMware Workstation 2022-11-18 16-58-55.mp4` |
| `fail` | 2022-11-21 | 00:17 | 36.7 MB | `[fail]Ubuntu - VMware Workstation 2022-11-21 14-50-14.mp4` |
| `fail` | 2022-12-03 | 01:14 | 161.1 MB | `[fail]Ubuntu - VMware Workstation 2022-12-03 22-28-14.mp4` |
| `final` | 2022-12-17 | 03:42 | 483.5 MB | `[final]Ubuntu - VMware Workstation 2022-12-17 00-45-42.mp4` |

**合计 7 段 / 13 分 07 秒 / 1.71 GB。**

画面里能看到：地面站五个终端的启动与操作、MAVROS 打印的 `/mavros/local_position/pose` 随飞机移动而变化
（判断 T265 定点是否正常）、识别节点输出的圆心偏差与漏检时的表现、降落与舵机投放、
`AUTO.LAND` 与上锁的完整时序。

另有 7 段过程记录未随本 Release 发布。14 段的完整索引、时长与 SHA256 校验和见仓库
[`04_联调录屏/`](https://github.com/yicongl1/Drone-Delivery-2022/tree/main/04_%E8%81%94%E8%B0%83%E5%BD%95%E5%B1%8F)。

代码与文档：[Drone-Delivery-2022](https://github.com/yicongl1/Drone-Delivery-2022)
