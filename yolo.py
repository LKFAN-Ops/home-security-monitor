#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
from ultralytics import YOLO
from datetime import datetime

VEHICLE_CLASSES = {2: "Car", 3: "Moto", 5: "Bus", 7: "Truck"}

def main():
    model = YOLO("yolov8s.pt")
    model.fuse()

    cap = cv2.VideoCapture("highway.mp4")
    if not cap.isOpened():
        print("Video open failed, check path!")
        return

    counted_ids = set()
    total_car_count = 0
    frame_idx = 0
    infer_w, infer_h = 480, 480  # ✅ 从640降到480，速度更快

    cv2.namedWindow("YOLO - Vehicle Counter", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("YOLO - Vehicle Counter", 540, 960)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        orig_h, orig_w = frame.shape[:2]

        small = cv2.resize(frame, (infer_w, infer_h))
        scale_x = orig_w / infer_w
        scale_y = orig_h / infer_h

        # ✅ 每2帧推理一次，减少CPU压力
        if frame_idx % 2 == 0:
            results = model.track(
                small,
                persist=True,
                verbose=False,
                conf=0.45,
                iou=0.5,
                classes=list(VEHICLE_CLASSES.keys()),
                imgsz=480
            )[0]

            if results.boxes.id is not None:
                for box, track_id in zip(results.boxes, results.boxes.id):
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    tid = int(track_id)

                    if cls_id not in VEHICLE_CLASSES:
                        continue

                    if tid not in counted_ids:
                        counted_ids.add(tid)
                        total_car_count += 1

                    x1 = int(box.xyxy[0][0] * scale_x)
                    y1 = int(box.xyxy[0][1] * scale_y)
                    x2 = int(box.xyxy[0][2] * scale_x)
                    y2 = int(box.xyxy[0][3] * scale_y)
                    label = VEHICLE_CLASSES[cls_id]

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.putText(frame, f"{label} ID:{tid} {conf:.2f}",
                                (x1, max(y1 - 10, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        cv2.putText(frame, f"Total: {total_car_count}",
                    (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 4)
        cv2.putText(frame, f"Frame: {frame_idx}",
                    (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        cv2.imshow("YOLO - Vehicle Counter", frame)

        if frame_idx % 10 == 0:
            print(f"Frame {frame_idx}: total unique vehicles = {total_car_count}")

        if cv2.waitKey(1) & 0xFF == 27:
            break

    result_text = (
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Video: highway.mp4\n"
        f"Total unique vehicles: {total_car_count}"
    )
    with open("yolo_car_flow_result.txt", "w", encoding="utf-8") as f:
        f.write(result_text)
    print(f"Done! Total unique vehicles: {total_car_count}")
    print(f"Saved to yolo_car_flow_result.txt")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# import os
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
#
# import cv2
# from ultralytics import YOLO
# from deep_sort_realtime.deepsort_tracker import DeepSort
# from datetime import datetime
#
# VEHICLE_CLASSES = {2: "Car", 3: "Moto", 5: "Bus", 7: "Truck"}
#
# def main():
#     model = YOLO("yolov8s.pt")
#     model.fuse()
#
#     # ✅ 初始化DeepSORT追踪器
#     tracker = DeepSort(
#         max_age=30,          # 目标消失后保留ID的帧数
#         n_init=3,            # 连续检测3帧才确认为真实目标，减少误检
#         max_cosine_distance=0.3,  # 外观特征相似度阈值
#         nn_budget=100        # 特征库最大存储数量
#     )
#
#     cap = cv2.VideoCapture("highway.mp4")
#     if not cap.isOpened():
#         print("Video open failed, check path!")
#         return
#
#     counted_ids = set()
#     total_car_count = 0
#     frame_idx = 0
#     infer_w, infer_h = 480, 480
#
#     cv2.namedWindow("YOLO + DeepSORT - Vehicle Counter", cv2.WINDOW_NORMAL)
#     cv2.resizeWindow("YOLO + DeepSORT - Vehicle Counter", 540, 960)
#
#     while cap.isOpened():
#         ret, frame = cap.read()
#         if not ret:
#             break
#
#         frame_idx += 1
#         orig_h, orig_w = frame.shape[:2]
#
#         small = cv2.resize(frame, (infer_w, infer_h))
#         scale_x = orig_w / infer_w
#         scale_y = orig_h / infer_h
#
#         # YOLO检测
#         results = model.predict(
#             small,
#             verbose=False,
#             conf=0.45,
#             iou=0.5,
#             classes=list(VEHICLE_CLASSES.keys())
#         )[0]
#
#         # ✅ 将YOLO结果转为DeepSORT需要的格式
#         detections = []
#         for box in results.boxes:
#             cls_id = int(box.cls[0])
#             conf = float(box.conf[0])
#             if cls_id not in VEHICLE_CLASSES:
#                 continue
#             x1, y1, x2, y2 = map(float, box.xyxy[0])
#             # DeepSORT需要 [left, top, width, height] 格式
#             w = x2 - x1
#             h = y2 - y1
#             detections.append(([x1, y1, w, h], conf, cls_id))
#
#         # ✅ DeepSORT更新追踪
#         tracks = tracker.update_tracks(detections, frame=small)
#
#         for track in tracks:
#             if not track.is_confirmed():
#                 continue
#
#             tid = track.track_id
#             cls_id = track.det_class
#             ltrb = track.to_ltrb()  # 获取坐标 [left, top, right, bottom]
#
#             # 坐标换算回原始尺寸
#             x1 = int(ltrb[0] * scale_x)
#             y1 = int(ltrb[1] * scale_y)
#             x2 = int(ltrb[2] * scale_x)
#             y2 = int(ltrb[3] * scale_y)
#
#             label = VEHICLE_CLASSES.get(cls_id, "Vehicle")
#
#             # 每个ID只计数一次
#             if tid not in counted_ids:
#                 counted_ids.add(tid)
#                 total_car_count += 1
#
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
#             cv2.putText(frame, f"{label} ID:{tid}",
#                         (x1, max(y1 - 10, 10)),
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
#
#         cv2.putText(frame, f"Total: {total_car_count}",
#                     (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 4)
#         cv2.putText(frame, f"Frame: {frame_idx}",
#                     (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
#         cv2.imshow("YOLO + DeepSORT - Vehicle Counter", frame)
#
#         if frame_idx % 10 == 0:
#             print(f"Frame {frame_idx}: total unique vehicles = {total_car_count}")
#
#         if cv2.waitKey(1) & 0xFF == 27:
#             break
#
#     result_text = (
#         f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
#         f"Video: highway.mp4\n"
#         f"Total unique vehicles: {total_car_count}"
#     )
#     with open("deepsort_car_flow_result.txt", "w", encoding="utf-8") as f:
#         f.write(result_text)
#     print(f"Done! Total unique vehicles: {total_car_count}")
#     print(f"Saved to deepsort_car_flow_result.txt")
#
#     cap.release()
#     cv2.destroyAllWindows()
#
# if __name__ == "__main__":
#     main()