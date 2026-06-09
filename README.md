<div align="center">
  <h1>🏠 家庭安全监控检测系统</h1>
  <p>
    <strong>基于 YOLOv8 人脸检测 + 通义千问视觉大模型的智能安防系统</strong>
  </p>
  <p>
    <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/YOLOv8-face-00C853?logo=ultralytics" alt="YOLOv8">
    <img src="https://img.shields.io/badge/Qwen--VL-阿里云-FF6F00?logo=alibabacloud" alt="Qwen-VL">
    <img src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv" alt="OpenCV">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

---

## 📸 系统预览

<div align="center">
  <img src="screenshots/monitor-preview.png" alt="家庭安全监控系统界面预览" width="800"/>
</div>

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 👤 **实时人脸检测** | YOLOv8n-face 专用模型，实时识别人脸并绘制检测框 |
| 🚨 **入侵报警** | 检测到人脸时画面红色警告 + 控制台日志提醒 |
| 🤖 **AI 场景描述** | 接入通义千问 VL 大模型，智能描述画面中的场景与行为 |
| ⏱️ **入侵冷却** | 可配置冷却时间，避免短时间内重复报警 |
| 📹 **自动录像** | 保存带检测框的完整监控录像（MP4 格式） |
| 📄 **事件报告** | 自动生成 TXT 格式安全事件日志 |
| 🖥️ **GUI 图形界面** | 基于 Tkinter 的可视化操作面板，参数实时可调 |
| 📦 **独立打包** | 支持 PyInstaller 打包为 exe，脱离 Python 环境 |

---

## 🗂️ 项目结构

```
📁 计算机视觉实训/
│
├── 🏠 家庭安全监控系统（主项目）
│   ├── safe.py                   # CLI 版监控主程序
│   ├── safe_gui.py               # GUI 图形界面版
│   └── 家庭安全监控工具.spec     # PyInstaller 打包配置
│
├── 📦 辅助学习模块
│   ├── module1_edge_detection.py           # Canny / Sobel 边缘检测
│   ├── module2_edge_detection.py           # 通义千问车辆检测
│   ├── module3_car_flow_counter.py         # 帧差法车流量计数
│   ├── module4_tongyi_car_detection.py     # 大模型车流量计数
│   ├── yolo.py                             # YOLOv8 车辆追踪计数
│   ├── fruit.py                            # 水果忍者体感游戏
│   └── test_api.py                         # 通义千问 API 测试
│
├── 📸 screenshots/              # 效果截图
├── build.bat                    # 一键打包脚本
└── README.md                    # 本文件
```

> **家庭安全监控系统**为本项目的核心，其余为实训过程中的辅助学习模块。

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 摄像头（可选，也支持本地视频文件）

### 安装依赖

```bash
pip install ultralytics opencv-python openai requests pillow
```

### 配置 API Key

所有模块统一通过环境变量 `DASHSCOPE_API_KEY` 读取 API Key，**无需在代码中填写**，避免泄露风险。

```powershell
# 推荐：设置为用户环境变量（持久化）
[System.Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "sk-你的API密钥", "User")

# 或临时设置（仅当前会话）
$env:DASHSCOPE_API_KEY = "sk-你的API密钥"
```

> 前往 [阿里云 DashScope](https://dashscope.aliyun.com/) 注册并创建 API Key。

### 运行

**CLI 版：**
```bash
python safe.py
```

**GUI 版：**
```bash
python safe_gui.py
```

---

## ⚙️ 配置参数（safe.py）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `INPUT_SOURCE` | `0`=摄像头 / 视频文件路径 | `0` |
| `CONF_THRESH` | 人脸检测置信度阈值 | `0.45` |
| `ALERT_COOLDOWN` | 报警冷却时间（秒） | `3.0` |
| `AI_INTERVAL` | AI 场景描述间隔（帧） | `30` |
| `OUTPUT_VIDEO` | 输出录像文件名 | `监控录像_带检测框.mp4` |
| `OUTPUT_REPORT` | 输出事件报告文件名 | `安全监控事件报告.txt` |

---

## 📦 打包为独立 exe

```bash
# 方式一：一键打包
build.bat

# 方式二：手动打包
pip install pyinstaller
pyinstaller 家庭安全监控工具.spec
```

打包后输出在 `dist/家庭安全监控工具/` 目录，可脱离 Python 环境直接运行。

---

## 🧩 辅助模块

| 模块 | 技术 | 功能 |
|------|------|------|
| `module1` | Canny / Sobel | 边缘检测与车辆轮廓绘制 |
| `module2` | 通义千问 VL+ | 基于大模型的运动车辆检测 |
| `module3` | 帧差法 | 视频车流量统计 |
| `module4` | 通义千问 VL+ | 大模型车流量计数与标注 |
| `yolo.py` | YOLOv8 + DeepSORT | 车辆追踪与唯一计数 |
| `fruit.py` | OpenCV + 手势识别 | 水果忍者体感交互游戏 |

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| [YOLOv8](https://github.com/ultralytics/ultralytics) | 人脸检测模型 |
| [通义千问 VL](https://dashscope.aliyun.com/) | 视觉大模型场景描述 |
| [OpenCV](https://opencv.org/) | 图像处理与视频流 |
| [Tkinter](https://docs.python.org/3/library/tkinter.html) + [Pillow](https://python-pillow.org/) | GUI 图形界面 |
| [PyInstaller](https://pyinstaller.org/) | 应用打包 |

---

## 📄 License

MIT
