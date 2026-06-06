from machine import Pin, PWM, SoftI2C, Timer
from micropython import const
import domain.sensorData as sensorData

import driver.hdc1080 as hdc1080
import driver.PM5350P as pm5350p

import domain.AAC as AAC
_FAN_PWM_FREQ = const(1000)
_FAN_PWM_DEFAULT = const(0)

class BSP:
    def __init__(self):
        self.config = None
        self.softI2C = SoftI2C(scl=Pin(3), sda=Pin(8), freq=100000)

        # esp32 引脚2是一颗自带的 led的灯
        self.__LED = Pin(2, Pin.OUT, value=0)

        #PM5350实例
        self.__pm5350pInstance = None
        self.__pm5350pData = {}

        # PWM控制
        self.__fanSpeed = 0
        self.__fan1PwmPin = None
        self.__fan2PwmPin = None
        self.__fan3PwmPin = None
        self.__fan4PwmPin = None

        #
        self.__sensorData = sensorData.SensorData()

        print("init hdc1080...")
        self.__hdc1080 = hdc1080.HDC1080(self.softI2C)

        self.__sensorReadTimer = Timer(0)
        self.__sensorReadTimer.init(mode=Timer.PERIODIC, period=5000, callback=self.timerHandler)

        self.aac = AAC.AAC()
    def setConfig(self, config):
        self.config = config
        self.initHW()

    def initHW(self):
        print("init pwm...")
        # PWM控制
        self.__fanSpeed = 0
        self.__fan1PwmPin = PWM(Pin(3),freq=self.config["pwm1freq"], duty=self.config["pwm1default"])
        self.__fan2PwmPin = PWM(Pin(46),freq=self.config["pwm2freq"], duty=self.config["pwm2default"])
        self.__fan3PwmPin = PWM(Pin(9),freq=self.config["pwm3freq"], duty=self.config["pwm3default"])
        self.__fan4PwmPin = PWM(Pin(10),freq=self.config["pwm4freq"], duty=self.config["pwm4default"])
        # 初始化PWM对象
        self.__fan1PwmPin.init(freq=self.config["pwm1freq"], duty=self.config["pwm1default"])
        self.__fan2PwmPin.init(freq=self.config["pwm2freq"], duty=self.config["pwm2default"])
        self.__fan3PwmPin.init(freq=self.config["pwm3freq"], duty=self.config["pwm3default"])
        self.__fan4PwmPin.init(freq=self.config["pwm4freq"], duty=self.config["pwm4default"])

        print("init PM5350P...")
        self.__pm5350pInstance = pm5350p.PM5350P(self.config["modbusSlaveAddr"],self.config["modbusBadud"])

    def readPm5350p(self):
        return self.__pm5350pData

    def hdc1080TimerHandler(self, timer):
        self.__sensorData.temp = self.__hdc1080.temperature
        self.__sensorData.humi = self.__hdc1080.humidity
        self.__sensorData.wetBulbTemp = self.aac.ts(self.__sensorData.temp, self.__sensorData.humi/100.0, 0.1)
        # print("hdc1080:temp={},humi={}".format(self.sensorData.temp, self.sensorData.humi))

    def pm5350pTimerHandler(self, timer):
        self.__pm5350pData = self.__pm5350pInstance.read()

    def timerHandler(self, timer):
        print("read sensor data...")
        #self.hdc1080TimerHandler(timer)
        #self.pm5350pTimerHandler(timer)

    def setLed(self, status):
        if status == 1:
            self.__LED.on()
        else:
            self.__LED.off()

    def setFan1Pwm(self, percent):
        if percent > 100:
            percent = 100

        if percent < 0:
            percent = 0

        self.__fanSpeed = percent

        duty = 0

        if percent == 0:
            duty = 0
        else:
            base = (self.config["pwm1min"]/100)*self.config["pwm1freq"]
            full = (self.config["pwm1max"] - self.config["pwm1min"])/100*self.config["pwm1freq"]
            duty = 1023*(full * (percent / 100.0) + base) /self.config["pwm1freq"]
            print("base:{},full:{},duty:{}".format(base,full,int(duty)))
            if duty > self.config["pwm1freq"]:
                duty = self.config["pwm1freq"] 

        
        #第2组用于控制风险转速
        self.__fan2PwmPin.duty(int(duty))
        #第3组用于同步控制mos，给风扇供应电源
        self.__fan3PwmPin.duty(int(duty))
        #第1组用于直接控制mos，给风扇供应电源
        if duty == 0:
            self.__fan1PwmPin.duty(0)
            print("PWM duty1:{}，duty2:{}，duty3:{}".format(int(duty),int(duty),0))
        else:
            #duty3=int(self.__systemConfig["pwm3max"]*self.__systemConfig["pwm3freq"]/100)
            self.__fan1PwmPin.duty(1023)
            print("PWM duty1:{}，duty2:{}，duty3:{}".format(int(duty),int(duty),1023))


    def getSensorData(self):
        return self.__sensorData

    def getfanSpeed(self):
        return self.__fanSpeed
    
bspInstance = BSP()
