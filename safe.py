# -*- coding: utf-8 -*-
"""
家庭安全监控提醒工具
功能：
  1. 支持摄像头实时监控 / 本地视频文件输入
  2. 使用 YOLOv8 人脸检测模型，自动检测画面中是否有人进入
  3. 检测到人脸时：屏幕红色警告提示 + 控制台打印提醒时间戳
  4. 连续检测"入侵冷却"机制，避免重复刷屏提醒
  5. 每隔 N 帧调用通义千问大模型，自动描述当前画面场景
  6. 自动保存带检测框的视频文件 + 事件记录 TXT 报告

使用方法：
  1. 填写下方 ===配置区=== 中的参数（API 密钥、输入源等）
  2. 确保已安装依赖：pip install ultralytics opencv-python openai
  3. 运行：python home_security_monitor.py

项目来源：人工智能视觉综合实训手册 第13课 综合项目整合
模型文件：yolov8n-face-lindevs.pt（官方人脸专用权重，无 omegaconf 警告）
"""

import os
import cv2
import time
import base64
import re
import requests
from ultralytics import YOLO
from openai import OpenAI

# ========================== 修改此处配置参数 ==========================
API_KEY        = os.environ.get("DASHSCOPE_API_KEY", "")  # 通义千问 API Key（优先读取环境变量，留空则跳过 AI 描述）
INPUT_SOURCE   = 0                            # 0=本地摄像头，或填写视频路径如 "test_video.mp4"
MODEL_PATH     = "yolov8n-face-lindevs.pt"   # 人脸检测模型路径
CONF_THRESH    = 0.45                         # 人脸检测置信度阈值（0~1，越高越严格）
AI_INTERVAL    = 30                           # 每隔多少帧调用一次大模型描述（降低 API 消耗）
ALERT_COOLDOWN = 3.0                          # 触发提醒后的冷却秒数，避免连续刷屏
OUTPUT_VIDEO   = "监控录像_带检测框.mp4"       # 输出视频文件名（留空则不保存）
OUTPUT_REPORT  = "安全监控事件报告.txt"        # 输出报告文件名
# =====================================================================


# ---------- 工具函数 ----------

def download_model(path: str):
    """若模型文件不存在或损坏则重新下载"""
    need_download = False

    if not os.path.exists(path):
        need_download = True
    else:
        # 校验文件大小：正常模型文件至少 5MB，残缺文件直接删除重下
        size_mb = os.path.getsize(path) / (1024 * 1024)
        if size_mb < 5:
            print(f"[初始化] 检测到模型文件损坏（{size_mb:.1f}MB），正在删除并重新下载...")
            os.remove(path)
            need_download = True

    if need_download:
        print(f"[初始化] 正在下载模型 {path}，请稍候...")
        url = "https://github.com/lindevs/yolov8-face/releases/download/v1.0.0/yolov8n-face-lindevs.pt"
        try:
            res = requests.get(url, stream=True, timeout=60)
            res.raise_for_status()
            with open(path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            print(f"[初始化] 模型下载完成！文件大小：{size_mb:.1f}MB")
        except Exception as e:
            print(f"[错误] 自动下载失败：{e}")
            print("[提示] 请手动下载模型文件，放到脚本同目录：")
            print("  https://github.com/lindevs/yolov8-face/releases/download/v1.0.0/yolov8n-face-lindevs.pt")
            raise SystemExit(1)


def frame_to_base64(frame) -> str:
    """将 OpenCV 帧转为 base64 字符串，用于大模型 API 传图"""
    _, buffer = cv2.imencode(".jpg", frame)
    return base64.b64encode(buffer).decode("utf-8")


def clean_text(text) -> str:
    """清洗大模型返回的文本，去除多余格式符号"""
    text = str(text).strip()
    text = re.sub(r"^```.*?\n|\n```$", "", text, flags=re.DOTALL)
    return text


def describe_scene(frame) -> str:
    """
    调用通义千问视觉大模型，对当前帧进行画面描述。
    使用阿里云新版 OpenAI 兼容接口（dashscope 已弃用）。
    """
    b64 = frame_to_base64(frame)
    prompt = (
        "这是一个家庭安全监控画面截图。"
        "请简洁描述：画面中有几个人、人物的大致位置、正在做什么、"
        "是否存在可疑行为或异常情况。回答控制在50字以内。"
    )
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        res = client.chat.completions.create(
            model="qwen-vl-max",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }]
        )
        return clean_text(res.choices[0].message.content)
    except Exception as e:
        return f"[大模型调用失败: {e}]"


# ---------- 主程序 ----------

def main():
    # 1. 初始化环境
    download_model(MODEL_PATH)

    # 2. 加载人脸检测模型
    #    来源：手册第6课 + notebook 12yolo_大模型实现人脸识别.ipynb
    print("[初始化] 加载人脸检测模型...")
    model = YOLO(MODEL_PATH)
    print("[初始化] 模型加载完成！")

    # 3. 打开视频源（摄像头 or 视频文件）
    #    来源：手册第10课 摄像头实时检测
    cap = cv2.VideoCapture(INPUT_SOURCE)
    if not cap.isOpened():
        print(f"[错误] 无法打开视频源：{INPUT_SOURCE}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source_label = "摄像头" if INPUT_SOURCE == 0 else str(INPUT_SOURCE)
    print(f"[初始化] 已打开 {source_label}，分辨率 {w}x{h}，帧率 {fps:.1f}")

    # 4. 初始化视频保存器（来源：手册第7课）
    out = None
    if OUTPUT_VIDEO:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(OUTPUT_VIDEO, fourcc, fps, (w, h))
        print(f"[初始化] 录像将保存至：{OUTPUT_VIDEO}")

    # 5. 状态变量
    frame_idx        = 0          # 帧计数器
    last_alert_time  = 0          # 上次触发提醒的时间戳
    event_log        = []         # 事件日志列表
    total_detections = 0          # 累计检测到人脸的帧数

    print("\n===== 家庭安全监控系统已启动，按 Q 键退出 =====\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[提示] 视频读取结束。")
            break

        # 6. YOLOv8 人脸检测
        #    置信度阈值来源：手册第8课 模型调优
        results  = model(frame, conf=CONF_THRESH, verbose=False)
        face_cnt = 0

        for r in results:
            for box in r.boxes:
                # 提取框坐标、置信度（来源：09车辆检测notebook / 手册第5课）
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = box.conf[0].item()
                face_cnt += 1

                # 绿色检测框 + 置信度标签
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"face {conf:.2f}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)

        # 7. 左上角显示实时人数（来源：手册第10课）
        cv2.putText(frame, f"People: {face_cnt}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.1, (0, 0, 255), 2)

        # 8. 检测到人脸 → 安全警告提示（核心功能：有人进入→自动提示）
        now = time.time()
        if face_cnt > 0:
            total_detections += 1

            # 冷却时间内不重复触发
            if now - last_alert_time >= ALERT_COOLDOWN:
                last_alert_time = now
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                alert_msg = f"[{ts}] ⚠️  检测到 {face_cnt} 人进入画面！"
                print(alert_msg)
                event_log.append(alert_msg)

            # 画面左下角红色警告文字
            cv2.rectangle(frame,
                          (0, h - 60), (w, h),
                          (0, 0, 200), -1)           # 红色底栏
            cv2.putText(frame, "⚠  ALERT: Person Detected!",
                        (10, h - 18),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9, (255, 255, 255), 2)

        # 9. 每隔 AI_INTERVAL 帧调用大模型描述画面
        #    来源：手册第12课 视频抽帧 + 大模型智能摘要
        if frame_idx % AI_INTERVAL == 0 and API_KEY:
            ts      = round(frame_idx / fps, 1)
            desc    = describe_scene(frame)
            log_msg = f"[{ts}s] 人脸数={face_cnt} | 大模型描述：{desc}"
            print(log_msg)
            event_log.append(log_msg)

        # 10. 写入录像
        if out is not None:
            out.write(frame)

        # 11. 实时显示窗口
        cv2.imshow("家庭安全监控系统 | 按 Q 退出", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\n[退出] 用户按下 Q 键，程序结束。")
            break

        frame_idx += 1

    # ---------- 收尾 ----------
    cap.release()
    if out:
        out.release()
    cv2.destroyAllWindows()

    # 12. 保存事件报告（来源：手册第13课 最终完整项目）
    if event_log and OUTPUT_REPORT:
        with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
            f.write("===== 家庭安全监控事件报告 =====\n\n")
            for line in event_log:
                f.write(line + "\n")
        print(f"\n[完成] 事件报告已保存：{OUTPUT_REPORT}")

    print(f"[统计] 共处理 {frame_idx} 帧，其中 {total_detections} 帧检测到人脸。")
    print("===== 监控系统已关闭 =====")


if __name__ == "__main__":
    main()