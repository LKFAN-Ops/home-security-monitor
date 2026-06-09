#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import cv2
import base64
import json
import re
import requests

API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
if not API_KEY:
    print("[错误] 请设置环境变量 DASHSCOPE_API_KEY")
    print("[提示] 在 PowerShell 中执行: $env:DASHSCOPE_API_KEY = \"你的API Key\"")
    raise SystemExit(1)

def encode_image_to_base64(frame):
    ret, buffer = cv2.imencode(".jpg", frame)
    if not ret:
        return None
    return base64.b64encode(buffer).decode("utf-8")

def qwen_vehicle_detect(frame):
    img_b64 = encode_image_to_base64(frame)
    if not img_b64:
        return []

    prompt = """只检测图片中正在运动的车辆（汽车、卡车、公交车、摩托车），
忽略路边静止车辆、静止景物，严格按照以下JSON格式输出，不要多余文字、不要markdown：
[{"bbox_2d":[x1,y1,x2,y2],"label":"车型类别"}]
bbox坐标为整数像素值，仅返回运动车辆目标"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "qwen-vl-plus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                    {"type": "text", "text": prompt}
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1500
    }

    try:
        response = requests.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=data,
            proxies={"http": None, "https": None},
            timeout=30
        )
        result = response.json()
        res_text = result["choices"][0]["message"]["content"].strip()
        print("模型返回：", res_text)

        if res_text.startswith("```"):
            res_text = res_text.replace("```json", "").replace("```", "").strip()

        # 解析JSON，损坏时用正则提取
        try:
            detect_data = json.loads(res_text)
        except json.JSONDecodeError:
            pattern = r'\{"bbox_2d":\s*\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\],\s*"label":\s*"([^"]+)"\}'
            matches = re.findall(pattern, res_text)
            detect_data = [
                {"bbox_2d": [int(m[0]), int(m[1]), int(m[2]), int(m[3])], "label": m[4]}
                for m in matches
            ]

        if not isinstance(detect_data, list):
            return []

        # 过滤无效框
        valid = []
        for obj in detect_data:
            bbox = obj.get("bbox_2d", [])
            if len(bbox) != 4:
                continue
            x1, y1, x2, y2 = bbox
            w = x2 - x1
            h = y2 - y1
            if w > 640 * 0.8 or h > 480 * 0.8:
                continue
            if w < 5 or h < 5:
                continue
            valid.append(obj)

        return valid

    except Exception as e:
        print("检测异常：", e)
        return []

def draw_result(frame, obj_list, scale_x=1.0, scale_y=1.0):
    for obj in obj_list:
        bbox = obj.get("bbox_2d", [])
        label = obj.get("label", "vehicle")
        if len(bbox) != 4:
            continue
        x1 = int(bbox[0] * scale_x)
        y1 = int(bbox[1] * scale_y)
        x2 = int(bbox[2] * scale_x)
        y2 = int(bbox[3] * scale_y)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, max(y1 - 10, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    return frame

def main():
    cap = cv2.VideoCapture("highway.mp4")
    if not cap.isOpened():
        print("视频读取失败，请检查路径！")
        return

    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_w, target_h = 640, 480
    scale_x = orig_w / target_w
    scale_y = orig_h / target_h

    frame_count = 0
    cache_result = []

    cv2.namedWindow("通义千问大模型-运动车辆检测", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("通义千问大模型-运动车辆检测", 960, 540)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % 10 == 0:
            small_frame = cv2.resize(frame, (target_w, target_h))
            cache_result = qwen_vehicle_detect(small_frame)
            print(f"第{frame_count}帧，检测到 {len(cache_result)} 个目标")

        show_frame = draw_result(frame.copy(), cache_result, scale_x, scale_y)
        cv2.imshow("通义千问大模型-运动车辆检测", show_frame)

        if cv2.waitKey(25) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()