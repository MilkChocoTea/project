import time
import math
import smbus2
import setsql
from PyQt5.QtCore import pyqtSignal, QObject

class MotorSignals(QObject):
    pwmvalue_changed = pyqtSignal(list)
signals = MotorSignals()
class PCA9685:
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
        if self.debug:
            print("Reseting PCA9685")
        self.write(self.__MODE1, 0x00)

    def write(self, reg, value):
        self.bus.write_byte_data(self.address, reg, value)
        if self.debug:
            print(f"I2C: Write 0x{value:02X} to register 0x{reg:02X}")

    def read(self, reg):
        result = self.bus.read_byte_data(self.address, reg)
        if self.debug:
            print(f"I2C: Device 0x{self.address:02X} returned 0x{result & 0xFF:02X} from reg 0x{reg:02X}")
        return result

    def setPWMFreq(self, freq):
        prescaleval = (6103.5 / float(freq)) - 1
        if self.debug:
            print(f"Setting PWM frequency to {freq} Hz")
            print(f"Estimated pre-scale: {prescaleval}")
        prescale = math.floor(prescaleval + 0.5)
        if self.debug:
            print(f"Final pre-scale: {prescale}")

        oldmode = self.read(self.__MODE1)
        newmode = (oldmode & 0x7F) | 0x10
        self.write(self.__MODE1, newmode)
        self.write(self.__PRESCALE, int(prescale))
        self.write(self.__MODE1, oldmode)
        time.sleep(0.005)
        self.write(self.__MODE1, oldmode | 0x80)

    def stopPWM(self, channel):
        self.write(self.__LED0_OFF_H + 4 * channel, 0x10)
        if self.debug:
            print(f"Stopped PWM output on channel {channel}")

    def setPWM(self, channel, on, off):
        self.write(self.__LED0_ON_L + 4 * channel, on & 0xFF)
        self.write(self.__LED0_ON_H + 4 * channel, on >> 8)
        self.write(self.__LED0_OFF_L + 4 * channel, off & 0xFF)
        self.write(self.__LED0_OFF_H + 4 * channel, off >> 8)
        if self.debug:
            print(f"channel: {channel}  LED_ON: {on} LED_OFF: {off}")

    def ServoAngle(self, channel, angle):
        global pwmvalue,anglevalue
        anglevalue[channel] = angle
        pwmvalue[channel] = int(MotorRange[channel] + 11 * angle)
        self.setPWM(channel, 0, int(pwmvalue[channel] * 0.2048))

pwm = PCA9685(0x40, debug=False)
pwm.setPWMFreq(50)
MotorRange = setsql.take_range()
initial = [0,0,0,90]
pwmvalue = [0,0,0,0]
anglevalue = [0,0,0,90]

def test():
    test = [25, 10, 0, 20]
    for i in range(4):
        pwm.ServoAngle(i, test[i])
        
def MotorSpeed(value,max_speed):
    if abs(value) <= 5:
        return -0.5 if value > 0 else 0.5
    else:
        return -max_speed if value > 0 else max_speed

def Warehouses(Data):
    global counters
    counters = setsql.read_sql(Data[1])
    prepare = setsql.read_sql("prepare")
    Reset()
    action = prepare + counters
    if Data[0] == "Pick":
        action = action[::-1]
    return action

def setinitial(value):
    for i in range(4):
        pwm.setPWM(i, 0, int(value[i] * 0.2048))

def Reset():
    for i in range(4):
        pwm.ServoAngle(i, initial[i])

def to_new_angle(Journey):
    Position = anglevalue
    values = [a - b for a, b in zip(Position, Journey)]
    while values != [0,0,0,0]:
        for i in range(4):
            if values[i] != 0:
                Position[i] -= to_new_speed(values[i])
                values[i] -= to_new_speed(values[i])
                pwm.ServoAngle(i, Position[i])
        time.sleep(0.02)
    return

def to_new_speed(value):
    return 0.5 if value > 0 else -0.5

def stopAllPWM():
    for channel in range(16):
        pwm.stopPWM(channel)
    if pwm.debug:
        print("Stopped PWM output on all channels")