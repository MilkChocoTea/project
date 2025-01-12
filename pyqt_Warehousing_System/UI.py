import subprocess
import sys

def is_package_installed(package_name):
    try:
        subprocess.check_call(["dpkg", "-l", package_name], stdout=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def install_system():
    print("Check and Install System Packages...")
    packages = ["python3-pyqt5", "python3-smbus", "i2c-tools","postgresql", "postgresql-client", "python3-psycopg2"]
    for package in packages:
        if is_package_installed(package) == False:
            try:
                print(f"Installing '{package}'...")
                subprocess.check_call(["sudo", "apt", "install", "-y", package])
            except Exception as e:
                sys.exit(f"An error occurred while installing '{package}'：{e}")
    print("Starting PostgreSQL service...")
    try:
        subprocess.check_call(["sudo", "systemctl", "start", "postgresql"])
    except Exception as e:
        sys.exit(f"Failed to start PostgreSQL：{e}")
install_system()

import setsql
setsql.check_user_exists()
setsql.check_database()
setsql.check_table()

from functools import partial
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget, QLabel
from PyQt5.QtCore import QThread, pyqtSignal
import time
import Motor
import copy

class RunMotorWorker(QThread):
    pwmvalue_updated = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, journey):
        super().__init__()
        self.journey = journey
        self.running = True
        self.paused = False

    def run(self):
        Position = Motor.initial.copy()
        for JourneyNode in self.journey:
            while JourneyNode != Position:
                while self.paused:
                    time.sleep(0.1)
                if not self.running:
                    return
                for y, pos in enumerate(JourneyNode):
                    if pos != Position[y]:
                        value = pos - Position[y]
                        if value != 0:
                            Position[y] -= Motor.MotorSpeed(value,2)
                            Motor.pwm.ServoAngle(y, Position[y])
                            self.pwmvalue_updated.emit(Motor.pwmvalue)
                time.sleep(0.02)
        self.finished.emit()

    def stop(self):
        self.running = False

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Robotic Arm')
        self.resize(850, 600)
        self.Data = ["", ""]
        self.labelrange = []
        self.pwmlabel = []
        self.learn_name = ""
        self.learn_data = []
        self.page2Button = []
        self.learn_button = []
        self.is_paused = False
        self.stacked_widget = QStackedWidget()

        self.page1 = QtWidgets.QWidget()
        SetButton1 = {"Place": [120, 280], "Pick": [570, 280], "Teach" : [350, 280], "Reset" : [120, 470], "Initial" : [570, 470],"Exit" : [350, 470]}
        keys = list(SetButton1.keys())
        self.createTitle('Warehousing System Majorization',self.page1,'font-size:48px;',10,0)
        self.createButton(keys[0], self.page1, (SetButton1[keys[0]][0], SetButton1[keys[0]][1], 150, 150), lambda: self.show_page2(keys[0]))
        self.createButton(keys[1], self.page1, (SetButton1[keys[1]][0], SetButton1[keys[1]][1], 150, 150), lambda: self.show_page2(keys[1]))
        self.createButton(keys[2], self.page1, (SetButton1[keys[2]][0], SetButton1[keys[2]][1], 150, 150), self.show_page4)
        self.createButton(keys[3], self.page1, (SetButton1[keys[3]][0], SetButton1[keys[3]][1], 150, 50), Motor.Reset)
        self.createButton(keys[4], self.page1, (SetButton1[keys[4]][0], SetButton1[keys[4]][1], 150, 50), self.show_page5)
        self.createButton(keys[5], self.page1, (SetButton1[keys[5]][0], SetButton1[keys[5]][1], 150, 50), self.exit)

        self.page2 = QtWidgets.QWidget()
        self.page2label = self.createTitle(" ",self.page2,'font-size:48px;',10,0)
        self.createButton("Back", self.page2, (50, 500, 130, 50), self.show_page1)

        self.page3 = QtWidgets.QWidget()
        self.page3label = self.createTitle(" ",self.page3,'font-size:48px;',10,0)
        self.done_button = self.createButton("Done", self.page3, (350, 280, 150, 150), self.show_page1)
        self.done_button.hide()
        self.pause_resume_button = self.createButton("Stop", self.page3, (350, 280, 150, 150), self.toggle_pause_resume)
        self.pwm0_label = self.createTitle(f"PWM0 : {Motor.pwmvalue[0]} , {Motor.anglevalue[0]}", self.page3,'font-size:24px;',50,300)
        self.pwm1_label = self.createTitle(f"PWM1 : {Motor.pwmvalue[1]} , {Motor.anglevalue[1]}", self.page3,'font-size:24px;',50,350)
        self.pwm2_label = self.createTitle(f"PWM2 : {Motor.pwmvalue[2]} , {Motor.anglevalue[2]}", self.page3,'font-size:24px;',50,400)
        self.pwm3_label = self.createTitle(f"PWM3 : {Motor.pwmvalue[3]} , {Motor.anglevalue[3]}", self.page3,'font-size:24px;',50,450)

        self.page4 = QtWidgets.QWidget()
        self.createTitle("Teaching Mod",self.page4,'font-size:48px;',10,0)
        self.createButton("Back", self.page4, (50, 500, 130, 50), self.show_page1)
        self.createButton("Create", self.page4, (190, 500, 130, 50), self.show_page7)

        self.page5 = QtWidgets.QWidget()
        self.createTitle("Set Initial",self.page5,'font-size:48px;',10,0)
        self.labelminrange = self.createTitle(f"Initial PWM：{Motor.MotorRange}",self.page5,'font-size:30px;',10,110)
        self.createTitle("+50",self.page5,'font-size:24px;',30,310)
        self.createTitle("-50",self.page5,'font-size:24px;',30,370)
        for i in range(4):
            y = 80 + i * 175
            label = self.createTitle(f"PWM{i}：{Motor.MotorRange[i]}",self.page5,'font-size:24px;',y,250)
            self.labelrange.append(label)
            self.createButton("+", self.page5, (y, 310, 150, 50), partial(self.set_PWM,i,50))
            self.createButton("-", self.page5, (y, 370, 150, 50), partial(self.set_PWM,i,-50))
        self.createButton("Cancel", self.page5, (50, 500, 130, 50), self.page5cancel)
        self.createButton("Save", self.page5, (190, 500, 130, 50), self.saveMotorData)

        self.page6 = QtWidgets.QWidget()
        self.box2_value = [1, 5, 10]
        self.labelangle = []
        self.learnlabel1 = self.createTitle("Learning：",self.page6,'font-size:48px;',10,0)
        self.learnlabel2 = self.createTitle("Data",self.page6,'font-size:24px;',10,80)
        self.box = QtWidgets.QComboBox(self.page6)
        self.box.setStyleSheet('font-size:24px;')
        self.box.setGeometry(70, 70, 300, 50)
        self.createButton("Add", self.page6, (380, 70, 130, 50), self.page6_add)
        self.createButton("Del", self.page6, (520, 70, 130, 50), self.page6_del)
        self.createTitle("Step",self.page6,'font-size:24px;',10,160)
        self.box2 = QtWidgets.QComboBox(self.page6)
        self.box2.addItems(list(map(str, self.box2_value)))
        self.box2.setStyleSheet('font-size:24px;')
        self.box2.setGeometry(70, 150, 60, 50)
        self.box2.currentIndexChanged.connect(self.change_box2)
        for i in range(4):
            y = 80 + i * 170
            label = self.createTitle(f"Angle{i}：",self.page6,'font-size:24px;',y,250)
            self.labelangle.append(label)
            self.createButton("+", self.page6, (y, 310, 150, 50), partial(self.set_angle,i,1))
            self.createButton("-", self.page6, (y, 370, 150, 50), partial(self.set_angle,i,-1))
        self.createButton("Cancel", self.page6, (50, 500, 130, 50), self.show_page4)
        self.createButton("Save", self.page6, (190, 500, 130, 50), self.page6_save)
        self.drop_button = self.createButton("Drop:", self.page6, (650, 500, 150, 50), self.page6_drop)

        self.page7 = QtWidgets.QWidget()
        self.createTitle("Add new Warehouse",self.page7,'font-size:48px;',10,0)
        self.input = QtWidgets.QLineEdit(self.page7)
        self.input.setGeometry(325,250,200,50)
        self.input.setMaxLength(20)
        self.createButton("Cancel", self.page7, (50, 500, 130, 50), self.show_page4)
        self.createButton("Add", self.page7, (190, 500, 130, 50), self.page7_add)

        pages = [self.page1, self.page2, self.page3, self.page4, self.page5, self.page6, self.page7]
        for page in pages:
            self.stacked_widget.addWidget(page)
        self.setCentralWidget(self.stacked_widget)
        self.worker = None

    def show_page1(self):
        self.Data = ["", ""]
        self.stacked_widget.setCurrentWidget(self.page1)
    
    def createTitle(self,text,parent,size,seat1,seat2):
        label = QtWidgets.QLabel(text, parent)
        label.setStyleSheet(size)
        label.move(seat1,seat2)
        label.adjustSize()
        return label

    def createButton(self, text, parent, geometry, onClick):
        Button = QtWidgets.QPushButton(text, parent)
        Button.setStyleSheet('font-size:30px;')
        Button.setGeometry(*geometry)
        Button.clicked.connect(onClick)
        return Button

    def exit(self):
        Motor.stopAllPWM()
        sys.exit("Exit")

    def show_page2(self, text):
        self.Data[0] = text
        self.page2label.setText(f"{self.Data[0]}")
        self.page2label.adjustSize()
        self.createPage2Button()
        self.stacked_widget.setCurrentWidget(self.page2)

    def createPage2Button(self):
        SetButton2 = [50, 150]
        self.KeyList = list(setsql.take_names())
        for key in self.KeyList[2:]:
            if SetButton2[0] >= 800:
                SetButton2[1] += 60
                SetButton2[0] = 50
            button = self.createButton(key, self.page2, (SetButton2[0], SetButton2[1], 130, 50), partial(self.show_page3, key))
            self.page2Button.append(button)
            SetButton2[0] += 140

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
            self.worker.resume()
            self.pause_resume_button.setText("Stop")
            self.is_paused = False
        else:
            self.worker.pause()
            self.pause_resume_button.setText("Keep")
            self.is_paused = True
    
    def update_pwm_label(self, pwm_values):
        if self.stacked_widget.currentWidget() == self.page3:
            self.pwm0_label.setText(f"PWM0 : {pwm_values[0]} , {Motor.anglevalue[0]}")
            self.pwm1_label.setText(f"PWM1 : {pwm_values[1]} , {Motor.anglevalue[1]}")
            self.pwm2_label.setText(f"PWM2 : {pwm_values[2]} , {Motor.anglevalue[2]}")
            self.pwm3_label.setText(f"PWM3 : {pwm_values[3]} , {Motor.anglevalue[3]}")
            self.pwm0_label.adjustSize()
            self.pwm1_label.adjustSize()
            self.pwm2_label.adjustSize()
            self.pwm3_label.adjustSize()

    def on_worker_finished(self):
        self.done_button.show()
        self.pause_resume_button.hide()

    def show_page4(self):
        self.createPage4Button()
        self.stacked_widget.setCurrentWidget(self.page4)

    def createPage4Button(self):
        self.KeyList = list(setsql.take_names())
        SetButton2 = [50, 150]
        for key in self.KeyList[1:]:
            if SetButton2[0] >= 800:
                SetButton2[1] += 60
                SetButton2[0] = 50
            button = self.createButton(key, self.page4, (SetButton2[0], SetButton2[1], 130, 50), partial(self.show_page6, key))
            self.learn_button.append(button)
            SetButton2[0] += 140

    def show_page5(self):
        self.page5cancel()
        self.stacked_widget.setCurrentWidget(self.page5)

    def set_PWM(self,value,setpwm):
        self.Range[value] += setpwm
        Motor.setinitial(self.Range)
        self.set_PWMvalue(value)

    def set_PWMvalue(self,value):
        self.labelrange[value].setText(f"PWM{value}：{self.Range[value]}")

    def saveMotorData(self):
        setsql.write_sql('MotorRange',[self.Range])
        Motor.MotorRange = setsql.take_range()
        self.labelminrange.setText(f"Initial PWM：{Motor.MotorRange}")
        Motor.Reset()

    def page5cancel(self):
        Motor.Reset()
        self.Range = setsql.take_range()
        for i in range(4):
            self.set_PWMvalue(i)
        self.show_page1()

    def show_page6(self,name):
        self.page6_update_value = 0
        self.learn_name = name
        self.learn_data = setsql.read_sql(self.learn_name)
        self.learnlabel1.setText(f"Learning：{self.learn_name}")
        self.learnlabel1.adjustSize()
        if name == self.KeyList[1]:
            self.drop_button.hide()
        else:
            self.drop_button.show()
            self.drop_button.setText(f"Drop:{name}")
        self.update_learn_data()
        self.on_selection_changed(0)
        self.stacked_widget.setCurrentWidget(self.page6)

    def update_learn_data(self,preserve_selection=False):
        current_index = self.box.currentIndex() if preserve_selection else self.page6_update_value
        self.clean_update_learn_data()
        result = [f"{i+1}： {', '.join(map(str, row))}" for i, row in enumerate(self.learn_data)]
        self.box.addItems(result)
        self.box.setCurrentIndex(current_index)
        self.box.currentIndexChanged.connect(self.on_selection_changed)
        return

    def clean_update_learn_data(self):
        try:
            self.box.currentIndexChanged.disconnect(self.on_selection_changed)
        except TypeError:
            pass
        self.box.clear()

    def on_selection_changed(self, value):
        self.page6_update_value = value
        for i in range(4):
            self.labelangle[i].setText(f"Angle{i}：{self.learn_data[value][i]}")
            self.labelangle[i].adjustSize()

    def set_angle(self,value,setangle):
        if not (0 <= self.page6_update_value < len(self.learn_data)):
            return
        self.learn_data[self.page6_update_value][value] += (setangle * self.page6_set)
        self.update_learn_data(preserve_selection=True)
        for i in range(4):
            self.labelangle[i].setText(f"Angle{i}：{self.learn_data[self.page6_update_value][i]}")
            self.labelangle[i].adjustSize()
        Motor.to_new_angle(self.learn_data[self.page6_update_value])
        return

    def page6_save(self):
        setsql.write_sql(self.learn_name,self.learn_data)

    def page6_add(self):
        value = copy.deepcopy(self.learn_data[self.page6_update_value])
        self.learn_data.insert(self.page6_update_value,value)
        self.page6_update_value += 1
        self.update_learn_data()
        for i in range(4):
            self.labelangle[i].setText(f"Angle{i}：{self.learn_data[self.page6_update_value][i]}")
            self.labelangle[i].adjustSize()
        return

    def page6_del(self):
        self.learn_data.pop(self.page6_update_value)
        if self.page6_update_value >= len(self.learn_data):
            self.page6_update_value -= 1
        self.update_learn_data()
        for i in range(4):
            self.labelangle[i].setText(f"Angle{i}：{self.learn_data[self.page6_update_value][i]}")
            self.labelangle[i].adjustSize()
        return
    
    def page6_drop(self):
        setsql.drop_table(self.learn_name)
        for button in self.learn_button:
            button.deleteLater()
            self.learn_button.remove(button)
        for button in self.page2Button:
            button.deleteLater()
            self.page2Button.remove(button)
        self.createPage2Button()
        self.createPage4Button()
        self.show_page4()
    
    def change_box2(self):
        self.page6_set = self.box2_value[self.box2.currentIndex()]

    def show_page7(self):
        self.input.clear()
        self.stacked_widget.setCurrentWidget(self.page7)

    def page7_add(self):
        name = self.input.text()
        setsql.add_table(name)
        self.show_page4()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
