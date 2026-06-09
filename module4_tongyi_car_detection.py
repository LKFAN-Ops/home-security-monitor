#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 模块四：基于通义千问视觉大模型的车流量计数及标注（修复版）

import cv2
import base64
import requests
import json
from datetime import datetime

import os

# 1. 配置通义千问API密钥（从环境变量读取）
API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    print("[错误] 请设置环境变量 DASHSCOPE_API_KEY")
    print("[提示] PowerShell: $env:DASHSCOPE_API_KEY = \"你的API Key\"")
    raise SystemExit(1)

# 2. 调用通义千问视觉API
def tongyi_vehicle_detection(frame):
    ret, buffer = cv2.imencode(".jpg", frame)
    image_base64 = base64.b64encode(buffer).decode("utf-8")

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    data = {
        "model": "qwen-vl-plus",
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": f"data:image/jpeg;base64,{image_base64}"
                        },
                        {
                            "text": (
                                "请检测图片中所有车辆，统计车辆数量，"
                                "并以JSON格式返回结果，格式如下：\n"
                                '{"count": 车辆数量, "vehicles": ['
                                '{"left": x坐标, "top": y坐标, "width": 宽度, "height": 高度}'
                                ']}\n只返回JSON，不要其他文字。'
                            )
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(data),
            proxies={"http": None, "https": None},
            timeout=30
        )
        result = response.json()
        return result
    except Exception as e:
        print(f"API请求失败：{e}")
        return {}


# 3. 解析通义千问返回结果
def parse_result(result):
    vehicles = []
    count = 0
    try:
        text = result["output"]["choices"][0]["message"]["content"][0]["text"]
        text = text.strip().strip("```json").strip("```").strip()
        data = json.loads(text)
        count = data.get("count", 0)
        vehicles = data.get("vehicles", [])
    except Exception as e:
        print(f"结果解析失败（当前帧跳过）：{e}")
    return count, vehicles


# 4. 主函数
def main():
    total_car_count = 0
    frame_interval = 10  # 每10帧调用一次API

    cap = cv2.VideoCapture("highway.mp4")  # 替换为你的视频路径
    if not cap.isOpened():
        print("视频读取失败，请检查路径是否正确！")
        return

    frame_idx = 0
    current_vehicles = []
    current_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 记录原始尺寸
        original_h, original_w = frame.shape[:2]

        # 缩放视频帧
        frame = cv2.resize(frame, (320, 240))
        frame_copy = frame.copy()
        new_h, new_w = frame.shape[:2]

        # 每隔frame_interval帧调用一次API
        if frame_idx % frame_interval == 0:
            result = tongyi_vehicle_detection(frame)
            current_count, current_vehicles = parse_result(result)
            total_car_count += current_count
            print(f"第{frame_idx}帧：检测到{current_count}辆车，累计{total_car_count}辆")

        # 按比例换算坐标，绘制标注框
        for vehicle in current_vehicles:
            try:
                scale_x = new_w / original_w
                scale_y = new_h / original_h
                left   = int(vehicle["left"]   * scale_x)
                top    = int(vehicle["top"]    * scale_y)
                width  = int(vehicle["width"]  * scale_x)
                height = int(vehicle["height"] * scale_y)

                cv2.rectangle(frame_copy, (left, top), (left + width, top + height), (0, 0, 255), 2)
                cv2.putText(frame_copy, "vehicle", (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            except Exception:
                pass

        # 显示累计车流量
        cv2.putText(frame_copy, f"Total: {total_car_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
        cv2.imshow("通义千问 - 车流量计数", frame_copy)

        frame_idx += 1
        if cv2.waitKey(25) & 0xFF == 27:
            break

    # 保存结果
    result_text = (
        f"实训时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"视频名称：highway.mp4\n"
        f"累计车流量：{total_car_count}"
    )
    with open("tongyi_car_flow_result.txt", "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"实训完成！累计车流量：{total_car_count}，结果已保存。")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()