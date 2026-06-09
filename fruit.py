#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import cv2
import numpy as np
import random
import math
import time

WINDOW_W, WINDOW_H = 960, 720
MAX_LIVES = 3
FRUIT_TYPES = ["apple", "orange", "watermelon", "banana", "bomb"]
FRUIT_COLORS = {
    "apple":      (50,  50,  220),
    "orange":     (30,  165, 255),
    "watermelon": (50,  180, 80),
    "banana":     (30,  220, 240),
    "bomb":       (40,  40,  40),
}
FRUIT_SLICE_COLORS = {
    "apple":      (80,  80,  255),
    "orange":     (60,  190, 255),
    "watermelon": (80,  60,  220),
    "banana":     (60,  240, 255),
    "bomb":       (200, 200, 200),
}
FRUIT_RADIUS = {
    "apple": 38, "orange": 35, "watermelon": 48,
    "banana": 30, "bomb": 32
}

# ===================== 粒子系统 =====================
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 10)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(2, 5)
        self.life = 1.0
        self.decay = random.uniform(0.04, 0.09)
        self.color = color
        self.size = random.randint(3, 8)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= self.decay
        return self.life > 0

    def draw(self, frame):
        c = tuple(int(v * self.life) for v in self.color)
        cv2.circle(frame, (int(self.x), int(self.y)), self.size, c, -1)

# ===================== 水果类 =====================
class Fruit:
    def __init__(self):
        self.type = random.choices(
            FRUIT_TYPES, weights=[25, 25, 20, 20, 10]
        )[0]
        self.x = random.randint(80, WINDOW_W - 80)
        self.y = WINDOW_H + 50
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-18, -13)
        self.gravity = 0.45
        self.radius = FRUIT_RADIUS[self.type]
        self.color = FRUIT_COLORS[self.type]
        self.sliced = False
        self.slice_time = 0
        self.angle = 0
        self.angle_speed = random.uniform(-4, 4)
        self.particles = []
        self.alive = True

    def update(self):
        if not self.sliced:
            self.x += self.vx
            self.y += self.vy
            self.vy += self.gravity
            self.angle += self.angle_speed
            if self.y > WINDOW_H + 100:
                self.alive = False
        else:
            if time.time() - self.slice_time > 0.5:
                self.alive = False
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, frame):
        for p in self.particles:
            p.draw(frame)
        if not self.sliced:
            self._draw_fruit(frame)

    def _draw_fruit(self, frame):
        cx, cy = int(self.x), int(self.y)
        r = self.radius
        if self.type == "bomb":
            cv2.circle(frame, (cx, cy), r, (60, 60, 60), -1)
            cv2.circle(frame, (cx, cy), r, (150, 150, 150), 3)
            cv2.line(frame, (cx, cy - r), (cx + 10, cy - r - 15), (100, 200, 255), 3)
            cv2.circle(frame, (cx + 10, cy - r - 15), 4, (50, 50, 255), -1)
            cv2.putText(frame, "B", (cx - 8, cy + 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 220, 220), 2)
        elif self.type == "watermelon":
            cv2.circle(frame, (cx, cy), r, (40, 160, 60), -1)
            cv2.circle(frame, (cx, cy), r - 6, (60, 40, 180), -1)
        elif self.type == "apple":
            cv2.circle(frame, (cx, cy), r, self.color, -1)
            cv2.line(frame, (cx, cy - r), (cx + 5, cy - r - 12), (30, 120, 30), 3)
        elif self.type == "orange":
            cv2.circle(frame, (cx, cy), r, self.color, -1)
            for i in range(8):
                a = math.radians(i * 45 + self.angle)
                x2 = int(cx + r * math.cos(a))
                y2 = int(cy + r * math.sin(a))
                cv2.line(frame, (cx, cy), (x2, y2), (20, 130, 220), 1)
        elif self.type == "banana":
            cv2.ellipse(frame, (cx, cy), (30, 15),
                        self.angle, 0, 180, self.color, 10)

        label = {"apple":"A","orange":"O","watermelon":"W","banana":"Ba","bomb":"B"}
        cv2.putText(frame, label[self.type], (cx - 8, cy + 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def slice(self):
        if not self.sliced:
            self.sliced = True
            self.slice_time = time.time()
            for _ in range(25):
                self.particles.append(
                    Particle(self.x, self.y, FRUIT_SLICE_COLORS[self.type])
                )

# ===================== 手势检测（纯OpenCV）=====================
class HandDetector:
    def __init__(self):
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=50, varThreshold=40, detectShadows=False
        )
        self.prev_x = -1
        self.prev_y = -1

    def get_finger_pos(self, frame):
        # 肤色检测
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 30, 60], dtype=np.uint8)
        upper = np.array([20, 150, 255], dtype=np.uint8)
        mask1 = cv2.inRange(hsv, lower, upper)
        lower2 = np.array([170, 30, 60], dtype=np.uint8)
        upper2 = np.array([180, 150, 255], dtype=np.uint8)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)

        # 形态学处理
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        mask = cv2.erode(mask, kernel, iterations=1)

        # 找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return -1, -1

        # 最大轮廓（手）
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < 3000:
            return -1, -1

        # 找凸壳最高点作为指尖
        hull = cv2.convexHull(largest, returnPoints=True)
        topmost = tuple(largest[largest[:, :, 1].argmin()][0])

        h, w = frame.shape[:2]
        # 镜像+映射到游戏窗口
        fx = int((1 - topmost[0] / w) * WINDOW_W)
        fy = int(topmost[1] / h * WINDOW_H)
        return fx, fy

# ===================== 刀光轨迹 =====================
class SlashTrail:
    def __init__(self):
        self.points = []

    def add(self, x, y):
        self.points.append((x, y, time.time()))
        self.points = [(px, py, pt) for px, py, pt in self.points
                       if time.time() - pt < 0.15]

    def draw(self, frame):
        pts = [(px, py) for px, py, _ in self.points]
        if len(pts) < 2:
            return
        for i in range(1, len(pts)):
            alpha = i / len(pts)
            color = (int(255 * alpha), int(255 * alpha), 255)
            thickness = max(1, int(5 * alpha))
            cv2.line(frame, pts[i - 1], pts[i], color, thickness)

# ===================== 主游戏 =====================
class FruitNinjaGame:
    def __init__(self):
        self.fruits = []
        self.score = 0
        self.lives = MAX_LIVES
        self.game_over = False
        self.spawn_interval = 1.2
        self.last_spawn = time.time()
        self.slash = SlashTrail()
        self.flash_color = None
        self.flash_time = 0
        self.score_popups = []
        self.detector = HandDetector()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def spawn_fruit(self):
        now = time.time()
        if now - self.last_spawn > self.spawn_interval:
            for _ in range(random.randint(1, 3)):
                self.fruits.append(Fruit())
            self.last_spawn = now
            self.spawn_interval = max(0.6, self.spawn_interval - 0.01)

    def draw_background(self, frame):
        for y in range(WINDOW_H):
            ratio = y / WINDOW_H
            r = int(10 + 20 * ratio)
            g = int(5 + 15 * ratio)
            b = int(30 + 50 * ratio)
            frame[y, :] = (b, g, r)
        if self.flash_color and time.time() - self.flash_time < 0.2:
            overlay = frame.copy()
            overlay[:] = self.flash_color
            cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

    def draw_ui(self, frame):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (WINDOW_W, 70), (20, 20, 50), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.putText(frame, f"Score: {self.score}",
                    (20, 48), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 220, 50), 2)
        # 生命值
        for i in range(MAX_LIVES):
            color = (50, 50, 220) if i < self.lives else (60, 60, 80)
            cx = WINDOW_W - 50 - i * 50
            cv2.circle(frame, (cx, 35), 15, color, -1)
            cv2.putText(frame, "♥" if i < self.lives else "×",
                        (cx - 8, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                        (255, 255, 255), 2)
        # 得分弹窗
        self.score_popups = [(x, y, t, txt, c) for x, y, t, txt, c
                              in self.score_popups if time.time() - t < 1.0]
        for x, y, t, txt, color in self.score_popups:
            elapsed = time.time() - t
            dy = int(elapsed * 60)
            cv2.putText(frame, txt, (x, y - dy),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, color, 2)

    def draw_game_over(self, frame):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (WINDOW_W, WINDOW_H), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
        cv2.putText(frame, "GAME OVER",
                    (WINDOW_W // 2 - 200, WINDOW_H // 2 - 60),
                    cv2.FONT_HERSHEY_DUPLEX, 2.5, (50, 50, 255), 4)
        cv2.putText(frame, f"Final Score: {self.score}",
                    (WINDOW_W // 2 - 160, WINDOW_H // 2 + 20),
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 220, 50), 3)
        cv2.putText(frame, "Press R to restart  /  ESC to quit",
                    (WINDOW_W // 2 - 230, WINDOW_H // 2 + 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (200, 200, 200), 2)

    def check_slice(self, fx, fy):
        if fx < 0 or fy < 0:
            return
        for fruit in self.fruits:
            if fruit.sliced:
                continue
            dist = math.hypot(fx - fruit.x, fy - fruit.y)
            if dist < fruit.radius + 15:
                fruit.slice()
                if fruit.type == "bomb":
                    self.lives -= 1
                    self.flash_color = (0, 0, 180)
                    self.flash_time = time.time()
                    self.score_popups.append(
                        (fx, fy, time.time(), "-LIFE!", (50, 50, 255))
                    )
                    if self.lives <= 0:
                        self.game_over = True
                else:
                    self.score += 10
                    self.flash_color = (30, 180, 30)
                    self.flash_time = time.time()
                    self.score_popups.append(
                        (fx, fy, time.time(), "+10", (50, 255, 100))
                    )

    def reset(self):
        self.fruits = []
        self.score = 0
        self.lives = MAX_LIVES
        self.game_over = False
        self.spawn_interval = 1.2
        self.last_spawn = time.time()
        self.score_popups = []

    def run(self):
        cv2.namedWindow("Fruit Ninja", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Fruit Ninja", WINDOW_W, WINDOW_H)

        while True:
            ret, cam_frame = self.cap.read()
            if not ret:
                print("Camera error!")
                break

            fx, fy = self.detector.get_finger_pos(cam_frame)

            canvas = np.zeros((WINDOW_H, WINDOW_W, 3), dtype=np.uint8)
            self.draw_background(canvas)

            if not self.game_over:
                self.spawn_fruit()
                if fx >= 0:
                    self.slash.add(fx, fy)
                    self.check_slice(fx, fy)

                self.fruits = [f for f in self.fruits if f.alive]
                for fruit in self.fruits:
                    fruit.update()
                    fruit.draw(canvas)

                if fx >= 0:
                    cv2.circle(canvas, (fx, fy), 14, (255, 255, 255), -1)
                    cv2.circle(canvas, (fx, fy), 16, (200, 200, 255), 2)

                self.slash.draw(canvas)
                self.draw_ui(canvas)

                # 右下角摄像头小窗
                cam_small = cv2.resize(cam_frame, (200, 150))
                cam_small = cv2.flip(cam_small, 1)
                canvas[WINDOW_H - 160:WINDOW_H - 10,
                       WINDOW_W - 210:WINDOW_W - 10] = cam_small
                cv2.rectangle(canvas,
                              (WINDOW_W - 210, WINDOW_H - 160),
                              (WINDOW_W - 10, WINDOW_H - 10),
                              (200, 200, 255), 2)
            else:
                self.draw_game_over(canvas)

            cv2.imshow("Fruit Ninja", canvas)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            elif key in (ord('r'), ord('R')):
                self.reset()

        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    game = FruitNinjaGame()
    game.run()