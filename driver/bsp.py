from machine import Pin, PWM, I2C, SoftI2C, Timer
from micropython import const
import domain.sensorData as sensorData
import neopixel

import driver.hdc1080 as hdc1080
import driver.PM5350P as pm5350p

import domain.AACOps as AAC
_FAN_PWM_FREQ = const(1000)
_FAN_PWM_DEFAULT = const(0)

class BSP:
    # 单例实例
    __instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(BSP, cls).__new__(cls)
            # 延迟初始化，在第一次调用时完成
            cls.__instance._initialized = False
        return cls.__instance
    
    def __init__(self):
        # 防止重复初始化
        if self._initialized:
            print("BSP initialed.")
            return
        
        self.config = None
        self.softI2C = SoftI2C(scl=Pin(3), sda=Pin(8), freq=100000)

        # esp32 引脚2是一颗自带的 led的灯
        self.__LED = Pin(2, Pin.OUT, value=0)
        # WS2812 8*1矩阵
        self.__LEDArray = neopixel.NeoPixel(Pin(48), 1)  #16->48

        self.__sysEnableSwitch = Pin(5, Pin.IN, Pin.PULL_DOWN)  #ESP32S3引脚范围0~21、26~48，所以修改23->5
        # 34及以上，无上下拉，需要外置
        self.__sprayEnableSwitch = Pin(6, Pin.IN, Pin.PULL_DOWN)  #ESP32S3引脚范围0~21、26~48，所以修改34->6
        self.__airconditionerForceEn = Pin(7, Pin.IN, Pin.PULL_DOWN)  # ESP32S3引脚范围0~21、26~48，所以修改34->7
        self.__airconditionerHallSensor = Pin(14, Pin.IN, Pin.PULL_DOWN)
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

        self.__sensorReadTimer = Timer(1)
        self.__sensorReadTimer.init(mode=Timer.PERIODIC, period=5000, callback=self.timerHandler)

        self.setLEDArray((255, 255, 255))
        self.aac = AAC.AACOptimized()
        
        # 标记已初始化
        self._initialized = True

    def setConfig(self, config):
        self.config = config
        self.initHW()

    def initHW(self):
        print("init pwm...")
        # PWM控制
        self.__fanSpeed = 0
        self.__fan1PwmPin = PWM(Pin(46),freq=self.config["pwm1freq"], duty=self.config["pwm1default"])
        self.__fan2PwmPin = PWM(Pin(9),freq=self.config["pwm2freq"], duty=self.config["pwm2default"])
        self.__fan3PwmPin = PWM(Pin(10),freq=self.config["pwm3freq"], duty=self.config["pwm3default"])
        self.__fan4PwmPin = PWM(Pin(11),freq=self.config["pwm4freq"], duty=self.config["pwm4default"])
        # 初始化PWM对象
        self.__fan1PwmPin.init(freq=self.config["pwm1freq"], duty=self.config["pwm1default"])
        self.__fan2PwmPin.init(freq=self.config["pwm2freq"], duty=self.config["pwm2default"])
        self.__fan3PwmPin.init(freq=self.config["pwm3freq"], duty=self.config["pwm3default"])
        self.__fan4PwmPin.init(freq=self.config["pwm4freq"], duty=self.config["pwm4default"])

        print("init PM5350P...")
        self.__pm5350pInstance = pm5350p.PM5350P(self.config["modbusSlaveAddr"],self.config["modbusBadud"])

    def setLEDArray(self, color):
        for i in range(1):
            self.__LEDArray[i] = color
        self.__LEDArray.write()
        
    def readPm5350p(self):
        return self.__pm5350pData

    def hdc1080TimerHandler(self, timer):
        self.__sensorData.temp = self.__hdc1080.temperature
        self.__sensorData.humi = self.__hdc1080.humidity
        self.__sensorData.wetBulbTemp = self.aac.ts(self.__sensorData.temp, self.__sensorData.humi/100.0, 0.1)
        print("hdc1080:temp={},humi={},wetBulbTemp={}".format(self.__sensorData.temp, self.__sensorData.humi,self.__sensorData.wetBulbTemp))

    def pm5350pTimerHandler(self, timer):
        self.__pm5350pData = self.__pm5350pInstance.read()
        #print("pm5350p:{}".format(self.__pm5350pData))

    def timerHandler(self, timer):
        print("read sensor data...")
        self.hdc1080TimerHandler(timer)
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

    def getSysEnableStatus(self):
        if self.__sysEnableSwitch.value() == 1:
            return True
        else:
            return False

    def getSprayEnableStatus(self):
        if self.__sprayEnableSwitch.value() == 1:
            return True
        else:
            return False

    def getAirconditionerStatus(self):
        if self.__airconditionerHallSensor.value() == 1 or self.__airconditionerForceEn.value() == 1:
            return True
        else:
            return False

    def getSensorData(self):
        return self.__sensorData

    def getfanSpeed(self):
        return self.__fanSpeed
    
    @classmethod
    def getInstance(cls):
        """获取单例实例"""
        if cls.__instance is None:
            cls.__instance = BSP()
        return cls.__instance
