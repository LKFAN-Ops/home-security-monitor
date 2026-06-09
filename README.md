# 家庭安全监控检测系统

基于 **YOLOv8 人脸检测** + **通义千问视觉大模型**的智能家庭安全监控系统。支持实时摄像头/视频文件监控、人脸检测报警、AI 场景描述、自动录像与事件报告生成。

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **实时人脸检测** | YOLOv8n-face 专用模型，精准识别人脸 |
| **声光报警** | 画面红色警告栏 + 控制台/日志提醒 |
| **AI 场景描述** | 每隔 N 帧调用通义千问 VL 大模型，智能描述画面内容 |
| **入侵冷却** | 可配置冷却时间，避免重复刷屏 |
| **自动录像** | 保存带检测框的监控录像（MP4） |
| **事件报告** | 自动生成 TXT 格式的安全事件日志 |
| **GUI 图形界面** | Tkinter 可视化界面，支持参数实时调整 |
| **PyInstaller 打包** | 可打包为独立 exe，脱离 Python 环境运行 |

---

## 🗂️ 项目结构

```
计算机视觉实训/
├── 🏠 家庭安全监控系统（主项目）
│   ├── safe.py              # CLI 版监控主程序
│   ├── safe_gui.py           # GUI 图形界面版
│   └── 家庭安全监控工具.spec  # PyInstaller 打包配置
│
├── 📦 辅助学习模块
│   ├── module1_edge_detection.py      # Canny/Sobel 边缘检测
│   ├── module2_edge_detection.py      # 通义千问车辆检测
│   ├── module3_car_flow_counter.py    # 帧差法车流量计数
│   ├── module4_tongyi_car_detection.py# 大模型车流量计数
│   ├── yolo.py                        # YOLOv8 车辆追踪计数
│   ├── fruit.py                       # 水果忍者体感游戏
│   └── test_api.py                    # 通义千问 API 连通性测试
│
├── build.bat              # 一键打包脚本
├── yolov8n-face-lindevs.pt # 人脸检测模型（自动下载）
├── highway.mp4             # 测试视频
└── data/                   # 测试图片
```

> **家庭安全监控系统**是本项目的核心，其余为计算机视觉实训过程中的辅助学习模块。

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- 摄像头（可选，也支持本地视频文件）

### 安装依赖

```bash
pip install ultralytics opencv-python openai requests pillow
```

### 运行

### 1. 配置 API Key（所有模块通用）

```bash
# PowerShell（推荐：设置用户环境变量）
[System.Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "sk-你的API密钥", "User")

# 或临时设置（仅当前会话有效）
$env:DASHSCOPE_API_KEY = "sk-你的API密钥"
```

> API Key 通过环境变量 `DASHSCOPE_API_KEY` 读取，**不会硬编码在代码中**，避免泄露风险。前往 [阿里云 DashScope](https://dashscope.aliyun.com/) 注册获取。

### 2. 运行

**CLI 命令行版：**

```bash
# 编辑 safe.py 中的配置参数（INPUT_SOURCE、CONF_THRESH 等）
python safe.py
```

**GUI 图形界面版：**

```bash
python safe_gui.py
```

---

## ⚙️ 配置说明（safe.py）

编辑 `safe.py` 中的配置区：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `INPUT_SOURCE` | 0=摄像头/视频文件路径 | `0` |
| `CONF_THRESH` | 人脸检测置信度 | `0.45` |
| `ALERT_COOLDOWN` | 报警冷却时间(秒) | `3.0` |
| `AI_INTERVAL` | AI 描述间隔(帧) | `30` |

---

## 📦 打包为独立 exe

```bash
# 一键打包（已配置 build.bat）
build.bat

# 或手动执行
pip install pyinstaller
pyinstaller 家庭安全监控工具.spec
```

打包后输出在 `dist/家庭安全监控工具/` 目录。

---

## 🧩 辅助模块一览

| 模块 | 技术 | 功能 |
|------|------|------|
| `module1` | Canny/Sobel | 边缘检测与车辆轮廓绘制 |
| `module2` | 通义千问 VL + | 基于大模型的运动车辆检测 |
| `module3` | 帧差法 | 视频车流量统计 |
| `module4` | 通义千问 VL + | 大模型车流量计数与标注 |
| `yolo.py` | YOLOv8 + DeepSORT | 车辆追踪与唯一计数 |
| `fruit.py` | OpenCV + 手势识别 | 水果忍者体感交互游戏 |

---

## 🛠️ 技术栈

- **人脸检测**: YOLOv8 (ultralytics)
- **视觉大模型**: 通义千问 Qwen-VL-Max / Qwen-VL-Plus
- **图像处理**: OpenCV
- **GUI**: Tkinter + Pillow
- **打包**: PyInstaller

---

## 📄 License

MIT
