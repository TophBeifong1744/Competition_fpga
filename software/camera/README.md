# #20 电脑端 USB 摄像头最小取图入口

本入口针对用户提供的 BL-H6-720p 资料及“USB 接电脑、画面在电脑输出”的方案。电脑操作系统负责 USB/UVC 类驱动；本页调用浏览器 `getUserMedia`，**不实现 Zynq USB Host 或 FPGA 并口相机驱动**。摄像头实际枚举和图像内容必须由实机运行证明。

## 运行

要求：装有 Python 3 的 Windows 电脑、支持摄像头权限的现代浏览器、已接入的实际 USB 摄像头。无需 Python 第三方包。

在本目录运行：

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

电脑浏览器打开 `http://127.0.0.1:8765/pc_uvc_capture.html`。点击“授权并列出摄像头”，在列表中**人工核对并选择实际 BL-H6**，再点击“打开预览”。默认严格请求 1280×720、目标 30 fps；不支持时改选 640×480/320×240 并如实记录实际档位。点击“保存当前帧与记录”，分别下载同名 `.png` 和 `.json` 到同一目录。点击“停止预览”检查流停止；若 USB 意外断开，可另存运行日志。网页不访问麦克风，也不上传图像。

核验下载文件：

```powershell
python verify_capture.py C:\path\to\camera-2026-09-28T00-00-00-000Z.json
```

成功输出 `FILE_INTEGRITY_PASS`、图像 SHA-256、尺寸和浏览器报告的设备标签；错误输出 `FAIL` 且进程退出码为 1。此核验只证明图像和记录内部一致，**不证明物理型号、实际供电电流、持续 30 fps、转台动作或声源联动**。

## 本地交付与板上效果分界

- `pc_uvc_capture.html` 是独立电脑端取图候选；用户点击授权、选择设备、预览、下载是现场操作。浏览器可列出内置摄像头，必须避免误选。
- 预览与 PNG 代表被浏览器解码后显示的画面；PNG 是无损保存的当前帧，**不是 USB 原始 MJPG/YUV 传输包**。记录中的 `fpsIdeal` 是请求，`negotiated.frameRate` 是浏览器报告，单帧不能证明持续帧率。
- 主机上若只有 `Chicony USB2.0 Camera`，不能将其采集结果冒充 BL-H6。`deviceId` 是浏览器内标识，记录中仅保存其 SHA-256；物理 VID/PID 需另由系统设备枚举和插拔对照确认。
- 电脑 USB 直连路径不占用 Zynq 底板 J4 并口相机针脚；转台 PWM/板卡与电脑取图仍是两条链路。#19 舵机结论不自动构成 #20 图像或联动效果。
- 如需作为 #20 图像效果证据，保留实际 BL-H6 的设备枚举、采集日志、同名 PNG/JSON，记录转台静止/水平/垂直或异常停止场景与对应命令。图像文件是否可公开需由用户先检查画面内容。

## 依赖依据

浏览器摄像头访问和枚举按 [W3C Media Capture and Streams](https://www.w3.org/TR/mediacapture-streams/)；`localhost` 安全上下文及权限要求见 [MDN getUserMedia](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia) 和 [MDN enumerateDevices](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/enumerateDevices)。这些 API 说明不能代替这只实物在当前电脑上的枚举和采集验证。
