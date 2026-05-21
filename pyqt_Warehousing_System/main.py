import sys
import time

def run_ui():
    """啟動圖形介面"""
    
    # --- 延遲匯入：確保只有在環境安裝好後才載入這些模組 ---
    try:
        from PyQt5 import QtWidgets, QtCore
        from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel
        from PyQt5.QtCore import QThread, pyqtSignal
        import copy
        from functools import partial
        import setsql
        setsql.initialize_all()
        import Motor
        import vision
        from PyQt5.QtGui import QImage, QPixmap
        
    except ImportError as e:
        print(f"\n[錯誤] 缺少必要模組: {e}")
        print("請先執行安裝指令： sudo python3 main.py --install")
        sys.exit(1)

    # --- 定義工作執行緒 (已針對 Motor.arm 優化) ---
    class RunMotorWorker(QThread):
        pwmvalue_updated = pyqtSignal(list)
        finished = pyqtSignal()

        def __init__(self, journey):
            super().__init__()
            self.journey = journey
            self.running = True
            self.paused = False

        def run(self):
            # 使用 Motor.arm (OOP 寫法) 避免直接讀取全域變數
            # 注意：這裡假設 Motor.py 已更新並提供了 arm 物件
            # 如果您尚未更新 Motor.py，請暫時改回 Motor.initial
            try:
                Position = Motor.arm.initial_pos.copy()
            except AttributeError:
                # 相容舊版 Motor.py
                Position = Motor.initial.copy()

            for JourneyNode in self.journey:
                # 檢查是否到達目標節點
                while JourneyNode != Position:
                    # 暫停處理
                    while self.paused:
                        if not self.running: return
                        time.sleep(0.1)
                    
                    if not self.running: return
                    
                    # 移動處理
                    for y, pos in enumerate(JourneyNode):
                        if pos != Position[y]:
                            value = pos - Position[y]
                            if value != 0:
                                # 優先使用新版 Motor.arm 方法
                                try:
                                    speed = Motor.arm.calculate_step_speed(value, 2)
                                    Position[y] -= speed
                                    Position[y] = int(round(Position[y]))
                                    Motor.arm.set_servo_angle(y, Position[y])
                                    current_pwm = Motor.arm.current_pwm
                                except AttributeError:
                                    # 相容舊版 Motor.py
                                    speed = Motor.MotorSpeed(value, 2)
                                    Position[y] -= speed
                                    Position[y] = int(round(Position[y]))
                                    Motor.pwm.ServoAngle(y, Position[y])
                                    current_pwm = Motor.pwmvalue

                                self.pwmvalue_updated.emit(current_pwm)
                    
                    time.sleep(0.02) # 控制移動平滑度
            
            self.finished.emit()

        def stop(self):
            self.running = False

        def pause(self):
            self.paused = True

        def resume(self):
            self.paused = False

    # --- 定義主視窗 (MainWindow) ---
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle('Robotic Arm Control System')
            self.resize(850, 600)
            
            # 資料變數初始化
            self.Data = ["", ""]
            self.labelrange = []
            self.labelangle = []
            self.page2Button = []
            self.learn_button = []
            self.learn_name = ""
            self.learn_data = []
            self.is_paused = False
            self.worker = None

            # 初始狀態上傳 (200: System Ready)
            setsql.state_update(200)

            # 建立堆疊式頁面
            self.stacked_widget = QStackedWidget()
            self.setup_ui_pages()
            self.setCentralWidget(self.stacked_widget)

            # 全域攝影機計時器（常駐，所有頁面共用）
            self._global_cam_timer = QtCore.QTimer()
            self._global_cam_timer.timeout.connect(self._global_cam_tick)
            self._global_cam_timer.start(200)  # 10 fps

        def setup_ui_pages(self):
            self.page1      = self.create_page1()
            self.move_page  = self.create_move_page()
            self.teach_page = self.create_teach_page()
            self.page5      = self.create_page5()
            self.page8      = self.create_page8()

            pages = [self.page1, self.move_page, self.teach_page, self.page5, self.page8]
            for page in pages:
                self.stacked_widget.addWidget(page)

        # --- UI 建構輔助函式 ---
        def create_page1(self):
            page = QtWidgets.QWidget()
            self.createTitle('Warehousing System Majorization', page, 'font-size:48px;', 10, 0)
            self.createButton("Move",   page, (350, 280, 150, 150), self.show_move_page)
            self.createButton("Teach",  page, (120, 280, 150, 150), self.show_teach_page)
            self.createButton("Exit",   page, (350, 470, 150, 50),  self.exit)
            self.createButton("Vision", page, (570, 280, 150, 150), self.show_page8)
            return page

        def create_move_page(self):
            """合併後的 Move 頁面：下拉選櫃位、Place/Pick、實時座標、暫停/繼續"""
            from PyQt5 import QtWidgets, QtCore

            page = QtWidgets.QWidget()

            # ── 標題 ──
            self.move_title = self.createTitle("Move", page, 'font-size:48px;', 10, 0)

            # ── 櫃位下拉選單 ──
            lbl = QtWidgets.QLabel("Warehouse :", page)
            lbl.setStyleSheet('font-size:28px;')
            lbl.setGeometry(50, 90, 220, 50)

            self.move_combo = QtWidgets.QComboBox(page)
            self.move_combo.setStyleSheet('font-size:26px;')
            self.move_combo.setGeometry(280, 90, 200, 50)

            # ── Place / Pick 按鈕 ──
            self.move_place_btn = QtWidgets.QPushButton("Place", page)
            self.move_place_btn.setStyleSheet('font-size:30px; background:#4a90d9; color:white; border-radius:8px;')
            self.move_place_btn.setGeometry(120, 170, 180, 80)
            self.move_place_btn.clicked.connect(lambda: self.start_move("Place"))

            self.move_pick_btn = QtWidgets.QPushButton("Pick", page)
            self.move_pick_btn.setStyleSheet('font-size:30px; background:#e07b39; color:white; border-radius:8px;')
            self.move_pick_btn.setGeometry(550, 170, 180, 80)
            self.move_pick_btn.clicked.connect(lambda: self.start_move("Pick"))

            # ── 實時座標顯示 ──
            coord_style = 'font-size:22px;'
            self.pwm0_label = self.createTitle("CH0 : ---", page, coord_style, 50, 280)
            self.pwm1_label = self.createTitle("CH1 : ---", page, coord_style, 50, 320)
            self.pwm2_label = self.createTitle("CH2 : ---", page, coord_style, 50, 360)
            self.pwm3_label = self.createTitle("CH3 : ---", page, coord_style, 50, 400)
            for lbl in [self.pwm0_label, self.pwm1_label, self.pwm2_label, self.pwm3_label]:
                lbl.setMinimumWidth(400)

            # ── 進度狀態 ──
            self.move_status_label = QtWidgets.QLabel("", page)
            self.move_status_label.setStyleSheet('font-size:22px; color:#555;')
            self.move_status_label.setGeometry(50, 440, 600, 36)

            # ── 狀態按鈕區 (右側) ──
            # Pause/Resume 按鈕：移動時才可按
            self.pause_resume_button = QtWidgets.QPushButton("Pause", page)
            self.pause_resume_button.setStyleSheet('font-size:26px; background:#f0c040; border-radius:6px;')
            self.pause_resume_button.setGeometry(335, 170, 180, 80)
            self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
            self.pause_resume_button.setEnabled(False)
            self.pause_resume_button.setStyleSheet(
                'font-size:26px; background:#cccccc; color:#888; border-radius:6px;')

            # ── 攝影機預覽（右下角）──
            self.move_cam_preview = QtWidgets.QLabel(page)
            self.move_cam_preview.setGeometry(490, 270, 340, 255)
            self.move_cam_preview.setStyleSheet('background:#111; border:1px solid #555;')
            self.move_cam_preview.setAlignment(QtCore.Qt.AlignCenter)
            self.move_cam_preview.setText("Camera")

            # ── 返回 ──
            back_btn = QtWidgets.QPushButton("Back", page)
            back_btn.setStyleSheet('font-size:24px;')
            back_btn.setGeometry(50, 500, 130, 50)
            back_btn.clicked.connect(self.show_page1)

            return page

        def create_teach_page(self):
            """合併 Teach 頁面：上方選櫃位+Create，下方 Step 下拉+角度編輯"""
            from PyQt5 import QtWidgets, QtCore

            page = QtWidgets.QWidget()

            # ── 標題 ──
            self.createTitle("Teaching", page, 'font-size:48px;', 10, 0)

            # ── 櫃位選單 + Create 按鈕 ──
            lbl = QtWidgets.QLabel("Warehouse :", page)
            lbl.setStyleSheet('font-size:26px;')
            lbl.setGeometry(50, 80, 200, 44)

            self.teach_combo = QtWidgets.QComboBox(page)
            self.teach_combo.setStyleSheet('font-size:24px;')
            self.teach_combo.setGeometry(260, 80, 220, 44)
            self.teach_combo.currentTextChanged.connect(self.on_teach_warehouse_changed)

            self.teach_create_btn = QtWidgets.QPushButton("+ Create", page)
            self.teach_create_btn.setStyleSheet('font-size:22px; background:#4a90d9; color:white; border-radius:6px;')
            self.teach_create_btn.setGeometry(500, 80, 120, 44)
            self.teach_create_btn.clicked.connect(self.show_teach_create)

            self.teach_drop_btn = QtWidgets.QPushButton("Drop", page)
            self.teach_drop_btn.setStyleSheet('font-size:22px; background:#d9534f; color:white; border-radius:6px;')
            self.teach_drop_btn.setGeometry(634, 80, 100, 44)
            self.teach_drop_btn.clicked.connect(self.teach_drop_warehouse)

            # ── Create 輸入區（預設隱藏）──
            self.teach_input_frame = QtWidgets.QWidget(page)
            self.teach_input_frame.setGeometry(50, 135, 700, 50)
            self.teach_input_frame.hide()

            inp_lbl = QtWidgets.QLabel("Name :", self.teach_input_frame)
            inp_lbl.setStyleSheet('font-size:22px;')
            inp_lbl.setGeometry(0, 8, 90, 36)

            self.teach_input = QtWidgets.QLineEdit(self.teach_input_frame)
            self.teach_input.setStyleSheet('font-size:22px;')
            self.teach_input.setGeometry(96, 4, 200, 40)
            self.teach_input.setMaxLength(20)

            confirm_btn = QtWidgets.QPushButton("OK", self.teach_input_frame)
            confirm_btn.setStyleSheet('font-size:20px; background:#5cb85c; color:white; border-radius:4px;')
            confirm_btn.setGeometry(310, 4, 70, 40)
            confirm_btn.clicked.connect(self.teach_confirm_create)

            cancel_btn = QtWidgets.QPushButton("Cancel", self.teach_input_frame)
            cancel_btn.setStyleSheet('font-size:20px; border-radius:4px;')
            cancel_btn.setGeometry(390, 4, 90, 40)
            cancel_btn.clicked.connect(lambda: self.teach_input_frame.hide())

            # ── Step 下拉選單 ──
            sep = QtWidgets.QFrame(page)
            sep.setFrameShape(QtWidgets.QFrame.HLine)
            sep.setGeometry(30, 196, 790, 2)

            step_lbl = QtWidgets.QLabel("Step :", page)
            step_lbl.setStyleSheet('font-size:24px;')
            step_lbl.setGeometry(50, 208, 90, 44)

            self.teach_step_combo = QtWidgets.QComboBox(page)
            self.teach_step_combo.setStyleSheet('font-size:22px;')
            self.teach_step_combo.setGeometry(148, 208, 300, 44)
            self.teach_step_combo.currentIndexChanged.connect(self.on_teach_step_changed)

            self.teach_go_btn = QtWidgets.QPushButton("GO", page)
            self.teach_go_btn.setStyleSheet('font-size:20px; background:#5a3e8a; color:white; border-radius:4px;')
            self.teach_go_btn.setGeometry(458, 208, 60, 44)
            self.teach_go_btn.clicked.connect(self.teach_go)

            self.teach_add_btn = QtWidgets.QPushButton("+ Add", page)
            self.teach_add_btn.setStyleSheet('font-size:20px; background:#5cb85c; color:white; border-radius:4px;')
            self.teach_add_btn.setGeometry(528, 208, 90, 44)
            self.teach_add_btn.clicked.connect(self.teach_step_add)

            self.teach_del_btn = QtWidgets.QPushButton("Del", page)
            self.teach_del_btn.setStyleSheet('font-size:20px; background:#d9534f; color:white; border-radius:4px;')
            self.teach_del_btn.setGeometry(628, 208, 70, 44)
            self.teach_del_btn.clicked.connect(self.teach_step_del)

            # ── 角度調整 ──
            self.teach_labelangle = []
            step_size_lbl = QtWidgets.QLabel("Step size:", page)
            step_size_lbl.setStyleSheet('font-size:20px;')
            step_size_lbl.setGeometry(500, 268, 110, 32)

            self.teach_step_size_combo = QtWidgets.QComboBox(page)
            self.teach_step_size_combo.addItems(["1", "5", "10"])
            self.teach_step_size_combo.setStyleSheet('font-size:20px;')
            self.teach_step_size_combo.setGeometry(616, 268, 70, 32)
            self.teach_step_size = 1
            self.teach_step_size_combo.currentIndexChanged.connect(
                lambda i: setattr(self, 'teach_step_size', [1,5,10][i]))

            ch_names = ["CH0 (Rotate)", "CH1 (Arm Up/Down)", "CH2 (Elbow)", "CH3 (Gripper)"]
            for i in range(4):
                y = 270 + i * 52
                lbl2 = QtWidgets.QLabel(ch_names[i], page)
                lbl2.setStyleSheet('font-size:20px;')
                lbl2.setGeometry(50, y + 8, 200, 32)

                val_lbl = QtWidgets.QLabel("---", page)
                val_lbl.setStyleSheet('font-size:22px; font-weight:bold;')
                val_lbl.setGeometry(258, y + 4, 80, 36)
                val_lbl.setMinimumWidth(80)
                self.teach_labelangle.append(val_lbl)

                btn_p = QtWidgets.QPushButton("+", page)
                btn_p.setStyleSheet('font-size:22px;')
                btn_p.setGeometry(348, y, 60, 44)
                btn_p.clicked.connect(partial(self.teach_set_angle, i, 1))

                btn_m = QtWidgets.QPushButton("-", page)
                btn_m.setStyleSheet('font-size:22px;')
                btn_m.setGeometry(418, y, 60, 44)
                btn_m.clicked.connect(partial(self.teach_set_angle, i, -1))

            # ── 攝影機預覽（右下角）──
            self.teach_cam_preview = QtWidgets.QLabel(page)
            self.teach_cam_preview.setGeometry(490, 300, 340, 255)
            self.teach_cam_preview.setStyleSheet('background:#111; border:1px solid #555;')
            self.teach_cam_preview.setAlignment(QtCore.Qt.AlignCenter)
            self.teach_cam_preview.setText("Camera Off")

            self.teach_cam_btn = QtWidgets.QPushButton("Camera", page)
            self.teach_cam_btn.setStyleSheet('font-size:18px; background:#f0c040; border-radius:4px;')
            self.teach_cam_btn.setGeometry(360, 510, 120, 36)
            self.teach_cam_btn.setCheckable(True)
            self.teach_cam_btn.clicked.connect(self._teach_toggle_cam)

            # 計時器（Live Preview）
            self._teach_cam_timer = QtCore.QTimer()
            self._teach_cam_timer.timeout.connect(self._teach_cam_tick)

            # ── 底部按鈕 ──
            back_btn = QtWidgets.QPushButton("Back", page)
            back_btn.setStyleSheet('font-size:24px;')
            back_btn.setGeometry(50, 500, 130, 50)
            back_btn.clicked.connect(self.teach_back)

            self.teach_save_btn = QtWidgets.QPushButton("Save", page)
            self.teach_save_btn.setStyleSheet('font-size:24px; background:#5cb85c; color:white; border-radius:6px;')
            self.teach_save_btn.setGeometry(200, 500, 130, 50)
            self.teach_save_btn.clicked.connect(self.teach_save)

            return page

        def create_page5(self):
            page = QtWidgets.QWidget()
            self.createTitle("Set Initial", page, 'font-size:48px;', 10, 0)
            
            # 嘗試獲取 Range，相容新舊版
            try:
                ranges = Motor.arm.motor_ranges
            except AttributeError:
                ranges = Motor.MotorRange

            self.labelminrange = self.createTitle(f"Initial PWM：{ranges}", page, 'font-size:30px;', 10, 110)
            self.createTitle("+50", page, 'font-size:24px;', 30, 310)
            self.createTitle("-50", page, 'font-size:24px;', 30, 370)
            
            for i in range(4):
                y = 80 + i * 180
                label = self.createTitle(f"PWM{i}：{ranges[i]}", page, 'font-size:24px;', y, 250)
                label.setMinimumWidth(200)
                self.labelrange.append(label)
                self.createButton("+", page, (y, 310, 150, 50), partial(self.set_PWM, i, 50))
                self.createButton("-", page, (y, 370, 150, 50), partial(self.set_PWM, i, -50))
                
            self.createButton("Cancel", page, (50, 500, 130, 50), self.page5cancel)
            self.createButton("Save", page, (190, 500, 130, 50), self.saveMotorData)
            return page



        # --- 共用工具 ---
        def createTitle(self, text, parent, size, x, y):
            label = QtWidgets.QLabel(text, parent)
            label.setStyleSheet(size)
            label.move(x, y)
            label.adjustSize()
            return label

        def createButton(self, text, parent, geometry, onClick):
            Button = QtWidgets.QPushButton(text, parent)
            Button.setStyleSheet('font-size:30px;')
            Button.setGeometry(*geometry)
            Button.clicked.connect(onClick)
            return Button

        # --- 邏輯控制 ---
        def show_page1(self):
            setsql.state_update(200)
            self.Data = ["", ""]
            self.stacked_widget.setCurrentWidget(self.page1)

        def _global_cam_tick(self):
            """全域攝影機計時器：更新所有顯示攝影機畫面的頁面"""
            import cv2
            from PyQt5.QtGui import QImage, QPixmap
            if vision.vision_system is None:
                return
            frame = vision.vision_system.capture()
            if frame is None:
                return
            corrected = vision.vision_system.apply_corrections(frame)

            def to_pixmap(label, img):
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                return QPixmap.fromImage(qimg).scaled(
                    label.width(), label.height(), 1, 1)

            cur = self.stacked_widget.currentWidget()

            # Vision 頁面預覽（Live Preview 開啟時）
            if cur == self.page8 and hasattr(self, 'btn_live') and self.btn_live.isChecked():
                color = self.cmb_color.currentText()
                detections = vision.vision_system.detect_objects(corrected, color=color)
                display = vision.vision_system.draw_detections(corrected, detections)
                self.vision_preview.setPixmap(to_pixmap(self.vision_preview, display))

            # Move 頁面預覽
            elif cur == self.move_page:
                self.move_cam_preview.setPixmap(to_pixmap(self.move_cam_preview, corrected))

            # Teach 頁面預覽（Camera 按鈕開啟時）
            elif cur == self.teach_page and self.teach_cam_btn.isChecked():
                self.teach_cam_preview.setPixmap(to_pixmap(self.teach_cam_preview, corrected))

        def exit(self):
            setsql.state_update(100)
            Motor.stopAllPWM()
            self._global_cam_timer.stop()
            vision.vision_system.close_camera()
            sys.exit("Exit")

        def show_move_page(self):
            """進入 Move 頁面，刷新櫃位下拉選單"""
            setsql.state_update(300)
            self.move_combo.clear()
            self.KeyList = list(setsql.take_names())
            items = self.KeyList[2:] if len(self.KeyList) > 2 else []
            self.move_combo.addItems(items)
            # 重置狀態
            self.move_title.setText("Move")
            self.move_status_label.setText("")
            self.move_status_label.setStyleSheet('font-size:22px; color:#555;')
            for lbl in [self.pwm0_label, self.pwm1_label, self.pwm2_label, self.pwm3_label]:
                lbl.setText(lbl.text().split(":")[0] + " : ---")
            # Pause 灰色不可按
            self.pause_resume_button.setEnabled(False)
            self.pause_resume_button.setStyleSheet(
                'font-size:26px; background:#cccccc; color:#888; border-radius:6px;')
            self.pause_resume_button.setText("Pause")
            self.move_place_btn.setEnabled(True)
            self.move_pick_btn.setEnabled(True)
            self.stacked_widget.setCurrentWidget(self.move_page)

        def start_move(self, mode):
            """Place 或 Pick 按下後開始執行"""
            target = self.move_combo.currentText()
            if not target:
                self.move_status_label.setText("請先選擇櫃位")
                return

            self.Data = [mode, target]
            self.move_title.setText(f"{mode}  →  {target}")
            self.move_title.adjustSize()
            # 狀態：Moving
            self.move_status_label.setText("● Moving...")
            self.move_status_label.setStyleSheet('font-size:22px; color:#2a7ae2; font-weight:bold;')
            # 啟用 Pause 按鈕
            self.pause_resume_button.setEnabled(True)
            self.pause_resume_button.setStyleSheet(
                'font-size:26px; background:#f0c040; border-radius:6px;')
            self.pause_resume_button.setText("Pause")
            self.is_paused = False
            self.move_place_btn.setEnabled(False)
            self.move_pick_btn.setEnabled(False)

            journey = Motor.Warehouses(self.Data)
            self.worker = RunMotorWorker(journey)
            self.worker.pwmvalue_updated.connect(self.update_pwm_label)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()

        def toggle_pause_resume(self):
            if self.is_paused:
                setsql.state_update(300)
                self.worker.resume()
                self.pause_resume_button.setText("Pause")
                self.is_paused = False
            else:
                setsql.state_update(301)
                self.worker.pause()
                self.pause_resume_button.setText("Resume")
                self.is_paused = True

        def update_pwm_label(self, pwm_values):
            if self.stacked_widget.currentWidget() == self.move_page:
                try:
                    angles = Motor.arm.current_angles
                except AttributeError:
                    angles = Motor.anglevalue
                self.pwm0_label.setText(f"CH0 : PWM {pwm_values[0]:5d}  Angle {angles[0]:4d}°")
                self.pwm1_label.setText(f"CH1 : PWM {pwm_values[1]:5d}  Angle {angles[1]:4d}°")
                self.pwm2_label.setText(f"CH2 : PWM {pwm_values[2]:5d}  Angle {angles[2]:4d}°")
                self.pwm3_label.setText(f"CH3 : PWM {pwm_values[3]:5d}  Angle {angles[3]:4d}°")
                for lbl in [self.pwm0_label,self.pwm1_label,self.pwm2_label,self.pwm3_label]:
                    lbl.adjustSize()

        def on_worker_finished(self):
            # 狀態：Done
            self.move_status_label.setText("Done")
            self.move_status_label.setStyleSheet('font-size:22px; color:#5cb85c; font-weight:bold;')
            # Pause 灰色不可按
            self.pause_resume_button.setEnabled(False)
            self.pause_resume_button.setStyleSheet(
                'font-size:26px; background:#cccccc; color:#888; border-radius:6px;')
            self.pause_resume_button.setText("Pause")
            self.move_place_btn.setEnabled(True)
            self.move_pick_btn.setEnabled(True)

        def show_teach_page(self, select_name=None):
            """進入 Teach 頁面，刷新櫃位下拉"""
            setsql.state_update(201)
            self.teach_input_frame.hide()
            # 刷新下拉（暫停 signal 避免觸發變更）
            self.teach_combo.blockSignals(True)
            self.teach_combo.clear()
            self.KeyList = list(setsql.take_names())
            items = self.KeyList[1:] if len(self.KeyList) > 1 else []
            self.teach_combo.addItems(items)
            # 選定指定項目
            if select_name and select_name in items:
                self.teach_combo.setCurrentIndex(items.index(select_name))
            self.teach_combo.blockSignals(False)
            # 載入資料
            self._teach_load_current()
            self.stacked_widget.setCurrentWidget(self.teach_page)

        def _teach_load_current(self):
            """載入目前選擇的櫃位資料到 Step 下拉與角度標籤"""
            name = self.teach_combo.currentText()
            if not name:
                self.teach_step_combo.clear()
                for lbl in self.teach_labelangle: lbl.setText("---")
                return
            self.learn_name = name
            self.learn_data = setsql.read_sql(name)
            # 第一筆(prepare的第一row)是固定的，不顯示
            # Drop 按鈕：第一個櫃位不可刪
            # prepare 與 MotorRange 不可刪
            protected = {"prepare", "motorrange", "MotorRange"}
            is_protected = name.lower() in {"prepare", "motorrange", "calib"}
            self.teach_drop_btn.setEnabled(not is_protected)
            if is_protected:
                self.teach_drop_btn.setStyleSheet(
                    'font-size:22px; background:#aaaaaa; color:#666; border-radius:6px;')
            else:
                self.teach_drop_btn.setStyleSheet(
                    'font-size:22px; background:#d9534f; color:white; border-radius:6px;')
            self._teach_refresh_steps()

        def _teach_refresh_steps(self, preserve=False):
            """更新 Step 下拉選單內容"""
            cur = self.teach_step_combo.currentIndex() if preserve else 0
            self.teach_step_combo.blockSignals(True)
            self.teach_step_combo.clear()
            items = [f"Step {i+1}:  {', '.join(map(str, row))}"
                     for i, row in enumerate(self.learn_data)]
            self.teach_step_combo.addItems(items)
            cur = max(0, min(cur, self.teach_step_combo.count()-1))
            self.teach_step_combo.setCurrentIndex(cur)
            self.teach_step_combo.blockSignals(False)
            self.on_teach_step_changed(cur)

        def on_teach_warehouse_changed(self, _):
            self._teach_load_current()

        def on_teach_step_changed(self, idx):
            self.page6_update_value = idx
            if 0 <= idx < len(self.learn_data):
                for i in range(4):
                    self.teach_labelangle[i].setText(str(self.learn_data[idx][i]))

        def teach_set_angle(self, ch, direction):
            idx = self.page6_update_value
            if not (0 <= idx < len(self.learn_data)): return
            self.learn_data[idx][ch] += direction * self.teach_step_size
            self._teach_refresh_steps(preserve=True)
            Motor.to_new_angle(self.learn_data[idx])

        def teach_step_add(self):
            idx = self.page6_update_value
            val = copy.deepcopy(self.learn_data[idx]) if self.learn_data else [0,0,0,0]
            self.learn_data.insert(idx+1, val)
            self.page6_update_value = idx+1
            self._teach_refresh_steps()

        def teach_step_del(self):
            if not self.learn_data: return
            idx = self.page6_update_value
            self.learn_data.pop(idx)
            self.page6_update_value = max(0, min(idx, len(self.learn_data)-1))
            self._teach_refresh_steps()

        def teach_go(self):
            """移動手臂到目前選擇的 Step 位置"""
            idx = self.page6_update_value
            if 0 <= idx < len(self.learn_data):
                Motor.to_new_angle(self.learn_data[idx])

        def teach_back(self):
            # 關閉攝影機 timer
            self._teach_cam_timer.stop()
            self.teach_cam_btn.setChecked(False)
            self.teach_cam_preview.setText("Camera Off")
            Motor.to_new_angle([0, 0, 0, 90])
            self.show_page1()

        def _teach_toggle_cam(self, checked):
            # 常駐模式下只控制預覽顯示
            if checked:
                self.teach_cam_btn.setText("Stop")
            else:
                self.teach_cam_preview.setText("Camera Off")
                self.teach_cam_btn.setText("Camera")

        def _teach_cam_tick(self):
            import vision, cv2
            from PyQt5.QtGui import QImage, QPixmap
            if vision.vision_system is None:
                return
            frame = vision.vision_system.capture()
            if frame is None:
                return
            corrected = vision.vision_system.apply_corrections(frame)
            rgb = cv2.cvtColor(corrected, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg).scaled(
                self.teach_cam_preview.width(),
                self.teach_cam_preview.height(),
                1, 1)
            self.teach_cam_preview.setPixmap(pix)

        def teach_save(self):
            setsql.write_sql(self.learn_name, self.learn_data)
            self.teach_save_btn.setText("Done")
            self.teach_save_btn.setStyleSheet(
                'font-size:24px; background:#5cb85c; color:white; border-radius:6px;')
            QtCore.QTimer.singleShot(3000, self._teach_save_reset)

        def _teach_save_reset(self):
            self.teach_save_btn.setText("Save")
            self.teach_save_btn.setStyleSheet(
                'font-size:24px; background:#5cb85c; color:white; border-radius:6px;')

        def teach_drop_warehouse(self):
            name = self.teach_combo.currentText()
            if name:
                setsql.drop_table(name)
                self.show_teach_page()

        def show_teach_create(self):
            self.teach_input.clear()
            self.teach_input_frame.show()

        def teach_confirm_create(self):
            name = self.teach_input.text().strip()
            if name:
                setsql.add_table(name)
                self.teach_input_frame.hide()
                self.show_teach_page(select_name=name)

        def show_page5(self):
            self.page5cancel()
            setsql.state_update(202)
            self.stacked_widget.setCurrentWidget(self.page5)

        def set_PWM(self, value, setpwm):
            self.Range[value] += setpwm
            Motor.setinitial(self.Range)
            self.labelrange[value].setText(f"PWM{value}：{self.Range[value]}")

        def saveMotorData(self):
            setsql.write_sql('MotorRange', [self.Range])
            try:
                Motor.arm.motor_ranges = setsql.take_range()
                current_range = Motor.arm.motor_ranges
            except AttributeError:
                Motor.MotorRange = setsql.take_range()
                current_range = Motor.MotorRange
            
            self.labelminrange.setText(f"Initial PWM：{current_range}")
            Motor.Reset()

        def page5cancel(self):
            Motor.Reset()
            self.Range = setsql.take_range()
            for i in range(4):
                self.labelrange[i].setText(f"PWM{i}：{self.Range[i]}")
            self.show_page1()



        def create_page8(self):
            """視覺校正頁面"""
            from PyQt5 import QtWidgets, QtCore, QtGui

            page = QtWidgets.QWidget()

            # ── 標題 ──
            title = QtWidgets.QLabel("Vision Calibration", page)
            title.setGeometry(20, 10, 400, 30)
            title.setStyleSheet("font-size: 16pt; font-weight: bold;")

            # ── 攝影機預覽 ──
            self.vision_preview = QtWidgets.QLabel(page)
            self.vision_preview.setGeometry(20, 50, 480, 360)
            self.vision_preview.setStyleSheet("background-color: #111; border: 1px solid #555;")
            self.vision_preview.setAlignment(QtCore.Qt.AlignCenter)
            self.vision_preview.setText("Camera Off")

            # ── 狀態列 ──
            self.vision_status = QtWidgets.QLabel("Status: Ready", page)
            self.vision_status.setGeometry(20, 418, 700, 24)
            self.vision_status.setStyleSheet("color: #0a0;")

            # ── 控制面板 (右側) ──
            ctrl_x = 520

            # 區塊 1: 攝影機
            QtWidgets.QLabel("── Camera ──", page).setGeometry(ctrl_x, 50, 200, 20)

            self.btn_live = QtWidgets.QPushButton("Preview: OFF", page)
            self.btn_live.setGeometry(ctrl_x, 75, 200, 36)
            self.btn_live.setCheckable(True)
            self.btn_live.clicked.connect(self._vision_toggle_live)

            # 區塊 2: 色彩校正
            QtWidgets.QLabel("── Color Calibration ──", page).setGeometry(ctrl_x, 128, 200, 20)

            self.btn_auto_wb = QtWidgets.QPushButton("Auto White Balance", page)
            self.btn_auto_wb.setGeometry(ctrl_x, 152, 270, 36)
            self.btn_auto_wb.clicked.connect(self._vision_auto_wb)

            QtWidgets.QLabel("CLAHE:", page).setGeometry(ctrl_x, 194, 60, 26)
            self.chk_clahe = QtWidgets.QCheckBox("Enable", page)
            self.chk_clahe.setGeometry(ctrl_x + 65, 194, 80, 26)
            self.chk_clahe.setChecked(True)
            self.chk_clahe.stateChanged.connect(self._vision_toggle_clahe)

            # 區塊 3: 物件偵測
            QtWidgets.QLabel("── Object Detection ──", page).setGeometry(ctrl_x, 232, 200, 20)

            QtWidgets.QLabel("Color:", page).setGeometry(ctrl_x, 256, 50, 26)
            self.cmb_color = QtWidgets.QComboBox(page)
            self.cmb_color.setGeometry(ctrl_x + 55, 256, 100, 26)
            self.cmb_color.addItems(["red", "green", "blue", "yellow"])

            self.btn_detect = QtWidgets.QPushButton("Detect Once", page)
            self.btn_detect.setGeometry(ctrl_x, 288, 130, 36)
            self.btn_detect.clicked.connect(self._vision_detect_once)

            # 區塊 4: 透視校正
            QtWidgets.QLabel("── Perspective ──", page).setGeometry(ctrl_x, 338, 200, 20)

            self.btn_persp = QtWidgets.QPushButton("Set 4 Corner Points", page)
            self.btn_persp.setGeometry(ctrl_x, 362, 190, 36)
            self.btn_persp.clicked.connect(self._vision_set_perspective)

            # 區塊 5: 閉迴路伺服
            QtWidgets.QLabel("── Visual Servo ──", page).setGeometry(ctrl_x, 412, 200, 20)

            self.btn_servo_run = QtWidgets.QPushButton("Start Visual Servo", page)
            self.btn_servo_run.setGeometry(ctrl_x, 436, 180, 36)
            self.btn_servo_run.setStyleSheet("background-color: #2a7; color: white; font-weight: bold;")
            self.btn_servo_run.clicked.connect(self._vision_start_servo)

            self.btn_servo_stop = QtWidgets.QPushButton("Stop", page)
            self.btn_servo_stop.setGeometry(ctrl_x + 188, 436, 80, 36)
            self.btn_servo_stop.setStyleSheet("background-color: #c33; color: white;")
            self.btn_servo_stop.clicked.connect(self._vision_stop_servo)

            # 區塊 6: 儲存/返回
            self.btn_save_calib = QtWidgets.QPushButton("Save Calibration", page)
            self.btn_save_calib.setGeometry(ctrl_x, 484, 180, 36)
            self.btn_save_calib.clicked.connect(self._vision_save_calib)

            # ── Auto Calibrate ──
            QtWidgets.QLabel("── Auto Calibrate ──", page).setGeometry(ctrl_x, 530, 200, 20)

            self.btn_aruco_run = QtWidgets.QPushButton("Start Calibrate", page)
            self.btn_aruco_run.setStyleSheet('font-size:20px; background:#2a7ae2; color:white; border-radius:6px;')
            self.btn_aruco_run.setGeometry(ctrl_x, 554, 160, 36)
            self.btn_aruco_run.clicked.connect(self._aruco_start)

            self.btn_aruco_stop = QtWidgets.QPushButton("Stop", page)
            self.btn_aruco_stop.setStyleSheet('font-size:20px; background:#d9534f; color:white; border-radius:6px;')
            self.btn_aruco_stop.setGeometry(ctrl_x + 168, 554, 70, 36)
            self.btn_aruco_stop.clicked.connect(self._aruco_stop)

            btn_back = QtWidgets.QPushButton("Back", page)
            btn_back.setGeometry(20, 450, 100, 36)
            btn_back.clicked.connect(self.show_page1)

            btn_initial = QtWidgets.QPushButton("Initial", page)
            btn_initial.setStyleSheet('font-size:18px;')
            btn_initial.setGeometry(130, 450, 100, 36)
            btn_initial.clicked.connect(self.show_page5)

            # ── 內部計時器 (Live Preview) ──
            self._vision_timer = QtCore.QTimer()
            self._vision_timer.timeout.connect(self._vision_frame_tick)
            self._vision_worker = None

            return page


        # ── 攝影機控制 ──

        def _vision_open_camera(self):
            import vision
            if vision.vision_system and vision.vision_system.cap:
                self.vision_status.setText("Status: Camera is running.")
            else:
                self.vision_status.setText("Status: Camera not available.")

        def _vision_close_camera(self):
            # 常駐模式下不實際關閉，只停止 Live Preview
            self._vision_timer.stop()
            self.btn_live.setChecked(False)
            self.vision_preview.setText("Camera Off")
            self.vision_status.setText("Status: Live preview stopped.")

        def _vision_toggle_live(self, checked):
            if checked:
                self.btn_live.setText("Preview: ON")
                self.vision_status.setText("Status: Live preview running...")
            else:
                self.btn_live.setText("Preview: OFF")
                self.vision_preview.setText("Camera Off")
                self.vision_status.setText("Status: Live preview stopped.")

        def _vision_frame_tick(self):
            """計時器回呼：每 100ms 抓一幀更新預覽"""
            import vision
            color = self.cmb_color.currentText()
            frame = vision.vision_system.capture()
            if frame is None:
                return
            corrected = vision.vision_system.apply_corrections(frame)
            detections = vision.vision_system.detect_objects(corrected, color=color)
            display = vision.vision_system.draw_detections(corrected, detections)
            self._vision_show_frame(display)

        def _vision_show_frame(self, frame):
            """把 OpenCV BGR ndarray 顯示到 QLabel，並記錄原始尺寸供座標換算"""
            from PyQt5.QtGui import QImage, QPixmap
            import cv2
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            self._vision_frame_orig_size = (w, h)   # 記錄原始畫面尺寸
            qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg).scaled(
                self.vision_preview.width(),
                self.vision_preview.height(),
                1,   # KeepAspectRatio
                1    # SmoothTransformation
            )
            self.vision_preview.setPixmap(pix)


        # ── 色彩校正 ──

        def _vision_auto_wb(self):
            import vision
            frame = vision.vision_system.capture()
            if frame is None:
                self.vision_status.setText("Status: Capture failed.")
                return
            gains = vision.vision_system.compute_auto_wb(frame)
            self.vision_status.setText(f"Status: WB gains R={gains[0]:.3f} G={gains[1]:.3f} B={gains[2]:.3f}")
            self._vision_snapshot()

        def _vision_toggle_clahe(self, state):
            import vision
            vision.vision_system.calib.use_clahe = (state == 2)  # Qt.Checked == 2
            self.vision_status.setText(f"Status: CLAHE {'ON' if state == 2 else 'OFF'}")


        # ── 物件偵測 ──

        def _vision_detect_once(self):
            import vision
            color = self.cmb_color.currentText()
            frame = vision.vision_system.capture()
            if frame is None:
                self.vision_status.setText("Status: Capture failed.")
                return
            corrected = vision.vision_system.apply_corrections(frame)
            detections = vision.vision_system.detect_objects(corrected, color=color)
            display = vision.vision_system.draw_detections(corrected, detections)
            self._vision_show_frame(display)
            if detections:
                cx, cy = detections[0]["center"]
                self.vision_status.setText(
                    f"Status: Found {len(detections)} object(s). Best center=({cx},{cy})px, area={detections[0]['area']:.0f}"
                )
            else:
                self.vision_status.setText(f"Status: No {color} object detected.")

        # ── 透視校正 ──

        def _vision_set_perspective(self):
            """
            進入角點點選模式：凍結目前畫面，讓使用者依序點四個角點。
            點選順序：左上 → 右上 → 右下 → 左下
            """
            import vision
            # 凍結目前畫面
            frame = vision.vision_system.capture()
            if frame is None:
                self.vision_status.setText("Status: 請先確認攝影機正常")
                return
            corrected = vision.vision_system.apply_corrections(frame)
            self._vision_show_frame(corrected)
            # 暫停全域計時器避免畫面一直更新干擾點選
            self._global_cam_timer.stop()
            # 初始化角點收集狀態
            self._persp_pts = []          # 收集的原始畫面座標
            self._persp_frame = corrected # 保存畫面供繪製用
            # 安裝滑鼠事件到預覽 Label
            self.vision_preview.mousePressEvent = self._persp_mouse_click
            self.vision_status.setText(
                "Status: 請依序點選四個角點 (左上→右上→右下→左下)，已點 0/4"
            )

        def _persp_mouse_click(self, event):
            """預覽 Label 的滑鼠點擊事件，收集四個角點"""
            from PyQt5.QtCore import Qt
            from PyQt5.QtGui import QImage, QPixmap
            import cv2, vision

            if not hasattr(self, '_persp_pts'):
                return

            # 把 QLabel 上的像素座標換算回原始畫面座標
            label_w = self.vision_preview.width()
            label_h = self.vision_preview.height()
            orig_w, orig_h = getattr(self, '_vision_frame_orig_size', (640, 480))

            # scaled 使用 KeepAspectRatio，計算實際顯示區域
            scale = min(label_w / orig_w, label_h / orig_h)
            disp_w = int(orig_w * scale)
            disp_h = int(orig_h * scale)
            offset_x = (label_w - disp_w) // 2
            offset_y = (label_h - disp_h) // 2

            lx = event.x() - offset_x
            ly = event.y() - offset_y
            if lx < 0 or ly < 0 or lx > disp_w or ly > disp_h:
                return  # 點到黑邊，忽略

            # 換算回原始畫面座標
            ox = int(lx / scale)
            oy = int(ly / scale)
            self._persp_pts.append([ox, oy])

            # 在畫面上畫出已點的點
            preview = self._persp_frame.copy()
            labels = ["TL", "TR", "BR", "BL"]
            colors = [(0,255,0),(0,200,255),(255,100,0),(255,0,200)]
            for i, pt in enumerate(self._persp_pts):
                cv2.circle(preview, tuple(pt), 8, colors[i], -1)
                cv2.putText(preview, labels[i], (pt[0]+10, pt[1]-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors[i], 2)
            # 連線提示
            if len(self._persp_pts) > 1:
                for i in range(len(self._persp_pts)-1):
                    cv2.line(preview, tuple(self._persp_pts[i]),
                             tuple(self._persp_pts[i+1]), (255,255,0), 1)
            self._vision_show_frame(preview)

            n = len(self._persp_pts)
            if n < 4:
                next_labels = ["左上", "右上", "右下", "左下"]
                self.vision_status.setText(
                    f"Status: 已點 {n}/4，下一個點：{next_labels[n]}"
                )
            else:
                # 四點齊了，套用透視校正
                vision.vision_system.set_perspective_points(self._persp_pts)
                # 移除滑鼠事件
                self.vision_preview.mousePressEvent = None
                # 顯示校正後結果
                warped = vision.vision_system.apply_perspective(self._persp_frame)
                self._vision_show_frame(warped)
                self.vision_status.setText(
                    f"Status: 透視校正完成！角點={self._persp_pts}  按 Save Calibration 儲存"
                )
                del self._persp_pts
                # 恢復全域計時器
                self._global_cam_timer.start(200)


        # ── 視覺伺服 ──

        def _vision_start_servo(self):
            from PyQt5 import QtCore
            import vision, Motor

            if vision.servo_controller is None:
                self.vision_status.setText("Status: Servo controller not initialized.")
                return
            if vision.servo_controller.is_running:
                self.vision_status.setText("Status: Already running.")
                return

            color = self.cmb_color.currentText()
            vision.servo_controller.target_color = color

            # 注入狀態回呼：每次迭代更新 UI
            def on_status(msg, frame=None):
                self.vision_status.setText(f"Servo: {msg}")
                if frame is not None:
                    self._vision_show_frame(frame)

            vision.servo_controller.status_callback = on_status

            # 在背景執行緒跑，避免 UI 卡死
            class ServoThread(QtCore.QThread):
                done = QtCore.pyqtSignal(dict)
                def __init__(self, ctrl, color):
                    super().__init__()
                    self.ctrl = ctrl
                    self.color = color
                def run(self):
                    result = self.ctrl.run_once(self.color)
                    self.done.emit(result)

            self._servo_thread = ServoThread(vision.servo_controller, color)
            self._servo_thread.done.connect(self._on_servo_done)
            self._servo_thread.start()
            self.vision_status.setText(f"Status: Visual servo started (target={color})...")

        def _vision_stop_servo(self):
            import vision
            if vision.servo_controller:
                vision.servo_controller.stop()
            self.vision_status.setText("Status: Servo stopped by user.")

        def _on_servo_done(self, result: dict):
            ex, ey = result["final_error"]
            msg = (f"Servo done — success={result['success']}, "
                   f"iter={result['iterations']}, "
                   f"finalErr=({ex:.1f},{ey:.1f})px — {result['message']}")
            self.vision_status.setText(msg)


        # ── 儲存校正 ──

        def _vision_save_calib(self):
            import vision
            vision.vision_system.calib.save()
            self.vision_status.setText("Status: Calibration saved to database.")

        def _aruco_start(self):
            import vision
            from PyQt5 import QtCore
            if vision.aruco_calibrator is None:
                self.vision_status.setText("Status: ArUco calibrator not initialized.")
                return
            if vision.aruco_calibrator.is_running:
                self.vision_status.setText("Status: Already running.")
                return
            # 校準程式內部會自動移動手臂（點1:0度 → 點2:90度）

            def on_status(msg, frame=None):
                self.vision_status.setText(f"Calib: {msg}")
                if frame is not None:
                    self._vision_show_frame(frame)

            vision.aruco_calibrator.status_callback = on_status

            class CalibThread(QtCore.QThread):
                done = QtCore.pyqtSignal(dict)
                def __init__(self, calibrator):
                    super().__init__()
                    self.calibrator = calibrator
                def run(self):
                    result = self.calibrator.run()
                    self.done.emit(result)

            self._calib_thread = CalibThread(vision.aruco_calibrator)
            self._calib_thread.done.connect(self._aruco_done)
            self._calib_thread.start()
            self.vision_status.setText("Status: Auto calibration started...")

        def _aruco_stop(self):
            import vision
            if vision.aruco_calibrator:
                vision.aruco_calibrator.stop()
            self.vision_status.setText("Status: Calibration stopped.")

        def _aruco_done(self, result: dict):
            if result['success']:
                msg = f"Success: {result['message']}"
            else:
                msg = f"Failed: {result['message']}"
            self.vision_status.setText(msg)

        def show_page8(self):
            self.stacked_widget.setCurrentWidget(self.page8)
            self.vision_status.setText("Status: Vision Calibration page ready.")

    # --- UI 啟動程序 ---
    try:
        vision.init(Motor.arm)
        # 啟動時自動開攝影機
        vision.vision_system.open_camera()

        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"啟動失敗: {e}")
        sys.exit(1)


# ==========================================
# 程式入口點 (Entry Point)
# ==========================================

if __name__ == "__main__":
    run_ui()