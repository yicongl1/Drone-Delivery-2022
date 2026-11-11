# 联调录屏

2022 年 10–12 月每次上机调试的屏幕录制，共 14 段、3.4 GB、26 分 06 秒。
全部为 VMware Workstation 录制：**2512×1440 / 30 fps / H.264 / 约 18 Mbps**，文件名前缀是当时的自评结果。

| # | 日期 | 时长 | 大小 | 文件 |
| --- | --- | --- | --- | --- |
| 1 | 2022-10-14 18:57 | 01:34 | 203.2 MB | `[fail]Ubuntu - VMware Workstation 2022-10-14 18-55-44.mp4` |
| 2 | 2022-10-15 16:04 | 01:37 | 210.0 MB | `[right]Ubuntu - VMware Workstation 2022-10-15 16-02-43.mp4` |
| 3 | 2022-10-21 17:34 | 00:51 | 111.2 MB | `[useful]Ubuntu - VMware Workstation 2022-10-21 17-33-12.mp4` |
| 4 | 2022-10-28 15:24 | 00:54 | 117.0 MB | `[useful]Ubuntu - VMware Workstation 2022-10-28 15-23-52.mp4` |
| 5 | 2022-11-04 13:40 | 00:41 | 88.1 MB | `[useful]Ubuntu - VMware Workstation 2022-11-04 13-39-52.mp4` |
| 6 | 2022-11-04 14:39 | 01:50 | 238.6 MB | `[right]Ubuntu - VMware Workstation 2022-11-04 14-37-23.mp4` |
| 7 | 2022-11-06 17:50 | 02:16 | 296.0 MB | `[useful]Ubuntu - VMware Workstation 2022-11-06 17-47-59.mp4` |
| 8 | 2022-11-08 16:37 | 02:13 | 289.5 MB | `[useful]Ubuntu - VMware Workstation 2022-11-08 16-35-32.mp4` |
| 9 | 2022-11-09 16:07 | 03:09 | 409.2 MB | `[usefulUbuntu - VMware Workstation 2022-11-09 16-04-38.mp4` |
| 10 | 2022-11-17 17:22 | 02:55 | 380.3 MB | `[useful]Ubuntu - VMware Workstation 2022-11-17 17-19-39.mp4` |
| 11 | 2022-11-18 17:01 | 02:53 | 375.0 MB | `[nodetected]Ubuntu - VMware Workstation 2022-11-18 16-58-55.mp4` |
| 12 | 2022-11-21 14:50 | 00:17 | 36.7 MB | `[fail]Ubuntu - VMware Workstation 2022-11-21 14-50-14.mp4` |
| 13 | 2022-12-03 22:29 | 01:14 | 161.1 MB | `[fail]Ubuntu - VMware Workstation 2022-12-03 22-28-14.mp4` |
| 14 | 2022-12-17 00:49 | 03:42 | 483.5 MB | `[final]Ubuntu - VMware Workstation 2022-12-17 00-45-42.mp4` |

前缀含义：`[final]` 最终版、`[right]` 定点/识别正常、`[useful]` 有参考价值的中间过程、`[nodetected]` 当时没检测到目标、`[fail]` 失败记录。
第 9 个文件名少一个 `]`，是原始文件名。

**完整性校验**：`SHA256SUMS.txt`（14 条，`sha256sum -c` 或 `Get-FileHash` 均可核对）。

> 想还原某天的现场，可对照 `06_归档/` 里的代码快照：`offb_1015_twodetect.zip`（10/15）、
> `offb-2022-10-28变体/`（10/28），以及 `03_代码/ros_ws/src/offb/src/cycle_detect_new_10_26.cpp`。

---

## 打包进 GitHub Release 的可行性

结论：**可以，14 个文件不用拆分、也不用压缩，直接作为 release assets 上传即可。**

| 限制 | 数值 | 是否触发 |
| --- | --- | --- |
| 单个 release asset 上限 | 2 GiB | 否，最大 483.5 MB |
| 仓库大小建议 | 尽量 < 1 GB；单文件 > 100 MiB 会被 git 直接拒收 | release asset **不计入**仓库大小，所以不受影响 |
| 总 release 大小 | 没有公开硬上限 | 3.4 GB 属正常范围，但 GitHub 不是网盘，别当 CDN 反复刷 |

**不建议压缩**：H.264 已经是压缩流，7z/zip 对这批文件基本没有收益（通常 < 2%），
却要额外占 3.4 GB 临时空间、多花一遍读写时间。要「一个包」的话用 tar 打包成归档容器即可（不压缩，只为合并）。

**更不建议塞进 git 历史**：3.4 GB 进去后 clone 会变得非常痛苦，且无法干净地移除。release asset 就是为这种场景准备的。

### 上传步骤

本机目前没装 GitHub CLI（`gh` 未找到，git 已安装）。先装再传：

```powershell
winget install --id GitHub.cli -e        # 装完重开终端
gh auth login                            # 选 GitHub.com → HTTPS → 浏览器授权
```

然后在仓库根目录（`git init` 并 push 过至少一个 commit 之后）：

```powershell
# 1) 先建草稿 release，确认页面没问题再发布
gh release create drone-2022 --draft `
  --title "智能配送无人机 2022 · 联调录屏" `
  --notes-file "04_联调录屏/README.md"

# 2) 逐个上传（文件名含 [ ]，用 -Filter 取值，避免被当成通配符）
$files = Get-ChildItem -LiteralPath "04_联调录屏" -Filter *.mp4 | ForEach-Object FullName
gh release upload drone-2022 $files

# 3) 核对数量后发布草稿
gh release view drone-2022
gh release edit drone-2022 --draft=false --latest
```

上传 3.4 GB 的耗时取决于上行带宽（20 Mbps 上行约 25 分钟），中途失败可重跑同一命令，
`--clobber` 会覆盖同名 asset。

### 放之前必须确认的两件事

1. **公开还是私有**。公开仓库的 release asset 任何人都能下载；私有仓库的 asset 需要登录授权才能下。
   录屏里是团队成员的终端、主机名、局域网 IP / hosts 配置，可能还有账号痕迹。
   不确定就先建**私有仓库**，或者逐段看一遍再公开。
2. **播放体验**。3.4 GB 的原片适合存档，不适合随手点开看。如果目的是「让人看懂当时在干什么」，
   更合适的是另传一份到 B 站（可设仅自己可见/未列出）或网盘，release 里保留原始文件 + 本索引。

### 如果以后要把整个仓库也发布

`04_联调录屏/`（3.4 GB）和 `05_项目管理课程/` 里的视频（约 700 MB）都不该进 git 历史，
建议根目录放一个 `.gitignore`：

```gitignore
# 大体积媒体只走 Release，不进 git 历史
04_联调录屏/*.mp4
05_项目管理课程/展示视频素材/**/*.mp4
05_项目管理课程/展示视频素材/**/*.mkv
05_项目管理课程/展示视频素材/**/*.mov
05_项目管理课程/小组作业/**/*.mp4
05_项目管理课程/小组作业/**/*.mov
01_竞赛材料/答辩与比赛视频/*.mp4
```
