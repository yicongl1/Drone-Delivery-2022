# 智能配送无人机 —— 竞赛资料与技术实现归档

> 2022 年「智能配送无人机」赛项的全套资料：比赛文档、ROS 飞控代码、联调录屏，以及借用同一课题完成的项目管理课程作业。
>
> 比赛背景与获奖记录见个人网站：<https://yicongl1.github.io/competitions/drone/>

| 项目 | 内容 |
| --- | --- |
| 赛事 | 第十二届上海市大学生工程实践与创新能力大赛 · 智能配送无人机赛项 |
| 校内选拔 | 第十一届上海大学大学生工程训练综合能力竞赛 · **一等奖**（2022.10） |
| 市赛 | **特等奖**（2022.12） |
| 团队 | 4 人（飞控 / 视觉 / 结构三条线） |
| 平台 | PX4 飞控 + Jetson Nano 伴飞计算机 + Intel RealSense T265 + CSI 相机 + Arduino 舵机投放机构 |
| 软件 | Ubuntu + ROS Melodic + MAVROS + OpenCV + PX4 OFFBOARD 模式 |
| 资料规模 | 391 个文件，约 4.5 GB（去重前 630 个 / 4.7 GB） |

---

## 目录

- [1. 比赛任务与评分规则](#1-比赛任务与评分规则)
- [2. 技术方案](#2-技术方案)
- [3. 代码详解](#3-代码详解)
- [4. 如何复现](#4-如何复现)
- [5. 已知问题与历史遗留](#5-已知问题与历史遗留)
- [6. 资料目录索引](#6-资料目录索引)
- [7. 项目管理课程部分](#7-项目管理课程部分)
- [8. 参考资料](#8-参考资料)

---

## 1. 比赛任务与评分规则

赛题要求在**不碰障碍、不丢目标**的前提下，让无人机自主完成「越障 → 识别 → 投放」的一整套动作。

**场地**：起（终）点与投放区 A、B、C 分居场地四角。A 区为**靶环图案**，考验投放精度；B、C 区为不同图案，需要用视觉手段识别。起点与 A·B 中点之间有**建筑物**，B 至 C 的连线上有**灯柱**。障碍物位置与图形顺序**现场抽签**，且 B 点至 C 点之间的灯柱可在 ±500 mm 内变动，用来防止「伪自控」（纯按时间开环跑脚本）。

**物料**：圆锥 + 球冠组合体，球冠直径 60 mm、底部截面 50 mm、总高 65 mm（限高 70 mm）。相比圆柱体，重心更低、落地不易侧倾、受气流影响更小。

**流程**：装货固定 → 统一指令起飞并开始计时 → 按顺序把货物投放到 A、B、C 区（每个区只有一次投放机会）→ 投放 B、C 区时必须越障 → C 区完成后返航降落，停止计时。

**评分要点**：

- 每正确越过一个障碍 +5 分；
- A 区按落点与靶心的偏差计分，B、C 区按落区计分；
- 规定时间内返回起降区 +3 分；
- 物料必须**竖直放置**，倾倒不得分；
- 按控制方式设权重系数（自主程度越高系数越高）；
- 每队两轮，每轮 5 分钟（第一轮调试 5 分钟、第二轮调试 3 分钟），各占 50%，取最好成绩；
- 运行中停止 20 秒即结束本轮；一旦开始运行不得再接触机器人；触碰安全网或障碍物即比赛结束。

> 原始规则见 `01_竞赛材料/规则与赛题/`，我们提交的命题文档见 `01_竞赛材料/参赛文档/6-智能配送无人机场景设置与任务命题文档.docx`。

**我们的投放机构**：全包裹式载物仓，四个标准亚克力棒 + 两个外圆环装配，大面积镂空减重；舱底每个货舱架设**独立舵机**，舵机臂抵住物料使其在飞行中相对静止。收到投放指令后舵机臂转动，物料垂直滑落，载物仓随飞机继续飞行、可循环使用。物料三维模型见 `01_竞赛材料/物料与结构/wuliao.stl`（CATIA 导出的 ASCII STL）。

---

## 2. 技术方案

### 2.1 硬件

| 部件 | 型号 / 说明 | 作用 |
| --- | --- | --- |
| 飞控 | PX4（QGroundControl 配置与校准） | 姿态/位置控制，OFFBOARD 模式接受外部位置设定点 |
| 伴飞计算机 | NVIDIA Jetson Nano（aarch64 Ubuntu） | 跑 ROS 节点：MAVROS、视觉识别、串口投放 |
| 定位相机 | Intel RealSense **T265** | VIO 定位，经 `vision_to_mavros` 转成 `/mavros/vision_pose/pose` 提供给飞控 |
| 下视相机 | Jetson CSI 相机（`nvarguscamerasrc`） | 俯视靶环/图案，做圆心/方块识别 |
| 执行机构 | Arduino Uno + 3 路舵机 | 接收串口单字节指令，驱动货舱舱门投放 |
| 地面站 | 笔记本 + VMware Ubuntu 虚拟机 | SSH 进 Nano，运行控制台与 QGC |
| 网络 | 手机热点 / 路由器组建局域网 | Nano ↔ 地面站 ↔ QGC 的 ROS 通信 |

### 2.2 软件架构

机上（Nano）与地面站分两个 launch 启动，通过 ROS 网络（`ROS_MASTER_URI`）跨机器通信：

```
                    ┌─────────────────── Jetson Nano ────────────────────┐
  PX4 飞控  ⇄ MAVROS ┤                                                     │
                    │  realsense2_camera (T265) → vision_to_mavros        │
                    │        └→ /mavros/vision_pose/pose  → 飞控 EKF       │
                    │                                                     │
                    │  cam.py (CSI) → /camera/rgb/image_raw               │
                    │        └→ cycle_detect_new_node → /circle_center    │
                    │  test.cpp (serial) ← /servo  → /dev/arduino → 舵机  │
                    └─────────────────────────────────────────────────────┘
                                     ↕  ROS 网络
                    ┌──────────────── 地面站 ─────────────────────────────┐
                    │  com_node       主任务状态机（航点 / 下降 / 投放）   │
                    │  send_info_node 20 Hz 持续发设定点，防飞控掉出 OFFBOARD│
                    │  set_mode_node  交互式切模式 / 解锁                  │
                    │  showinfo_node  打印状态、位置、速度、姿态            │
                    │  servo_control_node 手动触发舵机                    │
                    └─────────────────────────────────────────────────────┘
```

### 2.3 飞行任务状态机（`com_node`）

`com.cpp` 是比赛主程序，按航点顺序执行「升 → 平飞 → 降落 → 投放 → 再升」：

```
1. 等待 MAVROS 连接
2. 从 stdin 读入航点个数与各点 (x, y)，z 统一用参数 desire_z
3. 等待飞控进入 OFFBOARD 且已解锁（由 set_mode_node 手动触发）
4. 对每个航点：
     fly_high()  从 0.3 m 起以 change 为步长逐步抬升到 desire_z
     fly_to()    以 change 为步长逼近目标点，三轴误差均 ≤0.15 m 视为到达
     landing()   以 change 为步长下降到地面，速度 <0.1 m/s 且高度 <0.1 m 视为落地
     unload()    等高度 <0.2 m → 位置保持 3 s → 发 /servo 序号 → 再保持 2 s
5. 全部完成 → 切 AUTO.LAND → 上锁
```

几个关键实现细节：

- **逐步逼近而不是直接发目标点**：`add_target()` 每周期只把设定点往目标挪 `change`（0.02~0.05 m），避免设定点跳变导致姿态剧烈抖动。
- **`send_info_node` 是安全网**：未解锁或不在 OFFBOARD 时以 20 Hz 持续发布速度设定点，保证解锁瞬间飞控不会因为「无设定点」而拒绝进入 OFFBOARD。
- **视觉修正只作用一次**：`node_flyput.cpp` 的 `is_ready()` 把 `/circle_center` 的偏差累加到落点上；这是「盲走 + 视觉纠偏」的简化方案。

### 2.4 视觉识别

两套基于 OpenCV 轮廓几何的检测器，思路一致：**用「周长² / 面积」这个无量纲量判断形状**，不需要模板和训练。

| 目标 | 判据 | 文件 |
| --- | --- | --- |
| 圆形（靶环） | $C^2/(4A) \approx \pi$，容差 0.4 | `offb/src/cycle_detect_new.cpp` |
| 正方形 | $C^2/A \approx 16$，容差 2 | `src/square_detect.cpp` |

处理流程：

```
bilateralFilter 双边滤波（去噪但保边）
  → Canny(24, 144) 边缘
  → 闭运算 9×9（融合断边）→ 开运算 3×3（去亮点噪声）
  → findContours → 按上述判据筛选轮廓
  → 取半径最小 / 面积合格者的轮廓矩质心 (m10/m00, m01/m00)
  → 像素偏差 (480-x, 270-y) 代入针孔模型换算成米
```

像素偏差到实际偏差的换算（`cx = 480, cy = 270` 为 960×540 图像中心）：

$$
\Delta x = \frac{e_y \cdot S_x \cdot z}{W \cdot f_x}, \qquad
\Delta y = \frac{e_x \cdot S_y \cdot z}{H \cdot f_y}
$$

其中 $S_x=3.2$、$S_y=2.4$（传感器尺寸 mm），$f_x=4.476$、$f_y=5.96$（标定焦距），$z$ 取当前飞行高度。结果封装成自定义消息 `offb/Circle{float32 circle_x, circle_y}` 发布到 `/circle_center`。

### 2.5 投放机构串口协议

`test.cpp` 是 ROS → Arduino 的桥，订阅 `/servo`（`std_msgs/UInt8`），按单字节下发：

| 字节 | 含义 |
| --- | --- |
| `1` / `2` / `3` | 打开对应的 1 / 2 / 3 号货舱舵机 |
| `6` | 还原全部舵机（节点退出时也会补发一次） |
| 其他 | 忽略 |

串口默认 `/dev/arduino`（可用 `throw_serial_port` 参数改成 `/dev/ttyACM0`），波特率 9600。`/dev/arduino` 是靠 udev 规则固定出来的别名，避免 USB 插拔后端口在 `ttyACM0/ttyACM1` 之间跳变——具体做法见操作手册第九章。

### 2.6 网络与地面站

Nano 与地面站各自在 `~/.bashrc` 里导出 `ROS_MASTER_URI` / `ROS_IP`，并在 `/etc/hosts` 里互加主机名，才能跨机器跑 ROS。QGC 通过 MAVROS 的 `gcs_url` 参数（`udp-b://@<地面站IP>`）与飞控建立链路。这部分完整步骤（含静态 IP、DHCP 自动分配、截图）在 `02_技术文档/ROS启动与联网/ros启动/`。

---

## 3. 代码详解

工作空间位于 `03_代码/ros_ws/`，`src/` 下有 5 个包：

| 包 | 来源 | 说明 |
| --- | --- | --- |
| `offb` | 本项目主要工作（基于 XTDrone / `px4_command` 的 offboard 框架改写） | 飞控控制、视觉识别、串口投放 |
| `common/msgs`（包名 `offb_msgs`） | 同上，配套消息定义 | `offb` 依赖的 `DroneState`、`AttitudeReference` 等消息 |
| `vision_to_mavros` | 第三方 [thien94/vision_to_mavros](https://github.com/thien94/vision_to_mavros) | T265 VIO → `/mavros/vision_pose/pose` |
| `realsense-ros` | 第三方 IntelRealSense（`realsense2_camera` 2.3.2） | T265 驱动 |
| `ddynamic_reconfigure` | 第三方（`kinetic-devel` 分支，0.4.1） | 动态参数，`vision_to_mavros` 的依赖 |

### 3.1 `offb` 包中被编译的节点

`offb/CMakeLists.txt` 里实际 `add_executable` 的目标：

| 可执行文件 | 源文件 | 作用 |
| --- | --- | --- |
| `offb_node` | `src/offb.cpp` | 通用多点 offboard 示例：stdin 输入航点后逐点飞行、末段速度下降落地 |
| `com_node` | `src/com.cpp` | **比赛主程序**：读航点 → 升 → 平飞 → 降 → 投放，循环 |
| `node_flyput_node` | `src/node_flyput.cpp` | **单点定投**：盲飞到固定点 + `/circle_center` 纠偏后降落投放 |
| `cycle_detect_new_node` | `src/cycle_detect_new.cpp` | 圆（靶环）检测，发布 `/circle_center` |
| `send_info_node` | `src/send_info.cpp` | 未进入 OFFBOARD 时持续发设定点，防掉模式 |
| `set_mode_node` | `src/set_mode.cpp` | 键盘状态机：0=Arm 1=TAKEOFF 2=OFFBOARD 3=LAND 4=POSCTL 5=MISSION 6=LOITER 7=Disarm |
| `showinfo_node` | `src/showinfo.cpp` | 终端打印连接/解锁/模式/位置/速度/四元数 |
| `test_node` | `src/test.cpp` | 串口桥：`/servo` → Arduino，驱动舵机投放 |
| `servo_control_node` | `src/servo_control.cpp` | 手动输入 1/2/3/6 触发舵机 |
| `mission_node` | `src/mission.cpp` | 空壳（只打印 Hello world），占位 |

### 3.2 未被编译的文件（历史遗留 / 草稿）

| 文件 | 状态 |
| --- | --- |
| `src/square_detect.cpp`（在 `src/` 根目录，不属于任何包） | 方块检测版本，与圆检测同架构，发布 `/square_center`；未加入 `offb` 的 CMake，需手动加 target 才能编译 |
| `src/cycle_detect_new_10_26.cpp` | 10/26 版本，用 `desire_z` 参数代替实时高度 |
| `src/landing_quadrotor.cpp` + `include/landing_quadrotor.h` | 基于 ArUco 的精准降落 PID（`bingo` 的 px4 二维码降落方案），CMake 中已整段注释；依赖的 `offb/ArucoInfo.msg` 并不存在，无法直接编译 |
| `src/takeoff_test.cpp` | 直接发 `ActuatorControl` 推力起飞测试（`take_off_test.launch` 引用的 `takeoff_node` 也没有对应 target） |
| `src/fly.cpp` | 只写了一半的草稿，语法不完整，不能编译 |
| `include/auto_2d_nav.h`、`include/math_utils.h`、`include/px4_control_cfg.h`、`include/state_from_mavros.h` | 从 `px4_command` / XTDrone 摘出的通用工具与状态订阅库 |

### 3.3 launch 文件

| launch | 跑在哪 | 组合 |
| --- | --- | --- |
| `remote_uav.launch` | Nano | `mavros/px4.launch` + `rs_t265.launch` + `t265_tf_to_mavros.launch` + 串口 + `cam.py` + `cycle_detect_new_node` |
| `remote_station.launch` | 地面站 | `send_info` + `com_node` + `showinfo` + `set_mode` + `servo_control` |
| `remix.launch` | 地面站 | `send_info` + `node_flyput_node`（单点定投）+ `showinfo` + `set_mode` + `cam.py` + `cycle_detect_new_node` |
| `com.launch` / `com_test.launch` | 地面站 | `com_node` + 串口 + 舵机控制；`com_test` 把设定点话题 remap 到 `/fuckoff` 做隔离测试 |
| `control.launch` | 地面站 | 只跑主控 + 显示 + 模式切换 + 串口（`desire_z=2`） |
| `condition_remix.launch` | — | 只跑相机 + `targetring_write.py`，纯视觉调试 |
| `test_serial.launch` / `take_off_test.launch` / `test.launch` | — | 串口、起飞、最小节点的单点测试 |

`desire_z`（巡航高度）在不同 launch 里是 0.5 / 1.0 / 1.4 / 2.0 / 5.0 m——按不同场地与调试阶段改的，**上机前必须确认当前用的是哪个值**。

### 3.4 Python 脚本

| 脚本 | 作用 |
| --- | --- |
| `cam.py` | Jetson CSI 相机 GStreamer 管线（`nvarguscamerasrc` → 960×540 BGR）发布 `/camera/rgb/image_raw` |
| `targetring_write.py` | HoughCircles 原型，只打印像素偏差 |
| `new_target.py` | HoughCircles 原型，直接发布 `offb/Circle` |
| `multirotor_communication.py` | 来自 XTDrone 的多机通信/设定点封装（未在比赛中使用） |
| `multirotor_keyboard_control.py` | 来自 XTDrone 的键盘遥控（未在比赛中使用） |

---

## 4. 如何复现

### 4.1 环境

- Jetson Nano：Ubuntu 18.04 + ROS Melodic + OpenCV 4（`CMakeLists.txt` 硬编码了 `/usr/lib/aarch64-linux-gnu/cmake/opencv4`）
- 地面站：Ubuntu（虚拟机即可）+ ROS Melodic
- 依赖：`mavros`、`mavros_msgs`、`cv_bridge`、`image_transport`、`serial`、`Eigen3`、`realsense2_camera`、`librealsense2`

### 4.2 编译

```bash
cd 03_代码/ros_ws
catkin_make
source devel/setup.bash
```

> 第三方包中 `realsense-ros` 和 `ddynamic_reconfigure` 保留了各自的 `.git`，版本与 2022 年现场一致；`vision_to_mavros` 是直接拷入的源码。

### 4.3 启动顺序

1. **Nano**：`roslaunch offb remote_uav.launch`
2. 观察终端里的位置信息是否随手动移动而**同向同幅**变化（T265 定点是否正常）。位置抖动、数据为 0 或更新迟缓 → 不要起飞。
3. 把飞机放回物理原点，确认 x/y/z 三轴都接近 0（小数点后两位）。
4. **地面站**：`roslaunch offb remote_station.launch`，会弹出 5 个终端。
5. 在模式切换终端输入 `2`（切 OFFBOARD），再输入 `0`（Arm）。
6. 在航点终端按提示输入航点数量与 x/y 坐标。
7. 投放：自动（`com_node` 流程里 `unload()` 会发 `/servo`）或手动在舵机终端输入 `1/2/3/6`。

### 4.4 安全须知（摘自操作手册，务必遵守）

- **解锁后必须在 5 秒内切到 OFFBOARD**，否则飞控会自动上锁导致起飞失败；**不要用 AUTO.TAKEOFF**。
- 飞行时至少 3 人在场：1 人握遥控器、1 人操作地面站、1 人准备手接。
- 异常（抖动过大、高度过高、冲向人群）→ 立即拨 **emkill** 开关（遥控器通道 9，右上角 B 开关），断电前不要拨回。
- 校准电调时**必须卸下螺旋桨**。
- 修改 `desire_z` 等参数后必须 `catkin_make` 重新编译才会生效。
- 地面站报错时可跳过电源/USB/安全开关检查：`CBRK_SUPPLY_CHK=894281`、`CBRK_USB_CHK=197848`、`CBRK_IO_SAFETY=22027`。

---

## 5. 已知问题与历史遗留

这些是归档时保留的原样问题，**没有修改代码**，仅记录以免后面踩坑：

1. `offb/CMakeLists.txt` 末尾 `install(TARGETS ...)` 的目标列表被整段注释掉，只剩下 `ARCHIVE/LIBRARY/RUNTIME DESTINATION`。`catkin_make` 默认不执行 install，所以当年没影响；若要 `catkin_make install`，建议先把这段删掉。
2. `offb` 依赖 `offb_msgs`，而它由 `src/common/msgs` 提供——编译顺序上 `common` 必须先于 `offb`（`catkin_make` 一般能自动处理；若只编单包，用 `catkin_make --only-pkg-with-deps offb`）。
3. `remote_uav.launch` 里的串口默认是 `/dev/ttyACM0`，`remix.launch` / `com.launch` 用的是 udev 别名 `/dev/arduino`，两台机器上要分别配好。
4. `landing_quadrotor.cpp` 依赖的 `offb/ArucoInfo.msg` 不存在，`take_off_test.launch` 引用的 `takeoff_node` 也没有编译目标——这几个是半成品，不要直接 `roslaunch`。
5. 视觉部分的焦距 `fx=4.476 / fy=5.96` 和传感器尺寸是按当时那台 CSI 相机标定的，换相机必须重新标定。
6. 检测代码用 `(0, 0)` 作「没检测到」的哨兵值（`if((center.x!=0)&&(center.y!=0))`）：圆检测里靠 `min_radius < 8192` 判断是否找到轮廓，方块检测里靠中心是否为 `(0,0)`。没有多帧一致性校验或置信度过滤——画面里出现一个符合判据的干扰轮廓，就会立刻把它的偏差发给飞控。

---

## 6. 资料目录索引

```
drone/
├── README.md                      本文件
├── CLEANUP-REPORT.md              去重与整理报告（删了什么、为什么）
│
├── 01_竞赛材料/                    154 MB / 18 个文件
│   ├── 规则与赛题/                 市赛第二轮通知、补充通知、各赛道评分规则、命题文档模板
│   ├── 参赛文档/                   答辩PPT-智能配送无人机.pptx、场景设置与任务命题-智能配送无人机.docx、
│   │                             参赛材料打包-已损坏.zip（见 CLEANUP-REPORT 5.4）
│   ├── 答辩与比赛视频/              预答辩.mp4、飞行测试.mp4
│   ├── 奖状/                      校赛一等奖奖状.jpg
│   └── 物料与结构/                 wuliao.stl（物料三维模型）
│
├── 02_技术文档/                    57.5 MB / 26 个文件
│   ├── 操作手册/                   无人机操作说明 0925/0928/1004/1006 四版、
│   │                             地面站连接配置.pdf、地面站与Nano配置.pages、emkill 截图
│   └── ROS启动与联网/ros启动/      联网配置截图、ROS启动命令.pdf、路由器连接说明
│
├── 03_代码/ros_ws/                102.6 MB / 253 个文件（catkin 工作空间）
│   └── src/{offb, common, vision_to_mavros, realsense-ros, ddynamic_reconfigure}
│
├── 04_联调录屏/                   3.4 GB / 16 个文件（2022-10-14 ~ 2022-12-17，含索引与校验和）
│                                  逐段索引与 SHA256 见该目录 README.md；其中 7 段已发布到 Release
├── 05_项目管理课程/                916 MB / 72 个文件（讲义与考题已移除，见 `课件概要.md`）
└── 06_归档/                       6.1 MB
    ├── offb_1015_twodetect.zip    10/15 的旧快照（含当时两套检测并存、VS 工程文件）
    └── offb-2022-10-28变体/        废纸篓里 3 个与现行版本不同的文件
```

### 联调录屏的文件名前缀

录屏是当时每次调完随手存的，前缀就是自评结果：

| 前缀 | 含义 |
| --- | --- |
| `[final]` | 文件名标注为 final 的最终版调试（483 MB，最完整的一段） |
| `[right]` | 定点/识别结果正常 |
| `[useful]` | 有参考价值的中间过程 |
| `[nodetected]` | 名字表明当时没检测到目标 |
| `[fail]` | 失败记录（10-14、11-21、12-03 三次） |

其中 `[usefulUbuntu - VMware Workstation 2022-11-09 16-04-38.mp4` 少了一个右方括号 `]`，是原始文件名，未改动。

### 联调录屏

14 段录屏共 26 分钟，记录了从首次联调到最终版的全过程。其中 7 段
（`final` / `right` × 2 / `fail` × 3 / `nodetected`，1.71 GB）发布在
[Release drone-2022](https://github.com/yicongl1/Drone-Delivery-2022/releases/tag/drone-2022)，
其余 7 段过程记录未公开。逐段索引见 [`04_联调录屏/`](04_联调录屏/README.md)。

---

## 7. 项目管理课程部分

同一学期，我们把这套无人机配送项目当作**项目管理课（法语授课）的小组课题**（Groupe 13），围绕它完成了 PM 的全套交付物。

| 目录 | 内容 |
| --- | --- |
| `小组作业/group/` | `GANTT.pod`（GanttProject 甘特图）、`PPT-风险管理.ppt`、`PPT-资源管理.pptx`、`PPT-进度安排.pptx`、`PPT-沟通管理.pptx`、`关于开通无人机物流服务的问卷调查报告.docx`、`展示视频-过程版.mov` |
| `小组作业/group/final/` | 最终交付：`展示PPT.pptx`、`展示视频-提交版.mp4`、`宣传片.mp4`、`宣传单-1.pdf`、`宣传单-2.jpeg`、`海报.png` / `海报.jpeg` |
| `展示视频素材/PPT视频/` | 每位组员分头录制的讲解片段与讲稿，统一命名 `narration-01..08`（`视频/` 是片段，`文稿/` 是对应讲稿；04 是中法双语旁白稿） |
| `展示视频素材/无人机视频/` | 宣传片的素材：产品建模/贴图截图、QGC 界面、参考视频，以及按句切好的法语配音 `音频/`（含 `音频2`、`音频6` 两版方案） |
| `周安排/` | 五份周计划（`周安排-0915-0922.rtf` … `周安排-1020-1027.rtf`），按 SP1~SP6 分工到人，含截止时间 |
| `课件概要.md` | 课程讲义（C01–C10）、练习、复习资料与历年考题的**索引**。原件含他人版权内容，已移除 |

宣传片的法语文案（`法语音频要求.txt`）把技术方案讲成了产品故事：支线运输、最后 1 公里、航空测绘识别、Jetson Nano 作协同计算机、T265 做避障与定位、QGC 校准监控。

---

## 8. 参考资料

- 个人网站上的比赛记录：<https://yicongl1.github.io/competitions/drone/>
- PX4 OFFBOARD 模式：<https://docs.px4.io/main/en/flight_modes/offboard.html>
- MAVROS：<https://github.com/mavlink/mavros>
- vision_to_mavros：<https://github.com/thien94/vision_to_mavros>
- realsense-ros：<https://github.com/IntelRealSense/realsense-ros>
- XTDrone：<https://github.com/robin-shaun/XTDrone>

---

## 附：整理说明

- 原始目录为 `src/ + 智能无人机/ + 项目管理/ + 散落文件`，共 630 个文件 / 4.7 GB。
- 整理后为 6 个编号目录，391 个文件 / 约 4.5 GB。累计删除 244 个文件：180 个 macOS/Office 垃圾文件、43 个逐字节重复、1 个回收站元数据、20 个含他人版权的课程课件；逐条记录在 [CLEANUP-REPORT.md](CLEANUP-REPORT.md)。
- 文件名统一成「主题/内容」的可读形式，队友姓名替换为 `narration-01..08`、`预答辩.mp4` 之类的中性命名；文档正文里的姓名替换为 `成员A`–`成员H`，内嵌作者字段统一为 `group`。
- **本仓库只跟踪 313 个文件 / 295 MB**：联调录屏、比赛与小组视频约 4.2 GB 不进 git 历史（录屏走 Release），规则见 `.gitignore`。
- 源码逻辑、文档内容、视频画面均未改动。
