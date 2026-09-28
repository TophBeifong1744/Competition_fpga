# #20 BL-H6-720p 摄像头证据入口（2026-09-28）

对应 [Issue #20](https://github.com/TophBeifong1744/Competition_fpga/issues/20)；负责人 C/hsc119，非作者复核 A/TophBeifong1744。本目录记录实际交付和缺口，不把作者自检或口头事实改写成成员批准。

## 原始资料与可确认范围

| 原件 | SHA-256 | 资料所支持的内容 |
| --- | --- | --- |
| [BL-H6-720p V1.5 承认书](../../reference/camera/bl-h6-720p-spec-v1.5.pdf) | `e4424017def678b6c29bc37106d1419fb2df225eced1afb195e8f646d1084540` | 型号、USB 2.0、DC 5 V、工作电流 `<200 mA`、YUV/MJPG、1280×720 档位及标称 30 fps、约 60° 视场；第 4 页为外形安装尺寸。属于厂家规格，不是该实物实测。 |
| [USB 摄像头二次开发文档](../../reference/camera/usb-camera-uvc-development-note.pdf) | `f58d3bfa6c83175dc1e5bfd594f070976e29ca8ecf08c1da3ff743638386113b` | UVC 概念和 Android 示例。不是 BL-H6 专属 Windows 驱动源码，也不是 Zynq Host 驱动证据。 |

原件由用户于 2026-09-28 提供，复制入库后字节哈希与用户文件相同。承认书首页有产品型号，但尚无实物标签与电脑 USB VID/PID 的相互对应记录；资料也没有载荷质量或供电实测值。

## 现场事实与独立核验

| 项目 | 目前事实 | 等级 |
| --- | --- | --- |
| 接口与显示位置 | 用户说摄像头通过 USB 接电脑，画面在电脑输出。 | `USER_REPORTED` |
| 装配 | 用户说摄像头已固定在双轴转台上，转动时 USB 线不会缠绕。 | `USER_REPORTED` |
| 已试用 | 用户说以前实际验证过摄像头能正常显示；当前未插好。 | `USER_REPORTED`，无原始图像/日志归档 |
| 本机设备枚举 | 2026-09-28 `pnputil /enum-devices /class Camera /connected` 只列 `Chicony USB2.0 Camera`、`usbvideo.inf`，实例 `USB\VID_04F2&PID_B729&MI_00...`。 | `HOST_OBSERVED`，只证明笔记本内置设备，**不是 BL-H6** |
| 供电 | 厂家标称 USB 5 V、工作 `<200 mA`；实际 USB 口、电压/电流未测。 | `DATASHEET_ONLY` |
| 图像与异常停止 | 暂无可关联这只实物和候选版本的 PNG/采集日志；转台图像场景、USB 中断与异常停止记录未归档。 | `UNVERIFIED` |

## 本地候选与待补实证

[电脑端 UVC 最小链路](../../../software/camera/README.md)已准备：电脑系统 USB 类驱动 → 浏览器选择摄像头 → 实时预览 → 无损 PNG + JSON 记录 → SHA-256/尺寸核验。该链路不接 J4 并口相机网络，因此不会与四麦转接板的 J4-29/31/33/35 形成同脚驱动争用；实际转台 PWM 接线仍沿 #19 的独立结论，不从 USB 路径猜板卡引脚。

本地静态与校验器检查（2026-09-29）：提取网页内 JavaScript 后由 Node `--check` 解析通过；`python -B -m unittest discover -s software/camera -p 'test_*.py' -v` 为 3/3 PASS，其中错误 SHA-256 与错误尺寸负例均被拒绝。这些是**软件候选自检**，不是实际 BL-H6 取图或成员批准。

当前待用户提供或现场产生：

1. 接入 BL-H6 后保存其设备枚举和一组同名真实 `.png`/`.json`；如设备显示通用名称，以插拔前后差异核对 VID/PID 和摄像头选择。
2. 相同光照/目标下保存静止、水平动作后、垂直动作后的图像与命令/停稳记录；用户已报告机械到位，图像效果仍需单独记录。
3. 保存一次异常停止或 USB 中断日志，并确认停止后不继续宣称画面有效。声源联动须另核对 A 提供的有效/TTL 方向接口；未接入时只报告独立相机和转台效果。

本地代码、资料及用户现场描述可提交作者候选。**摄像头功能验收、转台带载图像效果与 A 的非作者批准尚未完成**，不得用本目录或 #19 的板测声明替代。
