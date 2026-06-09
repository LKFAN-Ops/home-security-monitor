# -*- coding: utf-8 -*-
"""
家庭安全监控提醒工具 —— GUI 版本
界面框架：Tkinter（Python 内置，无需额外安装）
打包方式：PyInstaller（见 build.bat）
"""

import os
import sys
import traceback

# ── 启动诊断日志（调试期间使用，出错后查看 startup_log.txt）──
_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "startup_log.txt")
def _slog(msg: str):
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as _f:
            _f.write(msg + "\n")
    except Exception:
        pass

_slog("=" * 40)
_slog(f"EXE 路径: {sys.argv[0]}")
_slog(f"_MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")

# Windows DPI 感知：必须在任何 UI 创建之前调用，否则高分屏下控件不渲染
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        _slog("DPI: SetProcessDpiAwareness(1) OK")
    except Exception as _e:
        _slog(f"DPI: shcore 失败 ({_e})，尝试 user32")
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            _slog("DPI: user32 OK")
        except Exception as _e2:
            _slog(f"DPI: user32 也失败 ({_e2})")

_slog("import cv2 ...")
import cv2
_slog("cv2 OK")
import time
import base64
import re
import threading
_slog("import tkinter ...")
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
_slog("tkinter OK")
_slog("import PIL ...")
from PIL import Image, ImageTk          # pip install pillow
_slog("PIL OK")
_slog("import requests ...")
import requests
_slog("import ultralytics ...")
from ultralytics import YOLO
_slog("ultralytics OK")
_slog("import openai ...")
from openai import OpenAI
_slog("所有 import 完成，准备创建 App")


def _write_crash_log(exc: BaseException):
    """打包后 console=False 时把崩溃信息写到 exe 旁边的文件里"""
    try:
        log_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_path = os.path.join(log_dir, "crash_log.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("===== 家庭安全监控 崩溃日志 =====\n\n")
            traceback.print_exc(file=f)
        return log_path
    except Exception:
        return None

# ──────────────────────────────────────────────
# 工具函数
# ──────────────────────────────────────────────

def resource_path(rel_path):
    """兼容 PyInstaller 打包后的资源路径"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)


def download_model(path: str, log_fn=print):
    need = False
    if not os.path.exists(path):
        need = True
    else:
        if os.path.getsize(path) / 1024 / 1024 < 5:
            log_fn(f"[警告] 模型文件损坏，正在删除重下…")
            os.remove(path)
            need = True
    if need:
        url = "https://github.com/lindevs/yolov8-face/releases/download/v1.0.0/yolov8n-face-lindevs.pt"
        log_fn("[下载] 正在下载人脸检测模型，请稍候…")
        try:
            r = requests.get(url, stream=True, timeout=90)
            r.raise_for_status()
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            log_fn(f"[下载] 完成！大小：{os.path.getsize(path)/1024/1024:.1f} MB")
        except Exception as e:
            log_fn(f"[错误] 下载失败：{e}")
            raise


def frame_to_b64(frame) -> str:
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
    return base64.b64encode(buf).decode()


def describe_scene(frame, api_key: str) -> str:
    b64 = frame_to_b64(frame)
    prompt = ("这是家庭安全监控画面。请简洁描述：有几人、位置、在做什么、"
               "是否有可疑行为。50字以内。")
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        res = client.chat.completions.create(
            model="qwen-vl-max",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": prompt}
            ]}]
        )
        txt = res.choices[0].message.content
        return re.sub(r"^```.*?\n|\n```$", "", str(txt).strip(), flags=re.DOTALL)
    except Exception as e:
        return f"[大模型失败: {e}]"


# ──────────────────────────────────────────────
# 主界面
# ──────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("家庭安全监控提醒工具  v1.0")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")

        # 运行状态
        self._running    = False
        self._thread     = None
        self._cap        = None
        self._model      = None
        self._stop_event = threading.Event()

        try:
            self._build_ui()
        except Exception as e:
            log_path = _write_crash_log(e)
            msg = f"界面初始化失败：{e}"
            if log_path:
                msg += f"\n\n详细日志已写入：\n{log_path}"
            messagebox.showerror("启动错误", msg)
            self.destroy()
            return

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI 构建 ──────────────────────────────

    def _build_ui(self):
        PAD = 10
        BG  = "#1a1a2e"
        FG  = "#e0e0e0"
        ACC = "#0f3460"
        BTN = "#e94560"
        ENT = "#16213e"

        # ── 左侧控制面板 ──
        left = tk.Frame(self, bg=BG, padx=PAD, pady=PAD)
        left.grid(row=0, column=0, sticky="ns")

        tk.Label(left, text="家庭安全监控", bg=BG, fg="#e94560",
                 font=("微软雅黑", 14, "bold")).pack(pady=(0, 10))

        # 视频源
        src_frame = tk.LabelFrame(left, text=" 视频源 ", bg=BG, fg=FG,
                                  font=("微软雅黑", 9))
        src_frame.pack(fill="x", pady=4)

        self.var_src = tk.StringVar(value="camera")
        tk.Radiobutton(src_frame, text="摄像头", variable=self.var_src,
                       value="camera", bg=BG, fg=FG,
                       selectcolor=ACC, activebackground=BG,
                       command=self._toggle_src).pack(side="left", padx=6)
        tk.Radiobutton(src_frame, text="视频文件", variable=self.var_src,
                       value="file", bg=BG, fg=FG,
                       selectcolor=ACC, activebackground=BG,
                       command=self._toggle_src).pack(side="left", padx=6)

        self.ent_file = tk.Entry(left, bg=ENT, fg=FG, insertbackground=FG,
                                 font=("微软雅黑", 9), state="disabled", width=28)
        self.ent_file.pack(fill="x", pady=2)
        self.btn_browse = tk.Button(left, text="浏览…", bg=ACC, fg=FG,
                                    font=("微软雅黑", 9), relief="flat",
                                    state="disabled", command=self._browse)
        self.btn_browse.pack(fill="x", pady=2)

        # 参数设置
        cfg_frame = tk.LabelFrame(left, text=" 参数设置 ", bg=BG, fg=FG,
                                  font=("微软雅黑", 9))
        cfg_frame.pack(fill="x", pady=6)

        def labeled_entry(parent, label, default, row):
            tk.Label(parent, text=label, bg=BG, fg=FG,
                     font=("微软雅黑", 9)).grid(row=row, column=0, sticky="w", padx=4, pady=2)
            var = tk.StringVar(value=default)
            tk.Entry(parent, textvariable=var, bg=ENT, fg=FG,
                     insertbackground=FG, font=("微软雅黑", 9), width=10
                     ).grid(row=row, column=1, sticky="ew", padx=4, pady=2)
            return var

        self.var_conf    = labeled_entry(cfg_frame, "置信度阈值", "0.45", 0)
        self.var_cool    = labeled_entry(cfg_frame, "报警冷却(秒)", "3.0",  1)
        self.var_ai_inv  = labeled_entry(cfg_frame, "AI描述间隔(帧)", "30", 2)

        # API Key
        tk.Label(left, text="通义千问 API Key", bg=BG, fg=FG,
                 font=("微软雅黑", 9)).pack(anchor="w")
        self.ent_api = tk.Entry(left, bg=ENT, fg=FG, insertbackground=FG,
                                font=("微软雅黑", 9), show="*", width=28)
        self.ent_api.pack(fill="x", pady=2)
        tk.Label(left, text="（不填则跳过AI描述）", bg=BG, fg="#888",
                 font=("微软雅黑", 8)).pack(anchor="w")

        # 模型路径
        tk.Label(left, text="模型文件路径", bg=BG, fg=FG,
                 font=("微软雅黑", 9)).pack(anchor="w", pady=(6, 0))
        model_row = tk.Frame(left, bg=BG)
        model_row.pack(fill="x", pady=2)
        self.ent_model = tk.Entry(model_row, bg=ENT, fg=FG, insertbackground=FG,
                                  font=("微软雅黑", 9))
        self.ent_model.insert(0, resource_path("yolov8n-face-lindevs.pt"))
        self.ent_model.pack(side="left", fill="x", expand=True)
        tk.Button(model_row, text="…", bg=ACC, fg=FG, font=("微软雅黑", 9),
                  relief="flat", width=3,
                  command=self._browse_model).pack(side="left", padx=2)

        # 启动 / 停止
        self.btn_start = tk.Button(left, text="▶  开始监控", bg=BTN, fg="white",
                                   font=("微软雅黑", 11, "bold"), relief="flat",
                                   height=2, command=self._start)
        self.btn_start.pack(fill="x", pady=(12, 2))
        self.btn_stop = tk.Button(left, text="■  停止", bg="#555", fg="white",
                                  font=("微软雅黑", 11), relief="flat",
                                  height=2, state="disabled", command=self._stop)
        self.btn_stop.pack(fill="x", pady=2)

        # 状态灯
        self.lbl_status = tk.Label(left, text="● 待机", bg=BG, fg="#888",
                                   font=("微软雅黑", 10))
        self.lbl_status.pack(pady=4)

        # ── 右侧预览 + 日志 ──
        right = tk.Frame(self, bg=BG)
        right.grid(row=0, column=1, padx=PAD, pady=PAD, sticky="nsew")

        # 视频预览画布
        self.canvas = tk.Canvas(right, width=640, height=480, bg="#000",
                                highlightthickness=1, highlightbackground=ACC)
        self.canvas.pack()

        # 统计行
        stats = tk.Frame(right, bg=ACC)
        stats.pack(fill="x", pady=2)
        self.lbl_people  = tk.Label(stats, text="当前人数：0", bg=ACC, fg="white",
                                    font=("微软雅黑", 10, "bold"))
        self.lbl_people.pack(side="left", padx=12)
        self.lbl_frames  = tk.Label(stats, text="帧数：0", bg=ACC, fg="white",
                                    font=("微软雅黑", 10))
        self.lbl_frames.pack(side="left", padx=12)
        self.lbl_alerts  = tk.Label(stats, text="报警次数：0", bg=ACC, fg="#ff6b6b",
                                    font=("微软雅黑", 10, "bold"))
        self.lbl_alerts.pack(side="right", padx=12)

        # 日志区
        tk.Label(right, text="运行日志", bg=BG, fg=FG,
                 font=("微软雅黑", 9)).pack(anchor="w")
        self.log_box = scrolledtext.ScrolledText(
            right, height=8, bg="#0d0d1a", fg="#00ff88",
            insertbackground="white", font=("Consolas", 9),
            state="disabled", relief="flat"
        )
        self.log_box.pack(fill="x")

    def _toggle_src(self):
        if self.var_src.get() == "file":
            self.ent_file.config(state="normal")
            self.btn_browse.config(state="normal")
        else:
            self.ent_file.config(state="disabled")
            self.btn_browse.config(state="disabled")

    def _browse(self):
        path = filedialog.askopenfilename(
            filetypes=[("视频文件", "*.mp4 *.avi *.mov *.mkv"), ("所有文件", "*.*")])
        if path:
            self.ent_file.delete(0, "end")
            self.ent_file.insert(0, path)

    def _browse_model(self):
        path = filedialog.askopenfilename(
            filetypes=[("PT 权重", "*.pt"), ("所有文件", "*.*")])
        if path:
            self.ent_model.delete(0, "end")
            self.ent_model.insert(0, path)

    # ── 日志输出 ──────────────────────────────

    def _log(self, msg: str):
        self.log_box.config(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    # ── 启动 / 停止 ──────────────────────────

    def _start(self):
        # 读取参数
        model_path = self.ent_model.get().strip()
        api_key    = self.ent_api.get().strip()
        try:
            conf    = float(self.var_conf.get())
            cool    = float(self.var_cool.get())
            ai_inv  = int(self.var_ai_inv.get())
        except ValueError:
            messagebox.showerror("参数错误", "置信度/冷却时间/AI间隔 必须为数字！")
            return

        if self.var_src.get() == "camera":
            source = 0
        else:
            source = self.ent_file.get().strip()
            if not source:
                messagebox.showerror("错误", "请选择视频文件！")
                return

        self._stop_event.clear()
        self._running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="● 运行中", fg="#00ff88")

        self._thread = threading.Thread(
            target=self._monitor_loop,
            args=(source, model_path, api_key, conf, cool, ai_inv),
            daemon=True
        )
        self._thread.start()

    def _stop(self):
        self._stop_event.set()
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text="● 正在停止…", fg="#ffa500")

    def _on_stop_done(self):
        self._running = False
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text="● 待机", fg="#888")
        self.canvas.delete("all")

    def _on_close(self):
        self._stop_event.set()
        self.destroy()

    # ── 检测主循环（子线程）─────────────────

    def _monitor_loop(self, source, model_path, api_key, conf_thresh, cooldown, ai_interval):
        try:
            download_model(model_path, self._log)
        except Exception:
            self.after(0, self._on_stop_done)
            return

        self._log("[初始化] 加载人脸检测模型…")
        try:
            model = YOLO(model_path)
        except Exception as e:
            self._log(f"[错误] 模型加载失败：{e}")
            self.after(0, self._on_stop_done)
            return
        self._log("[初始化] 模型加载完成！")

        # CAP_DSHOW 在 Windows 上比默认 MSMF 后端更稳定，避免黑帧
        backend = cv2.CAP_DSHOW if isinstance(source, int) else cv2.CAP_ANY
        cap = cv2.VideoCapture(source, backend)
        if not cap.isOpened():
            self._log(f"[错误] 无法打开视频源：{source}")
            self.after(0, self._on_stop_done)
            return

        # 预热：丢弃前几帧，等摄像头曝光稳定；同时获取真实分辨率
        self._log("[初始化] 摄像头预热中…")
        first_frame = None
        for _ in range(10):
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                first_frame = frame
                break
        if first_frame is None:
            self._log("[错误] 无法从视频源读取画面，请检查摄像头是否被占用")
            cap.release()
            self.after(0, self._on_stop_done)
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        h, w = first_frame.shape[:2]   # 从实际帧获取尺寸，避免 cap.get 返回 0
        self._log(f"[初始化] 视频源已打开，分辨率 {w}x{h}，帧率 {fps:.1f}")

        # 输出文件
        ts_str   = time.strftime("%Y%m%d_%H%M%S")
        out_dir  = os.path.dirname(os.path.abspath(sys.argv[0]))
        vid_path = os.path.join(out_dir, f"监控录像_{ts_str}.mp4")
        txt_path = os.path.join(out_dir, f"事件报告_{ts_str}.txt")
        fourcc   = cv2.VideoWriter_fourcc(*"mp4v")
        writer   = cv2.VideoWriter(vid_path, fourcc, fps, (w, h))
        if not writer.isOpened():
            # mp4v 失败时回退到 XVID+avi
            vid_path = vid_path.replace(".mp4", ".avi")
            fourcc   = cv2.VideoWriter_fourcc(*"XVID")
            writer   = cv2.VideoWriter(vid_path, fourcc, fps, (w, h))
        self._log(f"[录像] 保存至：{vid_path}")

        frame_idx        = 0
        last_alert_time  = 0
        alert_count      = 0
        event_log        = []
        # 目标处理帧率：最多 15 fps，避免推理占满 CPU
        TARGET_FPS       = min(fps, 15.0)
        frame_interval   = 1.0 / TARGET_FPS
        # UI 刷新节流：每隔此秒数才推送一次预览，避免 Tkinter 队列积压
        UI_INTERVAL      = 0.05   # ~20 fps 预览即可
        last_ui_time     = 0.0

        # 将预热时读到的第一帧放入队列，不丢弃
        pending_frame = first_frame

        while not self._stop_event.is_set():
            t_loop_start = time.time()

            if pending_frame is not None:
                frame, pending_frame = pending_frame, None
                ret = True
            else:
                ret, frame = cap.read()
            if not ret:
                self._log("[提示] 视频读取结束。")
                break

            # YOLOv8 检测
            results  = model(frame, conf=conf_thresh, verbose=False)
            face_cnt = 0

            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    c = box.conf[0].item()
                    face_cnt += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"face {c:.2f}", (x1, max(y1-10, 10)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

            # 人数叠加
            cv2.putText(frame, f"People: {face_cnt}", (12, 38),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 2)

            # 报警
            now = time.time()
            if face_cnt > 0:
                if now - last_alert_time >= cooldown:
                    last_alert_time = now
                    alert_count += 1
                    ts  = time.strftime("%Y-%m-%d %H:%M:%S")
                    msg = f"[{ts}] [警报] 检测到 {face_cnt} 人进入画面！"
                    self._log(msg)
                    event_log.append(msg)
                    ac = alert_count
                    self.after(0, lambda v=ac: self.lbl_alerts.config(
                        text=f"报警次数：{v}"))

                cv2.rectangle(frame, (0, h-55), (w, h), (0, 0, 180), -1)
                cv2.putText(frame, "ALERT: Person Detected!", (10, h-16),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)

            # AI 描述
            if (frame_idx % ai_interval == 0
                    and api_key):
                t = round(frame_idx / fps, 1)
                desc = describe_scene(frame, api_key)
                log_msg = f"[{t}s] 人脸={face_cnt} | {desc}"
                self._log(log_msg)
                event_log.append(log_msg)

            # 写录像
            writer.write(frame)

            # UI 预览节流：距上次刷新超过 UI_INTERVAL 才推送
            if now - last_ui_time >= UI_INTERVAL:
                last_ui_time = now
                preview = cv2.resize(frame, (640, 480))
                preview_rgb = cv2.cvtColor(preview, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(Image.fromarray(preview_rgb))
                fc  = face_cnt
                fi  = frame_idx
                self.after(10, lambda i=img, f=fc, n=fi: self._update_canvas(i, f, n))

            frame_idx += 1

            # 帧率限速：推理耗时不足 frame_interval 时主动 sleep，释放 CPU
            elapsed = time.time() - t_loop_start
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

        # 收尾
        cap.release()
        writer.release()

        if event_log:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write("===== 家庭安全监控事件报告 =====\n\n")
                for line in event_log:
                    f.write(line + "\n")
            self._log(f"[完成] 报告已保存：{txt_path}")

        self._log(f"[统计] 共处理 {frame_idx} 帧，触发报警 {alert_count} 次。")
        self.after(0, self._on_stop_done)

    def _update_canvas(self, img, face_cnt, frame_idx):
        self._photo = img                   # 防止 GC 回收
        self.canvas.create_image(0, 0, anchor="nw", image=img)
        self.lbl_people.config(text=f"当前人数：{face_cnt}")
        self.lbl_frames.config(text=f"帧数：{frame_idx}")


# ──────────────────────────────────────────────
if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        log_path = _write_crash_log(e)
        try:
            import tkinter.messagebox as mb
            mb.showerror("启动错误", f"程序崩溃：{e}\n\n日志：{log_path}")
        except Exception:
            pass