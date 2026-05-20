import time
import math
import smbus2
import setsql

class PCA9685:
    """
    PCA9685 I2C PWM 驅動晶片控制類別 (硬體底層)
    """
    __MODE1 = 0x00
    __PRESCALE = 0xFE
    __LED0_ON_L = 0x06
    __LED0_ON_H = 0x07
    __LED0_OFF_L = 0x08
    __LED0_OFF_H = 0x09

    def __init__(self, address=0x40, debug=False):
        self.bus = smbus2.SMBus(1)
        self.address = address
        self.debug = debug
        try:
            self.write(self.__MODE1, 0x00)
        except Exception as e:
            print(f"Error initializing PCA9685: {e}")

    def write(self, reg, value):
        try:
            self.bus.write_byte_data(self.address, reg, value)
        except Exception as e:
            print(f"I2C Write Error: {e}")

    def read(self, reg):
        try:
            return self.bus.read_byte_data(self.address, reg)
        except Exception as e:
            print(f"I2C Read Error: {e}")
            return 0

    def setPWMFreq(self, freq):
        prescaleval = (6103.5 / float(freq)) - 1
        prescale = math.floor(prescaleval + 0.5)

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        self.write(self.__MODE1, newmode)
        self.write(self.__PRESCALE, int(prescale))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def setPWM(self, channel, on, off):
        self.write(self.__LED0_ON_L + 4 * channel, on & 0xFF)
        self.write(self.__LED0_ON_H + 4 * channel, on >> 8)
        self.write(self.__LED0_OFF_L + 4 * channel, off & 0xFF)
        self.write(self.__LED0_OFF_H + 4 * channel, off >> 8)

    def stop_channel(self, channel):
        self.write(self.__LED0_OFF_H + 4 * channel, 0x10)

class RobotArm:
    """
    機械手臂控制類別 (高階邏輯)
    """
    def __init__(self):
        self.pwm_driver = PCA9685(0x40)
        self.pwm_driver.setPWMFreq(50)
        
        # 讀取資料庫中的校正參數
        self.motor_ranges = setsql.take_range()
        
        # 初始狀態定義
        self.initial_pos = [0, 0, 0, 90]
        
        # 當前狀態 (State)
        self.current_pwm = [0, 0, 0, 0]
        self.current_angles = [0, 0, 0, 90] # 預設起始角度

    def set_servo_angle(self, channel, angle):
        """
        設定指定伺服馬達的角度，並自動轉換為 PWM 訊號發送
        """
        # 更新狀態
        self.current_angles[channel] = int(round(angle))
        
        # 計算 PWM 值 (沿用原本的公式：Base + 11 * angle)
        raw_val = self.motor_ranges[channel] + 11 * self.current_angles[channel]
        self.current_pwm[channel] = int(raw_val)
        
        # 發送至硬體 (沿用公式：val * 0.2048)
        duty_cycle = int(self.current_pwm[channel] * 0.2048)
        self.pwm_driver.setPWM(channel, 0, duty_cycle)

    def set_initial_ranges(self, new_ranges):
        """用於校正模式，更新並測試新的 Range"""
        self.motor_ranges = new_ranges
        # 測試：將目前角度重新應用一次，看新 Range 的效果
        for i in range(4):
            # 為了避免馬達暴衝，這裡通常設為 0 或維持原角度，這裡維持 0
            self.pwm_driver.setPWM(i, 0, int(new_ranges[i] * 0.2048))

    def reset(self):
        """回到初始位置"""
        for i in range(4):
            self.set_servo_angle(i, self.initial_pos[i])

    def stop_all(self):
        """緊急停止/程式結束用"""
        for i in range(16):
            self.pwm_driver.stop_channel(i)

    def get_path_plan(self, data):
        """
        路徑規劃 (原 Warehouses)
        Data: ["Pick" or "Place", "TargetName"]
        """
        target_name = data[1]
        mode = data[0]
        
        counters = setsql.read_sql(target_name)
        prepare = setsql.read_sql("prepare")
        
        # 先確保 Reset
        self.reset()
        
        action = prepare + counters
        if mode == "Pick":
            action = action[::-1] # 反轉路徑
            
        return action

    @staticmethod
    def calculate_step_speed(diff, max_speed=2):
        """
        計算每一步的移動速度 (原 MotorSpeed)
        """
        if abs(diff) <= 5:
            return -1 if diff > 0 else 1
        else:
            return -max_speed if diff > 0 else max_speed

    def to_new_angle_direct(self, target_angles, max_speed=2):
        """
        直線軌跡移動：所有通道同時出發、同時到達。
        以距離最大的通道為基準，其他通道按比例分配每步移動量。
        """
        current = [float(a) for a in self.current_angles]
        target  = [float(a) for a in target_angles]
        diffs   = [target[i] - current[i] for i in range(4)]
        max_diff = max(abs(d) for d in diffs)

        if max_diff == 0:
            return

        # 每個通道的單步移動量（按比例，最大通道每步 max_speed）
        steps = [max_speed * d / max_diff for d in diffs]

        while True:
            remaining = [target[i] - current[i] for i in range(4)]
            if all(abs(r) < 0.5 for r in remaining):
                break

            moved = False
            for i in range(4):
                if abs(remaining[i]) < 0.5:
                    continue
                # 不超過目標
                move = steps[i]
                if abs(move) > abs(remaining[i]):
                    move = remaining[i]
                current[i] += move
                self.set_servo_angle(i, current[i])
                moved = True

            if not moved:
                break

            time.sleep(0.02)

        # 確保精確到達目標
        for i in range(4):
            self.set_servo_angle(i, target[i])

    def visual_servo_step(self, delta_angle_ch0: float, delta_angle_ch1: float,
                          max_step: float = 5.0):
        """
        視覺閉迴路補正步驟：
        根據 vision.py 計算出的角度誤差，微調 channel 0 (底座旋轉) 和
        channel 1 (手臂高低)。
        delta_angle_chX: 正值→正方向移動，負值→反方向
        max_step: 單次最大移動角度 (防止暴衝)
        """
        adjustments = [
            (0, delta_angle_ch0),
            (1, delta_angle_ch1),
        ]
        for ch, delta in adjustments:
            if abs(delta) < 0.5:   # 太小的誤差忽略
                continue
            clamped = max(-max_step, min(max_step, delta))
            new_angle = self.current_angles[ch] + clamped
            new_angle = max(-90.0, min(180.0, new_angle))
            self.set_servo_angle(ch, new_angle)


# --- 初始化實體 ---
# 為了相容 UI.py 的呼叫方式，我們建立一個全域實體
arm = RobotArm()

# --- 為了相容 UI.py 的舊變數名稱 (Compatibility Layer) ---
# UI.py 裡直接呼叫了 Motor.initial, Motor.pwmvalue 等
# 我們透過這層對應，讓 UI 不用大改也能運作
# 但建議之後修改 UI 使用 arm.current_pwm
initial = arm.initial_pos
pwmvalue = arm.current_pwm
anglevalue = arm.current_angles
MotorRange = arm.motor_ranges
pwm = arm.pwm_driver  # 讓 UI 可以呼叫 Motor.pwm.ServoAngle (如果不改 UI 的話)

# 重新定義函式以符合 UI 呼叫習慣
def Reset():
    arm.reset()

def stopAllPWM():
    arm.stop_all()

def MotorSpeed(value, max_speed):
    return arm.calculate_step_speed(value, max_speed)

def Warehouses(Data):
    return arm.get_path_plan(Data)

def setinitial(value):
    arm.set_initial_ranges(value)

def to_new_angle(journey):
    arm.to_new_angle_direct(journey)

# 這是個小修補：讓 UI 呼叫 Motor.pwm.ServoAngle 時能導向到我們的 arm 物件
# 但因為 pwm.ServoAngle 是原本 PCA9685 的方法，現在我們希望統一走 RobotArm
# 這裡動個手腳：
def _servo_angle_wrapper(channel, angle):
    arm.set_servo_angle(channel, angle)
# 將這個 wrapper 綁定到 pwm 物件上，騙過 UI
pwm.ServoAngle = _servo_angle_wrapper