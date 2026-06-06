import utime
import driver.enumSysStatus as enumSysStatus
import domain.DBUtils as db
import domain.AAC as AAC

class STATUS:
    INIT = 0
    READY = 1
    SYS_ENABLED = 2
    AIR_CONDITIONER_ON = 3
    OVER_TEMP = 4
    FAN_DELAY = 5

class FSM:
    def __init__(self,bspInstance,config):
        self.bspInstance = bspInstance
        self.config = config
        self.status = STATUS.INIT
        self.FSMRunCounter = 0
        self.startTime = utime.time()
        self.runTimeCounter = 0
        self.totalRunTime = 0
        if db.get("totalRunTime") is not None:
            self.totalRunTime = int(db.get("totalRunTime"))
        else:
            db.save({"totalRunTime":str(self.totalRunTime)})

        self.fanTotalRunTime = 0
        if db.get("fanTotalRunTime") is not None:
            self.fanTotalRunTime = int(db.get("fanTotalRunTime"))
        else:
            db.save({"fanTotalRunTime":str(self.fanTotalRunTime)})

        self.sysStatus = 0
        # 0=禁止 1=使能
        
        self.airConditionerStatus = 0

        self.fanOpenTime = 0
        self.fanDelayTime = 5
        self.fan1Speed = 0

        self.airTemp = 0
        self.humity = 0
        self.wetBulbTemp = 0
        self.aac = AAC.AAC()
   

        self.roomTemp = 0
        self.roomTempThreshold = 32

        self.lastOverTempTime = 0

        self.switch = {STATUS.INIT: self.initDevice,
                       STATUS.READY: self.checkSystemEnableStaus,
                       STATUS.SYS_ENABLED: self.checkAirConditionerStatus,
                       STATUS.AIR_CONDITIONER_ON: self.checkOverTemperature,
                       STATUS.OVER_TEMP: self.fitFanSpeed,
                       STATUS.FAN_DELAY: self.checkFanDelayTimeout}
        
    def setConfig(self, config):
        self.config = config

    def getStatus(self):
        return {"totalRunTime":self.totalRunTime,"fanTotalRunTime":self.fanTotalRunTime,"fanHThreshold":self.config["fanHThreshold"],"fanLThreshold":self.config["fanLThreshold"],"fanSpeed":self.bspInstance.getfanSpeed(),"airTemp":self.airTemp,"wetBulbTemp":self.wetBulbTemp}

    def saveData(self):
        totalRunTime = str(self.totalRunTime)
        fanTotalRunTime = str(self.fanTotalRunTime)
        db.save({"totalRunTime":totalRunTime,"fanTotalRunTime":fanTotalRunTime})

    def close(self):
        print("Fan FSM:close")
        self.setDeviceToReadyStatus()
        self.saveData()

    def checkSystemEnableStaus(self):
        if enumSysStatus.enumSysStatus.SYS_ENABLED == self.sysStatus:
            self.status = STATUS.SYS_ENABLED
        else:
            self.status = STATUS.READY
            # 设备设置为初始化状态
            self.setDeviceToReadyStatus()

    def checkAirConditionerStatus(self):
        if self.airConditionerStatus == True:
            self.status = STATUS.AIR_CONDITIONER_ON
        else:
            self.status = STATUS.READY
            # 设备设置为初始化状态
            self.setDeviceToReadyStatus()

    #阈值26 超过32则全速: 档位=100*(temp-26)/(32-26)
    def checkOverTemperature(self):
        #温度超过全速阈值
        if self.airTemp > self.config["fanHThreshold"]:
            self.lastOverTempTime = self.runTimeCounter
            self.fan1Speed = 100
            self.status = STATUS.OVER_TEMP
            print("over temp full speed, need open fan {}%.".format(self.fan1Speed))
        #温度在全速阈值和启动阈值之间
        elif self.airTemp > self.config["fanLThreshold"]:
            self.lastOverTempTime = self.runTimeCounter
            self.fan1Speed = round(100 * (self.airTemp - self.config["fanLThreshold"])/(self.config["fanHThreshold"] - self.config["fanLThreshold"]),1)
            self.status = STATUS.OVER_TEMP
            print("over temp, need open fan {}%.".format(self.fan1Speed))
        #温度低于启动阈值
        else:
            self.fan1Speed = 0
            self.status = STATUS.READY
            # 设备设置为初始化状态
            self.setDeviceToReadyStatus()

    def fitFanSpeed(self):
        self.fanOpenTime = self.runTimeCounter
        self.bspInstance.setFan1Pwm(self.fan1Speed)
        self.status = STATUS.FAN_DELAY
        
        
    def checkFanDelayTimeout(self):
        if self.runTimeCounter - self.fanOpenTime >= self.fanDelayTime:
            print("fan fit delay finish.")
            self.status = STATUS.READY
        else:
            return

    def getTemperature(self):
        self.airTemp = self.bspInstance.getSensorData().temp
        self.humity = self.bspInstance.getSensorData().humi
        self.wetBulbTemp = self.bspInstance.getSensorData().wetBulbTemp
        self.roomTemp = self.bspInstance.getSensorData().tempBMP280

    def getSysStatus(self):
        self.sysStatus = self.bspInstance.getSysEnableStatus()

    def getAirConditonerStatus(self):
        self.airConditionerStatus = self.bspInstance.getAirconditionerStatus()

    def readSystemSensor(self):
        self.getTemperature()
        self.getSysStatus()
        self.getAirConditonerStatus()

    def setDeviceToReadyStatus(self):
        print("init device.")
        self.bspInstance.setFan1Pwm(0)

    def initDevice(self):
        # 初始化设备
        print("[WARN]init system.")
        self.setDeviceToReadyStatus()
        self.status = STATUS.READY
        return
    
    def run(self, timer):
        self.runTimeCounter = utime.time()
        self.totalRunTime += (self.runTimeCounter - self.startTime)
        self.startTime = self.runTimeCounter
        self.FSMRunCounter += 1
        self.readSystemSensor()

        if self.bspInstance.getfanSpeed() > 0:
            self.fanTotalRunTime += 1

        print( "[{}]Fan FSM:{},Temp:{},Humi:{},Wet bulb temp:{},Threshold:{},Fan speed:{}%".format(self.runTimeCounter, self.status, self.airTemp, self.humity, self.wetBulbTemp, self.config["fanLThreshold"], self.fan1Speed))
        if (self.FSMRunCounter % 2) == 0:
            self.bspInstance.setLed(1)
        else:
            self.bspInstance.setLed(0)

        if (self.FSMRunCounter % 3600) == 0:
            self.saveData()
            print("AM FSM:save data to db finish.")


        func = self.switch.get(self.status, lambda: print("Fan FSM:status not define."))
        return func()

# if __name__=="__main__":
#     fsm = FSM()
#
#     for i in range(50):
#         print("[tick]:{}".format(fsm.timeCounter))
#         fsm.timeCounter = i
#         fsm.run()
