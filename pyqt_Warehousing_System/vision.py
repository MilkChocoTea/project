"""
vision.py — 影像校正模組
功能：
  1. 幾何校正 (鏡頭畸變矯正、透視校正)
  2. 色彩/亮度校正 (白平衡、直方圖均衡化)
  3. 物件辨識定位 (顏色遮罩 + 輪廓偵測，輸出像素座標)
  4. 像素→手臂角度轉換 (供閉迴路使用)

相依套件：
  pip install opencv-python-headless numpy --break-system-packages
  (Raspberry Pi 上建議用 apt: sudo apt install python3-opencv python3-numpy)

校正參數儲存：
  存入 armconfig 資料庫的 vision_calib 表，與 MotorRange 等參數放在一起。
  資料表由 setsql.check_table() 自動建立 (已加入 initial_tables 清單)。
"""

import cv2
import numpy as np
import json
import os
import time
import setsql

# 預設 HSV 顏色範圍 (可透過 UI 調整後存檔)
DEFAULT_COLOR_PROFILES = {
    "red":    {"lower": [0,   120,  70], "upper": [10,  255, 255]},
    "green":  {"lower": [36,  100,  70], "upper": [86,  255, 255]},
    "blue":   {"lower": [94,  80,   2],  "upper": [126, 255, 255]},
    "yellow": {"lower": [20,  100,  100],"upper": [30,  255, 255]},
}


# ══════════════════════════════════════════════
# CalibrationData — 校正參數的資料容器
# ══════════════════════════════════════════════
class CalibrationData:
    """存放所有校正參數，可序列化為 JSON"""

    def __init__(self):
        # 幾何：鏡頭內參 & 畸變係數
        self.camera_matrix: np.ndarray | None = None
        self.dist_coeffs:   np.ndarray | None = None

        # 幾何：透視變換矩陣
        self.perspective_matrix: np.ndarray | None = None
        # 透視校正後的實際尺寸 (px)
        self.perspective_size: tuple = (640, 640)

        # 色彩：白平衡增益 (R, G, B 乘數)
        self.wb_gains: list = [1.0, 1.0, 1.0]
        # 色彩：是否啟用 CLAHE 自適應直方圖均衡
        self.use_clahe: bool = True

        # 座標映射：像素→手臂角度的線性係數
        # angle_x = px_to_angle_x[0] * pixel_x + px_to_angle_x[1]
        self.px_to_angle: list = [[0.0, 0.0], [0.0, 0.0]]  # [x係數, y係數]

        # 顏色辨識設定
        self.color_profiles: dict = DEFAULT_COLOR_PROFILES.copy()

    # ── 序列化 ──
    def to_dict(self) -> dict:
        def arr(x):
            return x.tolist() if isinstance(x, np.ndarray) else x
        return {
            "camera_matrix":      arr(self.camera_matrix),
            "dist_coeffs":        arr(self.dist_coeffs),
            "perspective_matrix": arr(self.perspective_matrix),
            "perspective_size":   list(self.perspective_size),
            "wb_gains":           self.wb_gains,
            "use_clahe":          self.use_clahe,
            "px_to_angle":        self.px_to_angle,
            "color_profiles":     self.color_profiles,
        }

    def from_dict(self, d: dict):
        def mat(x):
            return np.array(x) if x is not None else None
        self.camera_matrix      = mat(d.get("camera_matrix"))
        self.dist_coeffs        = mat(d.get("dist_coeffs"))
        self.perspective_matrix = mat(d.get("perspective_matrix"))
        self.perspective_size   = tuple(d.get("perspective_size", (640, 640)))
        self.wb_gains           = d.get("wb_gains",    [1.0, 1.0, 1.0])
        self.use_clahe          = d.get("use_clahe",   True)
        self.px_to_angle        = d.get("px_to_angle", [[0.0, 0.0], [0.0, 0.0]])
        self.color_profiles     = d.get("color_profiles", DEFAULT_COLOR_PROFILES.copy())

    def save(self):
        """將所有校正參數序列化為 JSON 字串，儲存至 armconfig.vision_calib 表"""
        payload = json.dumps(self.to_dict())
        try:
            with setsql.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # UPSERT：若 id=1 已存在則覆蓋，否則新增
                    cur.execute("""
                        INSERT INTO vision_calib (id, calib_json, updated_at)
                        VALUES (1, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE
                            SET calib_json = EXCLUDED.calib_json,
                                updated_at  = EXCLUDED.updated_at;
                    """, (payload,))
            print("[Vision] 校正參數已儲存至資料庫 vision_calib")
        except Exception as e:
            print(f"[Vision] 儲存失敗：{e}")

    def load(self) -> bool:
        """從 armconfig.vision_calib 表讀取校正參數"""
        try:
            with setsql.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT calib_json FROM vision_calib WHERE id = 1;")
                    row = cur.fetchone()
            if row is None:
                print("[Vision] 資料庫中尚無校正參數，使用預設值")
                return False
            self.from_dict(json.loads(row[0]))
            print("[Vision] 已從資料庫讀取校正參數")
            return True
        except Exception as e:
            print(f"[Vision] 讀取失敗：{e}")
            return False


# ══════════════════════════════════════════════
# VisionSystem — 主要影像處理引擎
# ══════════════════════════════════════════════
class VisionSystem:
    """
    使用方式：
        vs = VisionSystem()
        vs.open_camera()
        frame = vs.capture()
        corrected = vs.apply_corrections(frame)
        objects = vs.detect_objects(corrected, color="red")
        delta = vs.compute_angle_delta(objects[0]["center"])
    """

    def __init__(self):
        self.calib = CalibrationData()
        self.calib.load()          # 嘗試讀取既有校正檔
        self.cap: cv2.VideoCapture | None = None
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    # ──────────────────────────────────────────
    # 攝影機管理
    # ──────────────────────────────────────────
    def open_camera(self, index: int = 0, width: int = 640, height: int = 480) -> bool:
        """
        開啟攝影機，依序嘗試四種方式：
          1. libcamera GStreamer pipeline (Pi Camera Module 新版 OS 首選)
          2. V4L2 直接存取 /dev/videoN
          3. OpenCV 預設後端
          4. 掃描其他 /dev/video* 裝置
        """
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

        # ── 方式 1：libcamera GStreamer pipeline ──────────────────────────
        # 需要：sudo apt install gstreamer1.0-libcamera -y
        gst_pipeline = (
            f"libcamerasrc ! "
            f"video/x-raw,width={width},height={height},framerate=30/1 ! "
            f"videoconvert ! video/x-raw,format=BGR ! appsink drop=1 max-buffers=1 sync=false"
        )
        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                self.cap = cap
                self._camera_mode = "libcamera-gst"
                print(f"[Vision] Pi Camera 已開啟 (libcamera GStreamer, {width}x{height})")
                return True
            cap.release()

        # ── 方式 2：V4L2 直接存取 ────────────────────────────────────────
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            ret, frame = cap.read()
            if ret and frame is not None:
                self.cap = cap
                self._camera_mode = "v4l2"
                print(f"[Vision] 攝影機已開啟 (V4L2 /dev/video{index}, {width}x{height})")
                return True
            cap.release()

        # ── 方式 3：OpenCV 預設後端 ───────────────────────────────────────
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            ret, frame = cap.read()
            if ret and frame is not None:
                self.cap = cap
                self._camera_mode = "default"
                print(f"[Vision] 攝影機已開啟 (預設後端 index={index}, {width}x{height})")
                return True
            cap.release()

        # ── 方式 4：掃描其他 video 裝置 ──────────────────────────────────
        import glob
        for dev in sorted(glob.glob("/dev/video*")):
            try:
                dev_index = int(dev.replace("/dev/video", ""))
            except ValueError:
                continue
            if dev_index == index:
                continue
            cap = cv2.VideoCapture(dev_index, cv2.CAP_V4L2)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                ret, frame = cap.read()
                if ret and frame is not None:
                    self.cap = cap
                    self._camera_mode = f"v4l2-{dev}"
                    print(f"[Vision] 攝影機已開啟 ({dev}, {width}x{height})")
                    return True
                cap.release()

        print("[Vision] 找不到可用的攝影機，請確認：")
        print("  1. sudo raspi-config → Interface Options → Camera → Enable")
        print("  2. 重開機後執行 ls /dev/video* 確認裝置存在")
        print("  3. 執行 libcamera-hello 確認 Pi Camera 硬體正常")
        print("  4. sudo apt install gstreamer1.0-libcamera -y")
        return False

    def close_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self._camera_mode = None

    def capture(self) -> np.ndarray | None:
        """擷取單張影像，失敗回傳 None"""
        if not self.cap or not self.cap.isOpened():
            return None
        # libcamera GStreamer pipeline 不需要 grab() 清緩衝
        if getattr(self, "_camera_mode", "") != "libcamera-gst":
            self.cap.grab()
        ret, frame = self.cap.read()
        return frame if ret and frame is not None else None


    # ──────────────────────────────────────────
    # 1. 幾何校正
    # ──────────────────────────────────────────
    def undistort(self, frame: np.ndarray) -> np.ndarray:
        """鏡頭畸變矯正 (需先完成 calibrate_lens())"""
        if self.calib.camera_matrix is None or self.calib.dist_coeffs is None:
            return frame
        h, w = frame.shape[:2]
        new_cam, roi = cv2.getOptimalNewCameraMatrix(
            self.calib.camera_matrix, self.calib.dist_coeffs, (w, h), 1, (w, h)
        )
        dst = cv2.undistort(frame, self.calib.camera_matrix, self.calib.dist_coeffs, None, new_cam)
        x, y, rw, rh = roi
        return dst[y:y+rh, x:x+rw] if all([rw, rh]) else dst

    def apply_perspective(self, frame: np.ndarray) -> np.ndarray:
        """透視校正 (需先完成 set_perspective_points())"""
        if self.calib.perspective_matrix is None:
            return frame
        w, h = self.calib.perspective_size
        return cv2.warpPerspective(frame, self.calib.perspective_matrix, (w, h))

    def set_perspective_points(self, src_pts: list[list[float]]):
        """
        設定四個角點進行透視校正。
        src_pts: 影像中的四個角點 [[x0,y0],[x1,y1],[x2,y2],[x3,y3]]
                 順序：左上、右上、右下、左下
        """
        w, h = self.calib.perspective_size
        dst_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
        src = np.float32(src_pts)
        self.calib.perspective_matrix = cv2.getPerspectiveTransform(src, dst_pts)
        print("[Vision] 透視矩陣已更新")

    def calibrate_lens(self, images: list[np.ndarray],
                       board_size: tuple = (9, 6),
                       square_mm: float = 25.0) -> bool:
        """
        棋盤格鏡頭校正。
        images: 多張含棋盤格的影像 (至少 10 張)
        board_size: 棋盤格內角點數 (cols, rows)
        square_mm: 每格邊長 (mm)
        回傳是否成功
        """
        obj_pts_single = np.zeros((board_size[0] * board_size[1], 3), np.float32)
        obj_pts_single[:, :2] = np.mgrid[0:board_size[0], 0:board_size[1]].T.reshape(-1, 2) * square_mm

        obj_pts_all, img_pts_all = [], []
        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ret, corners = cv2.findChessboardCorners(gray, board_size, None)
            if ret:
                obj_pts_all.append(obj_pts_single)
                refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1),
                                           (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
                img_pts_all.append(refined)

        if len(obj_pts_all) < 3:
            print(f"[Vision] 校正失敗：只找到 {len(obj_pts_all)} 張有效棋盤格影像")
            return False

        h, w = images[0].shape[:2]
        ret, mtx, dist, _, _ = cv2.calibrateCamera(obj_pts_all, img_pts_all, (w, h), None, None)
        if ret:
            self.calib.camera_matrix = mtx
            self.calib.dist_coeffs   = dist
            print(f"[Vision] 鏡頭校正完成，RMS 誤差={ret:.4f}")
            return True
        return False

    # ──────────────────────────────────────────
    # 2. 色彩/亮度校正
    # ──────────────────────────────────────────
    def apply_white_balance(self, frame: np.ndarray) -> np.ndarray:
        """套用白平衡增益"""
        r, g, b = self.calib.wb_gains
        lut_r = np.clip(np.arange(256) * r, 0, 255).astype(np.uint8)
        lut_g = np.clip(np.arange(256) * g, 0, 255).astype(np.uint8)
        lut_b = np.clip(np.arange(256) * b, 0, 255).astype(np.uint8)
        result = frame.copy()
        result[:, :, 2] = cv2.LUT(frame[:, :, 2], lut_r)
        result[:, :, 1] = cv2.LUT(frame[:, :, 1], lut_g)
        result[:, :, 0] = cv2.LUT(frame[:, :, 0], lut_b)
        return result

    def compute_auto_wb(self, frame: np.ndarray) -> list:
        """
        灰世界假設自動白平衡：
        計算各通道增益使三通道均值相等。
        """
        b, g, r = cv2.split(frame.astype(np.float32))
        mean_b, mean_g, mean_r = b.mean(), g.mean(), r.mean()
        mean_all = (mean_b + mean_g + mean_r) / 3.0
        gains = [mean_all / c if c > 0 else 1.0 for c in [mean_r, mean_g, mean_b]]
        self.calib.wb_gains = gains
        print(f"[Vision] 自動白平衡增益 R={gains[0]:.3f} G={gains[1]:.3f} B={gains[2]:.3f}")
        return gains

    def apply_clahe(self, frame: np.ndarray) -> np.ndarray:
        """CLAHE 自適應直方圖均衡 (在 L 通道上操作，保留色彩)"""
        if not self.calib.use_clahe:
            return frame
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2Lab)
        lab[:, :, 0] = self._clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_Lab2BGR)

    # ──────────────────────────────────────────
    # 整合：一鍵套用所有校正
    # ──────────────────────────────────────────
    def apply_corrections(self, frame: np.ndarray) -> np.ndarray:
        """依序套用所有啟用的校正流程"""
        out = self.undistort(frame)
        out = self.apply_perspective(out)
        out = self.apply_white_balance(out)
        out = self.apply_clahe(out)
        return out

    # ──────────────────────────────────────────
    # 3. 物件辨識定位
    # ──────────────────────────────────────────
    def detect_objects(self,
                       frame: np.ndarray,
                       color: str = "red",
                       min_area: int = 500) -> list[dict]:
        """
        用 HSV 顏色遮罩偵測物件，回傳偵測結果列表。
        每個結果：{
            "center":   (cx, cy),     # 像素座標 (影像中心為原點)
            "area":     float,        # 輪廓面積
            "bbox":     (x,y,w,h),    # 邊界框
            "contour":  np.ndarray    # 輪廓點
        }
        """
        profile = self.calib.color_profiles.get(color)
        if profile is None:
            print(f"[Vision] 未知顏色 '{color}'，可用：{list(self.calib.color_profiles.keys())}")
            return []

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array(profile["lower"], np.uint8)
        upper = np.array(profile["upper"], np.uint8)

        # 紅色跨越 HSV 0°，需合併兩個範圍
        if color == "red":
            lower2 = np.array([170, profile["lower"][1], profile["lower"][2]], np.uint8)
            upper2 = np.array([180, profile["upper"][1], profile["upper"][2]], np.uint8)
            mask = cv2.add(cv2.inRange(hsv, lower, upper),
                           cv2.inRange(hsv, lower2, upper2))
        else:
            mask = cv2.inRange(hsv, lower, upper)

        # 形態學去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        h, w = frame.shape[:2]
        cx_origin, cy_origin = w // 2, h // 2   # 以影像中心為原點

        results = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"]) - cx_origin
            cy = cy_origin - int(M["m01"] / M["m00"])  # y 軸朝上為正
            x, y, bw, bh = cv2.boundingRect(cnt)
            results.append({
                "center":  (cx, cy),
                "area":    area,
                "bbox":    (x, y, bw, bh),
                "contour": cnt,
            })

        # 面積由大到小排序
        results.sort(key=lambda d: d["area"], reverse=True)
        return results

    def draw_detections(self, frame: np.ndarray, detections: list[dict],
                        color_bgr: tuple = (0, 255, 0)) -> np.ndarray:
        """在影像上繪製偵測結果 (供預覽用)"""
        h, w = frame.shape[:2]
        out = frame.copy()
        # 繪製影像中心十字
        cv2.line(out, (w//2 - 20, h//2), (w//2 + 20, h//2), (255, 255, 0), 1)
        cv2.line(out, (w//2, h//2 - 20), (w//2, h//2 + 20), (255, 255, 0), 1)

        for d in detections:
            x, y, bw, bh = d["bbox"]
            # 轉回影像座標系繪製
            cx_img = d["center"][0] + w // 2
            cy_img = h // 2 - d["center"][1]
            cv2.rectangle(out, (x, y), (x+bw, y+bh), color_bgr, 2)
            cv2.circle(out, (cx_img, cy_img), 5, (0, 0, 255), -1)
            cv2.putText(out, f"({d['center'][0]},{d['center'][1]})",
                        (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_bgr, 1)
        return out

    # ──────────────────────────────────────────
    # 4. 像素 → 手臂角度轉換
    # ──────────────────────────────────────────
    def set_pixel_to_angle_mapping(self,
                                   pixel_ref: tuple,
                                   angle_ref: tuple,
                                   pixel_per_deg_x: float,
                                   pixel_per_deg_y: float):
        """
        設定線性映射係數。
        pixel_ref:      (px, py) 基準點像素座標 (影像中心)
        angle_ref:      (ax, ay) 對應的手臂角度基準值
        pixel_per_deg_x: 水平每度對應多少像素
        pixel_per_deg_y: 垂直每度對應多少像素
        """
        # angle = angle_ref + (pixel - pixel_ref) / pixel_per_deg
        # 整理成 angle = (1/ppd)*pixel + (angle_ref - pixel_ref/ppd)
        self.calib.px_to_angle = [
            [1.0 / pixel_per_deg_x, angle_ref[0] - pixel_ref[0] / pixel_per_deg_x],
            [1.0 / pixel_per_deg_y, angle_ref[1] - pixel_ref[1] / pixel_per_deg_y],
        ]
        print(f"[Vision] 像素→角度映射已設定")

    def pixel_to_angle(self, pixel_center: tuple) -> tuple[float, float]:
        """
        把偵測到的物件像素座標轉換為手臂目標角度偏移量 (Δangle_x, Δangle_y)
        pixel_center: (px, py) 以影像中心為原點
        """
        coeff_x, coeff_y = self.calib.px_to_angle
        angle_x = coeff_x[0] * pixel_center[0] + coeff_x[1]
        angle_y = coeff_y[0] * pixel_center[1] + coeff_y[1]
        return angle_x, angle_y

    def compute_angle_delta(self, pixel_center: tuple) -> tuple[float, float]:
        """
        計算影像中心到物件的角度誤差 (Δx, Δy)，供閉迴路修正用。
        正值表示物件在影像中心的右/上方。
        """
        coeff_x, coeff_y = self.calib.px_to_angle
        delta_x = coeff_x[0] * pixel_center[0]
        delta_y = coeff_y[0] * pixel_center[1]
        return delta_x, delta_y


# ══════════════════════════════════════════════
# VisualServoController — 閉迴路伺服控制器
# 將 VisionSystem 與 Motor.RobotArm 串接
# ══════════════════════════════════════════════
class VisualServoController:
    """
    閉迴路視覺伺服：
      1. 擷取影像
      2. 偵測目標物件
      3. 計算角度誤差
      4. 驅動手臂補正
      5. 反覆直到誤差收斂或超時
    """

    def __init__(self, vision: VisionSystem, arm):
        """
        vision: VisionSystem 實體
        arm:    Motor.RobotArm 實體 (Motor.arm)
        """
        self.vision = vision
        self.arm    = arm

        # 控制參數
        self.kp_x: float = 0.3        # 水平比例增益 (角度/像素比例)
        self.kp_y: float = 0.3        # 垂直比例增益
        self.dead_zone: int = 10      # 死區 (px)：小於此偏差不修正
        self.max_iter: int = 30       # 最大迭代次數
        self.loop_delay: float = 0.1  # 每次迭代等待時間 (s)
        self.converge_px: int = 8     # 收斂門檻 (px)
        self.target_color: str = "red"

        # 狀態
        self.is_running: bool = False
        self.last_error: tuple = (0.0, 0.0)
        self.status_callback = None   # 可由 UI 注入：fn(msg: str, frame: np.ndarray)

    def _log(self, msg: str, frame=None):
        print(f"[VisualServo] {msg}")
        if self.status_callback:
            self.status_callback(msg, frame)

    def run_once(self, color: str | None = None) -> dict:
        """
        執行一輪視覺伺服，回傳結果字典：
        {
            "success": bool,
            "iterations": int,
            "final_error": (ex, ey),  # 最終像素誤差
            "message": str
        }
        """
        color = color or self.target_color
        self.is_running = True

        for i in range(self.max_iter):
            if not self.is_running:
                return {"success": False, "iterations": i, "final_error": (0,0), "message": "中途停止"}

            frame = self.vision.capture()
            if frame is None:
                self._log("擷取影像失敗")
                break

            corrected = self.vision.apply_corrections(frame)
            detections = self.vision.detect_objects(corrected, color=color)

            if not detections:
                self._log(f"[{i+1}] 未偵測到 {color} 物件，繼續等待...")
                preview = corrected
                self._log(f"[{i+1}] 搜尋中...", preview)
                time.sleep(self.loop_delay)
                continue

            best = detections[0]
            px, py = best["center"]
            ex, ey = float(px), float(py)
            self.last_error = (ex, ey)

            preview = self.vision.draw_detections(corrected, detections)
            self._log(f"[{i+1}] 誤差=({ex:.1f},{ey:.1f})px", preview)

            # 收斂判斷
            if abs(ex) <= self.converge_px and abs(ey) <= self.converge_px:
                self._log(f"收斂！({ex:.1f},{ey:.1f})px ≤ {self.converge_px}px")
                self.is_running = False
                return {"success": True, "iterations": i+1, "final_error": (ex, ey), "message": "收斂成功"}

            # 超過死區才修正
            if abs(ex) > self.dead_zone or abs(ey) > self.dead_zone:
                self._apply_correction(ex, ey)

            time.sleep(self.loop_delay)

        self.is_running = False
        return {"success": False, "iterations": self.max_iter,
                "final_error": self.last_error, "message": f"超過最大迭代次數 {self.max_iter}"}

    def _apply_correction(self, ex: float, ey: float):
        """
        根據像素誤差計算並套用手臂角度補正。
        通道對應：
          Channel 0 (旋轉底座) ← 水平誤差 ex
          Channel 1 (垂直高低) ← 垂直誤差 ey
        可依實際機構調整映射。
        """
        # 像素誤差 → 角度差 (使用 px_to_angle 係數)
        da_x, da_y = self.vision.compute_angle_delta((ex, ey))

        # 乘以比例增益
        da_x *= self.kp_x
        da_y *= self.kp_y

        # 限制每次最大補正量 (防暴衝)
        da_x = max(-5.0, min(5.0, da_x))
        da_y = max(-5.0, min(5.0, da_y))

        new_a0 = self.arm.current_angles[0] + da_x
        new_a1 = self.arm.current_angles[1] + da_y

        self._log(f"  補正: ch0 {self.arm.current_angles[0]:.1f}→{new_a0:.1f}°, "
                  f"ch1 {self.arm.current_angles[1]:.1f}→{new_a1:.1f}°")

        self.arm.set_servo_angle(0, new_a0)
        self.arm.set_servo_angle(1, new_a1)

    def stop(self):
        self.is_running = False


# ══════════════════════════════════════════════
# 模組級便利 API (讓 main.py 直接 import 使用)
# ══════════════════════════════════════════════

# 單例：程式啟動時建立一次即可
vision_system: VisionSystem | None = None
servo_controller: VisualServoController | None = None


def init(arm=None) -> tuple[VisionSystem, VisualServoController | None]:
    """
    初始化模組單例。
    arm: Motor.arm 物件；若為 None 則只初始化 VisionSystem。
    """
    global vision_system, servo_controller
    vision_system = VisionSystem()
    if arm is not None:
        servo_controller = VisualServoController(vision_system, arm)
    return vision_system, servo_controller


def capture_and_detect(color: str = "red") -> tuple[np.ndarray | None, list[dict]]:
    """便利函式：擷取→校正→偵測，一步完成"""
    if vision_system is None:
        raise RuntimeError("請先呼叫 vision.init()")
    frame = vision_system.capture()
    if frame is None:
        return None, []
    corrected = vision_system.apply_corrections(frame)
    detections = vision_system.detect_objects(corrected, color=color)
    return corrected, detections

# ══════════════════════════════════════════════
# ArucoCalibrator — ArUco 自動校準控制器
# ══════════════════════════════════════════════
class ArucoCalibrator:
    """
    使用 ArUco Marker 自動校準手臂零點偏移量。
    
    流程：
      1. 手臂移到初始位置 [0, 0, 0, 90]
      2. 偵測 ArUco Marker 中心在畫面中的偏差
      3. 調整 CH1（左右）讓 Marker 對準畫面水平中心
      4. 調整 CH0（前後）讓 Marker 對準畫面垂直中心
      5. 記錄此時的角度偏移量存入資料庫
    """

    MARKER_SIZE_MM = 24.0          # Marker 實際尺寸 (mm)
    ARUCO_DICT     = cv2.aruco.DICT_4X4_50
    TARGET_ID      = 0             # 要追蹤的 Marker ID

    def __init__(self, vision: VisionSystem, arm):
        self.vision = vision
        self.arm    = arm

        # ArUco 偵測器
        aruco_dict   = cv2.aruco.getPredefinedDictionary(self.ARUCO_DICT)
        params       = cv2.aruco.DetectorParameters()
        params.adaptiveThreshConstant   = 5
        params.minMarkerPerimeterRate   = 0.01
        self.detector = cv2.aruco.ArucoDetector(aruco_dict, params)

        # 控制參數
        self.kp_x        : float = 0.15   # 水平比例增益 (角度/像素)
        self.kp_y        : float = 0.15   # 垂直比例增益
        self.dead_zone   : int   = 8      # 死區 (px)
        self.converge_px : int   = 10     # 收斂門檻 (px)
        self.max_iter    : int   = 60     # 最大迭代次數
        self.loop_delay  : float = 0.25   # 每次迭代等待 (s)
        self.max_step    : float = 2.0    # 單次最大補正角度（小步慢走）

        # 狀態
        self.is_running      : bool  = False
        self.status_callback        = None  # fn(msg, frame)
        self.calib_offset    : list  = [0.0, 0.0, 0.0, 0.0]

    def _log(self, msg: str, frame=None):
        if self.status_callback:
            self.status_callback(msg, frame)

    def detect_marker(self, frame: np.ndarray) -> dict | None:
        """
        偵測目標 Marker，回傳中心偏差（以畫面中心為原點）。
        回傳 {"center": (cx, cy), "corners": ..., "size": px}
        回傳 None 代表未偵測到。
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self.detector.detectMarkers(gray)

        if ids is None:
            return None

        for i, marker_id in enumerate(ids.flatten()):
            if marker_id != self.TARGET_ID:
                continue
            c   = corners[i][0]
            cx  = int(c[:, 0].mean())
            cy  = int(c[:, 1].mean())
            # 以畫面中心為原點
            h, w = frame.shape[:2]
            cx -= w // 2
            cy  = h // 2 - cy   # y 軸朝上為正
            size = float(np.linalg.norm(c[0] - c[1]))  # 邊長像素數
            return {"center": (cx, cy), "corners": corners[i], "size": size}

        return None

    def draw_marker(self, frame: np.ndarray, result: dict) -> np.ndarray:
        """在畫面上繪製偵測結果"""
        out = frame.copy()
        h, w = out.shape[:2]
        # 畫面中心十字
        cv2.line(out, (w//2-20, h//2), (w//2+20, h//2), (0, 255, 255), 1)
        cv2.line(out, (w//2, h//2-20), (w//2, h//2+20), (0, 255, 255), 1)
        # Marker 輪廓
        cv2.aruco.drawDetectedMarkers(out, [result["corners"]])
        # 中心點
        cx_img = result["center"][0] + w // 2
        cy_img = h // 2 - result["center"][1]
        cv2.circle(out, (cx_img, cy_img), 5, (0, 0, 255), -1)
        cv2.putText(out, f"({result['center'][0]},{result['center'][1]})",
                    (cx_img + 8, cy_img - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        return out

    def _align_marker_ch1(self) -> dict | None:
        """
        閉迴路調整 CH1 直到 Marker 對準畫面水平中心。
        回傳收斂時的偵測結果，失敗回傳 None。
        """
        for i in range(self.max_iter):
            if not self.is_running:
                return None
            frame = self.vision.capture()
            if frame is None:
                time.sleep(self.loop_delay)
                continue
            result = self.detect_marker(frame)
            preview = self.draw_marker(frame, result) if result else frame
            if result is None:
                self._log(f"  [{i+1}] 未偵測到 Marker...", preview)
                time.sleep(self.loop_delay)
                continue
            cx, _ = result["center"]
            self._log(f"  [{i+1}] 水平偏差={cx}px", preview)
            if abs(cx) <= self.converge_px:
                return result
            if abs(cx) > self.dead_zone:
                # cx > 0 = Marker 在右側，需減少 PWM（往左拉回）
                # cx < 0 = Marker 在左側，需增加 PWM（往右推）
                # 直接操作 PWM 而非角度，避免換算誤差
                delta_pwm = int(self.kp_x * cx * 15)
                delta_pwm = max(-30, min(30, delta_pwm))
                new_pwm = int(self.arm.current_pwm[1] - delta_pwm)
                duty = int(new_pwm * 0.2048)
                self.arm.pwm_driver.setPWM(1, 0, duty)
                self.arm.current_pwm[1] = new_pwm
            time.sleep(self.loop_delay)
        return None

    def run(self) -> dict:
        """
        PWM 掃描校準流程：
          點1：手臂移到 [0,0,0,0]，記錄 CH1 Base PWM
          點2：CH1 PWM 慢慢增加，等 ArUco 出現在畫面中心後停下
               記錄此時 PWM，對應角度 = 90 度
          算出每度增量 = (PWM2 - PWM1) / 90
        """
        self.is_running = True

        # ── 步驟1：移到 [0,0,0,0] 再打開夾爪避免擋住畫面 ──
        self._log("移到 [0,0,0,0]...")
        self.arm.to_new_angle_direct([0, 0, 0, 0])
        time.sleep(0.3)
        self._log("打開夾爪 [0,0,0,90]...")
        self.arm.to_new_angle_direct([0, 0, 0, 90])
        time.sleep(0.3)

        # ── 點1：記錄此時 CH1 的 PWM（0度）──
        pwm1 = float(self.arm.current_pwm[1])
        self._log(f"點1 PWM={pwm1:.0f}（CH1=0度）")

        # 暖機：等攝影機曝光穩定
        self._log("暖機中...")
        for _ in range(15):
            self.vision.capture()
            time.sleep(0.05)

        # ── 點2：雙向掃描找 ArUco ──
        pwm_step     = 5        # 每步 PWM 變化量（慢一點）
        scan_range   = int(11 * 100)  # 最多掃 100 度範圍
        pwm2         = None
        found_dir    = 0        # +1 或 -1

        for direction in [1, -1]:   # 先試增加，再試減少
            if not self.is_running:
                break
            dir_name = "增加" if direction == 1 else "減少"
            self._log(f"往 PWM {dir_name} 方向掃描...")
            current_pwm = pwm1

            for _ in range(scan_range // pwm_step):
                if not self.is_running:
                    break
                current_pwm += pwm_step * direction
                duty = int(current_pwm * 0.2048)
                self.arm.pwm_driver.setPWM(1, 0, duty)
                self.arm.current_pwm[1] = int(current_pwm)
                time.sleep(0.15)   # 等馬達到位再拍照

                frame = self.vision.capture()
                if frame is None:
                    continue

                result = self.detect_marker(frame)
                preview = self.draw_marker(frame, result) if result else frame
                self._log(f"  PWM={current_pwm:.0f} {'偵測到' if result else '搜尋中'}...", preview)

                if result is None:
                    continue

                cx, _ = result["center"]
                self._log(f"  Marker 出現！水平偏差={cx}px")

                # PWM增加→手臂往左→Marker從右側進入往左移
                # cx > 0 = Marker 在右側 → 繼續掃（還沒到中心）
                # cx ≈ 0 = 對準了
                # cx < 0 = Marker 過了中心到左側 → 閉迴路微調拉回來

                if abs(cx) <= self.converge_px:
                    # 已在死區，直接記錄
                    pwm2 = float(self.arm.current_pwm[1])
                    found_dir = direction
                    self._log(f"對準完成！點2 PWM={pwm2:.0f}")
                    break
                elif cx < 0:
                    # Marker 在左側，繼續增加 PWM 讓它往右移到中心
                    continue
                else:
                    # cx > 0，Marker 過了中心到右側，閉迴路微調拉回來
                    self._log(f"  Marker 過中心(cx={cx})，閉迴路微調...")
                    aligned = self._align_marker_ch1()
                    if aligned:
                        pwm2 = float(self.arm.current_pwm[1])
                        found_dir = direction
                        self._log(f"對準完成！點2 PWM={pwm2:.0f}")
                        break

            if pwm2 is not None:
                break

            # 這個方向找不到，回到起點再試另一個方向
            if direction == 1:
                self._log("此方向未找到，回到起點試另一方向...")
                duty = int(pwm1 * 0.2048)
                self.arm.pwm_driver.setPWM(1, 0, duty)
                self.arm.current_pwm[1] = int(pwm1)
                time.sleep(0.5)

        if pwm2 is None or not self.is_running:
            self.is_running = False
            return {"success": False, "pwm_per_deg": 0,
                    "message": "雙向掃描完成但未找到 ArUco，請確認 Marker 擺放位置"}

        # ── 計算每度增量 ──
        # found_dir=+1 表示 PWM 增加對應角度增加
        pwm_per_deg = (pwm2 - pwm1) / 90.0
        self._log(f"每度 PWM 增量 = {pwm_per_deg:.3f}（原本 11.0，方向={'正' if found_dir==1 else '負'}）")

        # ── 更新資料庫 ──
        self._save_pwm_per_deg(pwm_per_deg)
        self.arm.pwm_per_deg = pwm_per_deg

        msg = f"校準完成！每度增量={pwm_per_deg:.3f}"
        self._log(msg)
        # 強制更新 current_angles[1] 為 90 度，讓 to_new_angle_direct 知道目前位置
        self.arm.current_angles[1] = 90
        self._log("回到初始位置...")
        self.arm.to_new_angle_direct([0, 0, 0, 90])
        self.is_running = False
        return {"success": True, "pwm_per_deg": pwm_per_deg, "message": msg}

    def _save_pwm_per_deg(self, pwm_per_deg: float):
        """將每度 PWM 增量存入資料庫"""
        try:
            import json as _json
            with setsql.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT calib_json FROM vision_calib WHERE id=1;")
                    row = cur.fetchone()
                    data = _json.loads(row[0]) if row else {}
                    data["pwm_per_deg"]    = pwm_per_deg
                    data["aruco_calibrated"] = True
                    payload = _json.dumps(data)
                    cur.execute("""
                        INSERT INTO vision_calib (id, calib_json, updated_at)
                        VALUES (1, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE
                            SET calib_json = EXCLUDED.calib_json,
                                updated_at  = EXCLUDED.updated_at;
                    """, (payload,))
            # 同時更新 Motor 的計算參數
            self.arm.pwm_per_deg = pwm_per_deg
            print(f"[ArUco] pwm_per_deg={pwm_per_deg:.3f} 已存入資料庫")
        except Exception as e:
            print(f"[ArUco] 儲存失敗：{e}")

    def _save_offset(self):
        """將校準偏移量存入資料庫 vision_calib"""
        try:
            import json as _json
            with setsql.get_db_connection() as conn:
                with conn.cursor() as cur:
                    # 讀取現有 calib_json
                    cur.execute("SELECT calib_json FROM vision_calib WHERE id=1;")
                    row = cur.fetchone()
                    data = _json.loads(row[0]) if row else {}
                    data["aruco_offset"] = self.calib_offset
                    data["aruco_calibrated"] = True
                    payload = _json.dumps(data)
                    cur.execute("""
                        INSERT INTO vision_calib (id, calib_json, updated_at)
                        VALUES (1, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (id) DO UPDATE
                            SET calib_json = EXCLUDED.calib_json,
                                updated_at  = EXCLUDED.updated_at;
                    """, (payload,))
            print("[ArUco] 校準偏移量已存入資料庫")
        except Exception as e:
            print(f"[ArUco] 儲存失敗：{e}")

    def load_offset(self) -> list:
        """從資料庫讀取校準偏移量"""
        try:
            import json as _json
            with setsql.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT calib_json FROM vision_calib WHERE id=1;")
                    row = cur.fetchone()
            if row:
                data = _json.loads(row[0])
                self.calib_offset = data.get("aruco_offset", [0.0]*4)
                print(f"[ArUco] 已讀取校準偏移量：{self.calib_offset}")
                return self.calib_offset
        except Exception as e:
            print(f"[ArUco] 讀取失敗：{e}")
        return [0.0, 0.0, 0.0, 0.0]

    def stop(self):
        self.is_running = False


# ── 模組級單例 ──
aruco_calibrator: ArucoCalibrator | None = None

def init_aruco(arm=None) -> ArucoCalibrator | None:
    """初始化 ArUco 校準器，在 vision.init() 之後呼叫"""
    global aruco_calibrator
    if vision_system is None:
        print("[ArUco] 請先呼叫 vision.init()")
        return None
    if arm is None:
        return None
    aruco_calibrator = ArucoCalibrator(vision_system, arm)
    aruco_calibrator.load_offset()
    return aruco_calibrator