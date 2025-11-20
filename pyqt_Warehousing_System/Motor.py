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
        self.current_angles[channel] = angle
        
        # 計算 PWM 值 (沿用原本的公式：Base + 11 * angle)
        raw_val = self.motor_ranges[channel] + 11 * angle
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
            return -0.1 if diff > 0 else 0.1
        else:
            return -max_speed if diff > 0 else max_speed

    def to_new_angle_direct(self, target_angles):
        """
        直接移動到指定角度 (無平滑過渡，用於 Page 6 校正)
        """
        # 計算差值並移動，這裡保留原本的微步移動邏輯會比較順
        # 但為了校正方便，通常 Page 6 是直接設定到位
        pass 
        # 注意：原程式 UI 的 Page 6 用 worker 嗎？
        # Page 6 原程式是用 to_new_angle (有 sleep)
        # 建議改為由 UI 迴圈控制，或是這裡簡單實作一個帶 sleep 的 (僅供測試用)
        
        current = self.current_angles[:]
        diffs = [t - c for t, c in zip(target_angles, current)]
        
        while any(d != 0 for d in diffs):
            for i in range(4):
                if diffs[i] != 0:
                    step = self.calculate_step_speed(diffs[i])
                    current[i] -= step
                    diffs[i] -= step
                    self.set_servo_angle(i, current[i])
            time.sleep(0.02)


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