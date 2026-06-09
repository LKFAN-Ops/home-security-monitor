import cv2
import numpy as np

# 1. 读取视频
cap = cv2.VideoCapture("highway.mp4")
if not cap.isOpened():
    print("视频读取失败，请检查路径！")
    exit()

# ===================== 车辆计数参数 =====================
car_count = 0
line_y = 300  # 检测线位置（高速视频专用）
car_ids = []  # 追踪车辆，防止重复计数
# ======================================================

# 2. 读取第一帧，作为初始背景
ret, prev_frame = cap.read()
prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
prev_gray = cv2.GaussianBlur(prev_gray, (5, 5), 0)

while cap.isOpened():
    ret, curr_frame = cap.read()
    if not ret:
        break

    # 3. 当前帧预处理
    curr_gray = cv2.cvtColor(curr_frame, cv2.COLOR_BGR2GRAY)
    curr_gray = cv2.GaussianBlur(curr_gray, (5, 5), 0)

    # 4. 帧差法
    frame_diff = cv2.absdiff(prev_gray, curr_gray)
    _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=2)
    thresh = cv2.erode(thresh, kernel, iterations=1)

    # 5. 边缘 + 轮廓
    edges = cv2.Canny(thresh, 100, 200)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 画红色检测线
    cv2.line(curr_frame, (0, line_y), (curr_frame.shape[1], line_y), (0, 0, 255), 2)

    for cnt in contours:
        # 轮廓面积调小，才能检测到车
        if cv2.contourArea(cnt) < 300:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(curr_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 计算中心点
        cx = x + w // 2
        cy = y + h // 2

        # 判断：车辆中心 越过 检测线
        if abs(cy - line_y) < 5:
            # 防止重复计数
            if len(car_ids) == 0 or cx > car_ids[-1] + 30 or cx < car_ids[-1] - 30:
                car_count += 1
                car_ids.append(cx)
    # ==============================================================

    # 显示数量
    cv2.putText(curr_frame, f"Count: {car_count}", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)

    cv2.imshow("Car Count", curr_frame)
    prev_gray = curr_gray.copy()

    if cv2.waitKey(25) & 0xFF == 27:
        break

print(f"最终统计车辆总数：{car_count}")
cap.release()
cv2.destroyAllWindows()