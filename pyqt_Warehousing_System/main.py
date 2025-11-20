import sys
import os
import subprocess
import time

# ==========================================
# 系統管理功能 (安裝與移除)
# ==========================================

def run_command(command, ignore_errors=False):
    """執行 Shell 指令的輔助函式"""
    try:
        # 使用 subprocess 執行指令，並隱藏一般輸出，只顯示錯誤
        subprocess.check_call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        if not ignore_errors:
            print(f"[!] 執行失敗: {' '.join(command)}")
        return False

def install_system():
    """執行環境安裝 (原本的 setup.py)"""
    if os.geteuid() != 0:
        print("錯誤: 安裝模式需要 sudo 權限。\n請輸入: sudo python3 main.py --install")
        sys.exit(1)

    print("=== 開始環境檢查與安裝 ===")
    
    # 定義需要安裝的套件清單
    packages = [
        "python3-pyqt5", 
        "python3-smbus", 
        "i2c-tools", 
        "postgresql", 
        "postgresql-client", 
        "python3-psycopg2", 
        "python3-requests"
    ]
    
    for package in packages:
        try:
            # 檢查套件是否已安裝
            subprocess.check_call(["dpkg", "-l", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"[v] {package} 已安裝")
        except:
            print(f"[*] 正在安裝: {package} ...")
            subprocess.check_call(["sudo", "apt", "install", "-y", package])

    print("=== 檢查 PostgreSQL 服務 ===")
    try:
        subprocess.check_call(["sudo", "systemctl", "start", "postgresql"])
        subprocess.check_call(["sudo", "systemctl", "enable", "postgresql"])
        print("[v] PostgreSQL 服務已啟動")
    except Exception as e:
        print(f"[!] 無法啟動 PostgreSQL: {e}")

    print("\n=== 環境設定完成！ ===")
    print("請執行 'python3 main.py' 來啟動主程式。")

def uninstall_system():
    """執行解安裝 (原本的 uninstall.py)"""
    if os.geteuid() != 0:
        print("錯誤: 移除模式需要 sudo 權限。\n請輸入: sudo python3 main.py --uninstall")
        sys.exit(1)

    print("\n=== 解安裝程序 ===")
    
    # 1. 清除資料庫
    confirm_db = input("警告：確定要刪除 'armconfig' 資料庫與 'mct' 使用者嗎？(y/n): ")
    if confirm_db.lower() == 'y':
        print("[*] 正在清除資料庫...")
        # 強制切斷連線以允許刪除
        kill_sql = "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'armconfig';"
        subprocess.run(["sudo", "-u", "postgres", "psql", "-c", kill_sql], stderr=subprocess.DEVNULL)
        
        run_command(["sudo", "-u", "postgres", "psql", "-c", "DROP DATABASE IF EXISTS armconfig;"])
        run_command(["sudo", "-u", "postgres", "psql", "-c", "DROP USER IF EXISTS mct;"])
        print("[v] 資料庫已移除")
    else:
        print("略過資料庫清除。")
    
    # 2. 移除套件
    print("\n提示：建議保留系統套件 (PyQt5, PostgreSQL) 以免影響其他程式。")
    confirm_pkg = input("是否仍要強制移除系統套件？(y/n): ")
    if confirm_pkg.lower() == 'y':
        print("[*] 正在移除套件...")
        pkgs = ["python3-pyqt5", "python3-smbus", "postgresql", "python3-psycopg2", "python3-requests"]
        if run_command(["sudo", "apt", "remove", "-y"] + pkgs):
            run_command(["sudo", "apt", "autoremove", "-y"])
            print("[v] 套件已移除")
    else:
        print("略過套件移除。")

# ==========================================
# 主程式 UI 邏輯 (原本的 UI.py)
# ==========================================

def run_ui():
    """啟動圖形介面"""
    
    # --- 延遲匯入：確保只有在環境安裝好後才載入這些模組 ---
    try:
        from PyQt5 import QtWidgets, QtCore
        from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel
        from PyQt5.QtCore import QThread, pyqtSignal
        import copy
        from functools import partial
        
        # 匯入您的自定義模組
        import setsql
        import Motor
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
                                    Motor.arm.set_servo_angle(y, Position[y])
                                    current_pwm = Motor.arm.current_pwm
                                except AttributeError:
                                    # 相容舊版 Motor.py
                                    speed = Motor.MotorSpeed(value, 2)
                                    Position[y] -= speed
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

        def setup_ui_pages(self):
            self.page1 = self.create_page1()
            self.page2 = QtWidgets.QWidget()
            self.page2label = self.createTitle(" ", self.page2, 'font-size:48px;', 10, 0)
            self.createButton("Back", self.page2, (50, 500, 130, 50), self.show_page1)
            
            self.page3 = self.create_page3()
            self.page4 = self.create_page4_base()
            self.page5 = self.create_page5()
            self.page6 = self.create_page6()
            self.page7 = self.create_page7()

            pages = [self.page1, self.page2, self.page3, self.page4, self.page5, self.page6, self.page7]
            for page in pages:
                self.stacked_widget.addWidget(page)

        # --- UI 建構輔助函式 ---
        def create_page1(self):
            page = QtWidgets.QWidget()
            self.createTitle('Warehousing System Majorization', page, 'font-size:48px;', 10, 0)
            self.createButton("Place", page, (120, 280, 150, 150), lambda: self.show_page2("Place"))
            self.createButton("Pick", page, (570, 280, 150, 150), lambda: self.show_page2("Pick"))
            self.createButton("Teach", page, (350, 280, 150, 150), self.show_page4)
            self.createButton("Reset", page, (120, 470, 150, 50), Motor.Reset)
            self.createButton("Initial", page, (570, 470, 150, 50), self.show_page5)
            self.createButton("Exit", page, (350, 470, 150, 50), self.exit)
            return page

        def create_page3(self):
            page = QtWidgets.QWidget()
            self.page3label = self.createTitle(" ", page, 'font-size:48px;', 10, 0)
            self.done_button = self.createButton("Done", page, (350, 280, 150, 150), self.show_page1)
            self.done_button.hide()
            self.pause_resume_button = self.createButton("Stop", page, (350, 280, 150, 150), self.toggle_pause_resume)
            
            # 初始化 Label，數值稍後更新
            self.pwm0_label = self.createTitle("PWM0 : ", page, 'font-size:24px;', 50, 300)
            self.pwm1_label = self.createTitle("PWM1 : ", page, 'font-size:24px;', 50, 350)
            self.pwm2_label = self.createTitle("PWM2 : ", page, 'font-size:24px;', 50, 400)
            self.pwm3_label = self.createTitle("PWM3 : ", page, 'font-size:24px;', 50, 450)
            return page

        def create_page4_base(self):
            page = QtWidgets.QWidget()
            self.createTitle("Teaching Mod", page, 'font-size:48px;', 10, 0)
            self.createButton("Back", page, (50, 500, 130, 50), self.show_page1)
            self.createButton("Create", page, (190, 500, 130, 50), self.show_page7)
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
                y = 80 + i * 175
                label = self.createTitle(f"PWM{i}：{ranges[i]}", page, 'font-size:24px;', y, 250)
                self.labelrange.append(label)
                self.createButton("+", page, (y, 310, 150, 50), partial(self.set_PWM, i, 50))
                self.createButton("-", page, (y, 370, 150, 50), partial(self.set_PWM, i, -50))
                
            self.createButton("Cancel", page, (50, 500, 130, 50), self.page5cancel)
            self.createButton("Save", page, (190, 500, 130, 50), self.saveMotorData)
            return page

        def create_page6(self):
            page = QtWidgets.QWidget()
            self.box2_value = [1, 5, 10]
            self.learnlabel1 = self.createTitle("Learning：", page, 'font-size:48px;', 10, 0)
            self.createTitle("Data", page, 'font-size:24px;', 10, 80)
            
            self.box = QtWidgets.QComboBox(page)
            self.box.setStyleSheet('font-size:24px;')
            self.box.setGeometry(70, 70, 300, 50)
            self.createButton("Add", page, (380, 70, 130, 50), self.page6_add)
            self.createButton("Del", page, (520, 70, 130, 50), self.page6_del)
            
            self.createTitle("Step", page, 'font-size:24px;', 10, 160)
            self.box2 = QtWidgets.QComboBox(page)
            self.box2.addItems(list(map(str, self.box2_value)))
            self.box2.setStyleSheet('font-size:24px;')
            self.box2.setGeometry(70, 150, 60, 50)
            self.box2.currentIndexChanged.connect(self.change_box2)
            self.page6_set = self.box2_value[0]

            for i in range(4):
                y = 80 + i * 170
                label = self.createTitle(f"Angle{i}：", page, 'font-size:24px;', y, 250)
                self.labelangle.append(label)
                self.createButton("+", page, (y, 310, 150, 50), partial(self.set_angle, i, 1))
                self.createButton("-", page, (y, 370, 150, 50), partial(self.set_angle, i, -1))
                
            self.createButton("Cancel", page, (50, 500, 130, 50), self.show_page4)
            self.createButton("Save", page, (190, 500, 130, 50), self.page6_save)
            self.drop_button = self.createButton("Drop:", page, (650, 500, 150, 50), self.page6_drop)
            return page

        def create_page7(self):
            page = QtWidgets.QWidget()
            self.createTitle("Add new Warehouse", page, 'font-size:48px;', 10, 0)
            self.input = QtWidgets.QLineEdit(page)
            self.input.setGeometry(325, 250, 200, 50)
            self.input.setMaxLength(20)
            self.createButton("Cancel", page, (50, 500, 130, 50), self.show_page4)
            self.createButton("Add", page, (190, 500, 130, 50), self.page7_add)
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

        def exit(self):
            setsql.state_update(100)
            Motor.stopAllPWM()
            sys.exit("Exit")

        def show_page2(self, text):
            setsql.state_update(300)
            self.Data[0] = text
            self.page2label.setText(f"{self.Data[0]}")
            self.page2label.adjustSize()
            
            for btn in self.page2Button: btn.deleteLater()
            self.page2Button.clear()
            
            SetButton2 = [50, 150]
            self.KeyList = list(setsql.take_names())
            items = self.KeyList[2:] if len(self.KeyList) > 2 else []
            
            for key in items:
                if SetButton2[0] >= 800:
                    SetButton2[1] += 60
                    SetButton2[0] = 50
                btn = self.createButton(key, self.page2, (SetButton2[0], SetButton2[1], 130, 50), partial(self.show_page3, key))
                self.page2Button.append(btn)
                SetButton2[0] += 140
            
            self.stacked_widget.setCurrentWidget(self.page2)

        def show_page3(self, text):
            self.Data[1] = text
            self.page3label.setText(f"{self.Data[0]} to {self.Data[1]}")
            self.page3label.adjustSize()
            self.stacked_widget.setCurrentWidget(self.page3)
            self.done_button.hide()
            self.pause_resume_button.show()
            self.pause_resume_button.setText("Stop")
            self.is_paused = False

            journey = Motor.Warehouses(self.Data)
            self.worker = RunMotorWorker(journey)
            self.worker.pwmvalue_updated.connect(self.update_pwm_label)
            self.worker.finished.connect(self.on_worker_finished)
            self.worker.start()

        def toggle_pause_resume(self):
            if self.is_paused:
                setsql.state_update(300)
                self.worker.resume()
                self.pause_resume_button.setText("Stop")
                self.is_paused = False
            else:
                setsql.state_update(301)
                self.worker.pause()
                self.pause_resume_button.setText("Keep")
                self.is_paused = True

        def update_pwm_label(self, pwm_values):
            if self.stacked_widget.currentWidget() == self.page3:
                # 為了顯示角度，嘗試從 Motor 獲取
                try:
                    angles = Motor.arm.current_angles
                except AttributeError:
                    angles = Motor.anglevalue
                    
                self.pwm0_label.setText(f"PWM0 : {pwm_values[0]} , {angles[0]}")
                self.pwm1_label.setText(f"PWM1 : {pwm_values[1]} , {angles[1]}")
                self.pwm2_label.setText(f"PWM2 : {pwm_values[2]} , {angles[2]}")
                self.pwm3_label.setText(f"PWM3 : {pwm_values[3]} , {angles[3]}")
                self.pwm0_label.adjustSize()
                self.pwm1_label.adjustSize()
                self.pwm2_label.adjustSize()
                self.pwm3_label.adjustSize()

        def on_worker_finished(self):
            self.done_button.show()
            self.pause_resume_button.hide()

        def show_page4(self):
            setsql.state_update(201)
            for btn in self.learn_button: btn.deleteLater()
            self.learn_button.clear()
            
            self.KeyList = list(setsql.take_names())
            SetButton2 = [50, 150]
            items = self.KeyList[1:] if len(self.KeyList) > 1 else []

            for key in items:
                if SetButton2[0] >= 800:
                    SetButton2[1] += 60
                    SetButton2[0] = 50
                btn = self.createButton(key, self.page4, (SetButton2[0], SetButton2[1], 130, 50), partial(self.show_page6, key))
                self.learn_button.append(btn)
                SetButton2[0] += 140
            
            self.stacked_widget.setCurrentWidget(self.page4)

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

        def show_page6(self, name):
            self.page6_update_value = 0
            self.learn_name = name
            self.learn_data = setsql.read_sql(self.learn_name)
            self.learnlabel1.setText(f"Learning：{self.learn_name}")
            self.learnlabel1.adjustSize()
            
            if len(self.KeyList) > 1 and name == self.KeyList[1]:
                self.drop_button.hide()
            else:
                self.drop_button.show()
                self.drop_button.setText(f"Drop:{name}")
                
            self.update_learn_data()
            self.on_selection_changed(0)
            self.stacked_widget.setCurrentWidget(self.page6)

        def update_learn_data(self, preserve_selection=False):
            current = self.box.currentIndex() if preserve_selection else self.page6_update_value
            try: self.box.currentIndexChanged.disconnect(self.on_selection_changed)
            except: pass
            self.box.clear()
            
            result = [f"{i+1}： {', '.join(map(str, row))}" for i, row in enumerate(self.learn_data)]
            self.box.addItems(result)
            
            if current >= self.box.count(): current = self.box.count() - 1
            if current < 0: current = 0
            self.box.setCurrentIndex(current)
            self.box.currentIndexChanged.connect(self.on_selection_changed)

        def on_selection_changed(self, value):
            self.page6_update_value = value
            if 0 <= value < len(self.learn_data):
                for i in range(4):
                    self.labelangle[i].setText(f"Angle{i}：{self.learn_data[value][i]}")
                    self.labelangle[i].adjustSize()

        def set_angle(self, value, setangle):
            if not (0 <= self.page6_update_value < len(self.learn_data)): return
            self.learn_data[self.page6_update_value][value] += (setangle * self.page6_set)
            self.update_learn_data(preserve_selection=True)
            for i in range(4):
                self.labelangle[i].setText(f"Angle{i}：{self.learn_data[self.page6_update_value][i]}")
                self.labelangle[i].adjustSize()
            Motor.to_new_angle(self.learn_data[self.page6_update_value])

        def page6_save(self):
            setsql.write_sql(self.learn_name, self.learn_data)

        def page6_add(self):
            val = copy.deepcopy(self.learn_data[self.page6_update_value]) if self.learn_data else [0,0,0,0]
            self.learn_data.insert(self.page6_update_value + 1, val)
            self.page6_update_value += 1
            self.update_learn_data()
            self.on_selection_changed(self.page6_update_value)

        def page6_del(self):
            if not self.learn_data: return
            self.learn_data.pop(self.page6_update_value)
            if self.page6_update_value >= len(self.learn_data):
                self.page6_update_value = max(0, len(self.learn_data) - 1)
            self.update_learn_data()
            self.on_selection_changed(self.page6_update_value)
        
        def page6_drop(self):
            setsql.drop_table(self.learn_name)
            self.show_page4() # 回到上一頁會自動刷新按鈕
        
        def change_box2(self):
            self.page6_set = self.box2_value[self.box2.currentIndex()]

        def show_page7(self):
            self.input.clear()
            self.stacked_widget.setCurrentWidget(self.page7)

        def page7_add(self):
            name = self.input.text()
            if name:
                setsql.add_table(name)
                self.show_page4()

    # --- UI 啟動程序 ---
    print("Checking Database Integrity...")
    try:
        # 初始化檢查移到這裡，確保在環境具備時才執行
        setsql.check_user_exists()
        setsql.check_database()
        setsql.check_table()
        print("System Ready.")
        
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
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--install":
            install_system()
        elif arg == "--uninstall":
            uninstall_system()
        else:
            print(f"未知參數: {arg}")
            print("用法:")
            print("  python3 main.py              (啟動主程式)")
            print("  sudo python3 main.py --install   (安裝環境)")
            print("  sudo python3 main.py --uninstall (移除環境)")
    else:
        # 沒有參數時，預設執行 UI
        run_ui()