import machine
from machine import Timer
from lib.microdot import Microdot, send_file
import domain.wifi as wifi

import domain.fileUtils as fileUtils
import utime, ujson
import driver.bsp as bsp

import domain.DBUtils as db

import _thread
import gc
import micropython as mp

#import domain.LogUtils as LogUtils

#固件使用：ESP32_GENERIC_S3-SPIRAM_OCT-20250415-v1.25.0.bin
LEDArrayColor = (255, 0, 0)
# from machine import RTC

# rtc = RTC()
# rtc.datetime((2024, 1, 1, 12, 0, 0, 0, 0)) # set a specific date and time
# print(rtc.datetime()) # get date and time


#default systemConfig
defaulteSystemConfig = {"deviceusername": "admin", "devicepwd": "pengping", "wifipwdDefault": "13438045703",
                        "devicetype": "NodeMCU", "num2name": "Tree humidity", "APName": "PM5350P", "sw2name": "S2",
                        "id": 1, "wifiname": "cissco_2g", "ver": "1.1", "serverurl": "192.168.1.124",
                        "APNetMask": "255.255.255.0", "altitude": 498, "wifinameDefault": "IOT_2G",
                        "latitude": 30.67831, "serverurlDefault": "http://3a892544f7.qicp.vip", "APPwd": "Changeme_123",
                        "devicename": "PM5350P", "num1name": "Tree temprature", "rangename": "Tree light",
                        "mode": "normal", "sw1name": "S1", "wifipwd": "13438045703", "APGateway": "192.168.1.1",
                        "APIP": "123", "longitude": 104.0375, "pwm1freq": 25000, "pwm1default": 0, "pwm1min": 15,
                        "pwm1max": 100, "pwm2freq": 25000, "pwm2default": 0, "pwm2min": 15, "pwm2max": 100,
                        "pwm3freq": 25000, "pwm3default": 0, "pwm3min": 15, "pwm3max": 100, "pwm4freq": 25000,
                        "pwm4default": 0, "pwm4min": 15, "pwm4max": 100, "fanHThreshold": 36, "fanLThreshold": 31.5,
                        "modbusSlaveAddr": 6, "modbusBadud": 38400}
systemConfig = db.get("systemConfig")

#db.delete(["systemConfig"])

if systemConfig is not None:
    systemConfig = ujson.loads(systemConfig)
    print("systemConfig in DB:{}".format(systemConfig))
else:
    print("create default systemConfig:{}...".format(ujson.dumps(defaulteSystemConfig)))
    db.save({"systemConfig": ujson.dumps(defaulteSystemConfig)})
    systemConfig = ujson.loads(db.get("systemConfig"))


def createDefaultConfig():
    print("create default config...")
    db.delete(["systemConfig"])
    db.save({"systemConfig": ujson.dumps(defaulteSystemConfig)})


startTime = utime.time()
totalRunTime = 0
runTimeCounter = 0

if db.get("totalRunTime") is not None:
    totalRunTime = int(db.get("totalRunTime"))
else:
    db.save({"totalRunTime": str(totalRunTime)})

bspInstance = bsp.bspInstance
bspInstance.setConfig(systemConfig)

# 初始化看门狗定时器，超时时间为30秒
wdt = machine.WDT(timeout=60000)


def feedDog(timer):
    global runTimeCounter
    wdt.feed()
    print("{}:feed dog-----------".format(runTimeCounter))


WDTTimer = Timer(0)
WDTTimer.init(mode=Timer.PERIODIC, period=5000, callback=feedDog)


def saveData(self):
    global totalRunTime
    db.save({"totalRunTime": str(totalRunTime)})


#超时或者自动重连上了就会自动退出
def ModeTimerHandler(timer):
    print("config mode left {}s to exit.".format(MAX_CONFIG_MODE_TIME_IN_SECONDS - (utime.time() - whenGotoConfigMode)))
    status = wifi.isConnected()
    if status or ((utime.time() - whenGotoConfigMode) > MAX_CONFIG_MODE_TIME_IN_SECONDS):
        print("reboot after 5s.")
        wifi.stopAP()
        utime.sleep_ms(5000)
        machine.reset()


def createConfigTimer(seconds):
    modeTimer = Timer(3)
    modeTimer.init(mode=Timer.PERIODIC, period=seconds * 1000, callback=ModeTimerHandler)


print("start finish.")

#wifi.startAP(systemConfig["APName"],"880612")

MAX_CONFIG_MODE_TIME_IN_SECONDS = 300
whenGotoConfigMode = 0
whenGotoNormalMode = 0

#启动直接则尝试连接wifi，连接成功则直接连接，如果连接失败，则启动AP模式，AP模式最长等待300s
#如果300s仍然没有完成配置，则直接重启，如此往复
#在配置模式，配置成功wifi后，10s后自动重启

gotIpLast = ""
gotIpNow = ""


def broadcastIPInfo(name):
    global gotIpLast
    global gotIpNow
    global LEDArrayColor
    while True:
        print("{}:detect IP info...".format(name))
        gotIpNow = wifi.getStationIP()
        if gotIpNow and gotIpLast != gotIpNow:  # 检查IP获取是否成功
            broadcastName = systemConfig["devicename"] + "_" + gotIpNow
            wifi.startAP(broadcastName, systemConfig["APPwd"])
            print("---------------IP changed. now:{}, last:{}".format(gotIpNow, gotIpLast))
            gotIpLast = gotIpNow
        elif gotIpNow:
            print("get IP success:{}".format(gotIpNow))
            LEDArrayColor = (0, 255, 0)
            bspInstance.setLEDArray(LEDArrayColor)
        else:
            LEDArrayColor = (255, 0, 255)
            bspInstance.setLEDArray(LEDArrayColor)
            print("get IP failed.")
        utime.sleep_ms(5000)


if "normal" == systemConfig["mode"] and wifi.connectToWifi(systemConfig["wifiname"], systemConfig["wifipwd"]):
    print("connect wifi success. broadcast node ip.")
    _thread.start_new_thread(broadcastIPInfo, ("Thread-broadcastIPInfo",))
else:
    systemConfig["mode"] = "config"
    LEDArrayColor = (0, 0, 255)
    bspInstance.setLEDArray(LEDArrayColor)
    print("start config mode...")

    whenGotoConfigMode = utime.time()
    wifi.startAP(systemConfig["APName"], systemConfig["APPwd"], True)
    createConfigTimer(10)

# 初始化webserver
app = Microdot()


# 返回主页
@app.route('/')
def handler(request):
    global whenGotoConfigMode
    whenGotoConfigMode = utime.time()
    return send_file('/static/index.html')


@app.route('/favicon.ico')
def handler(request):
    if len(request.path) > 1:
        fileName = request.path[1:]
    else:
        return 'file name invalid:{}'.format(request.path), 404

    if '..' in fileName or not fileUtils.isFileExist("/static/", fileName):
        # directory traversal is not allowed
        return 'Not found:{}'.format(fileName), 404
    return send_file('/static/' + fileName)


@app.route('/static/<path:path>')
def handler(request, path):
    if '..' in path or not fileUtils.isFileExist("/static/", path):
        # directory traversal is not allowed
        return 'Not found', 404
    return send_file('/static/' + path)


@app.get('/status')
def handler(request):
    global whenGotoConfigMode
    global totalRunTime
    global runCounter
    global pm5350Data
    whenGotoConfigMode = utime.time()
    if "devicepwd" not in request.args or request.args["devicepwd"] != systemConfig["devicepwd"]:
        res = {"errCode": "-1", "msg": "invalid device password."}
        return ujson.dumps(res)
    elif "mode" in request.args and request.args["mode"] == "get":
        res = {"errCode": "0", "mode": "normal", "sw1": True, "sw2": False}
        res.update(systemConfig)
        # res["mode"] = systemConfig["mode"]
        # res["sw1name"] = systemConfig["sw1name"]
        # res["sw2name"] = systemConfig["sw2name"]
        # res["devicename"] = systemConfig["devicename"]
        # res["serverurl"] = systemConfig["serverurl"]
        # res["fineHThreshold"] = systemConfig["fineHThreshold"]
        # res["fineLThreshold"] = systemConfig["fineLThreshold"]

        res["temp"] = bspInstance.getSensorData().temp
        res["humi"] = bspInstance.getSensorData().humi
        res["wetBulbTemp"] = bspInstance.getSensorData().wetBulbTemp
        res["presure"] = bspInstance.getSensorData().presure
        res["luminance"] = bspInstance.getSensorData().luminance
        res["pm25"] = bspInstance.getSensorData().pm25
        res["runTime"] = runCounter
        res["totalRunTime"] = totalRunTime
        res.update(bspInstance.readPm5350p())

        return ujson.dumps(res)
    #'../status?mode=set&devicepwd={0}&r={1}&g={2}&b={3}&sw1={4}&sw2={5}
    elif "mode" in request.args and request.args["mode"] == "set":
        res = {"errCode": "0", "msg": "set finish."}
        db.save({"fineHThreshold": request.args["fineHThreshold"],
                "fineLThreshold": request.args["fineLThreshold"],
                "pwmFreq": request.args["pwmFreq"],
                 "pwmMinDuty": request.args["pwmMinDuty"],
                 "pwmMaxDuty": request.args["pwmMaxDuty"],
                 "sw1": request.args["sw1"],
                 "sw2": request.args["sw2"]})
        print("set config.")
        return ujson.dumps(res)
    else:
        res = {"errCode": "-1", "msg": "unsupported operation."}
        return ujson.dumps(res)


@app.get('/scanap')
def handler(request):
    global whenGotoConfigMode
    whenGotoConfigMode = utime.time()
    res = wifi.scanAP()
    if len(res) > 0:
        print("scanap:{}".format(res))
        return ujson.dumps(res)
    else:
        return "{}"


#setwifi?ssid=3&pwd=123456&serverurl=192.168.1.124&devicepwd=pengping&devicename=----&sw1name=----&sw2name=----
@app.get('/setwifi')
def handler(request):
    global whenGotoConfigMode
    whenGotoConfigMode = utime.time()
    res = {"errCode": "0", "msg": "success", "APName": "APName", "url": "url"}
    print("scanap:path:{} ".format(request.path))
    print("scanap:args:{}".format(request.args))
    ssid = request.args["ssid"]
    pwd = request.args["pwd"]
    if wifi.testWifiConnect(ssid, pwd):
        systemConfig["mode"] = "normal"
        systemConfig["sw1name"] = request.args["sw1name"]
        systemConfig["sw2name"] = request.args["sw2name"]
        systemConfig["devicename"] = request.args["devicename"]
        systemConfig["devicepwd"] = request.args["devicepwd"]
        systemConfig["serverurl"] = request.args["serverurl"]
        systemConfig["wifiname"] = ssid
        systemConfig["wifipwd"] = pwd
        systemConfig["mode"] = "normal"
        db.save({"systemConfig": ujson.dumps(systemConfig)})
        whenGotoConfigMode = utime.time() - MAX_CONFIG_MODE_TIME_IN_SECONDS + 10
        print("reboot after 10s.")
        createConfigTimer(10)
        res["APName"] = ssid
        res["url"] = wifi.getStationIP()
        res["errCode"] = "0"
        res["msg"] = "connect wifi success and node will reboot after 5s."
    else:
        systemConfig["mode"] = "config"
        res["errCode"] = "-1"
        res["msg"] = "connect wifi or save config failed."

    return ujson.dumps(res)


@app.get('/reset')
def handler(request):
    global whenGotoConfigMode
    whenGotoConfigMode = utime.time()
    res = {"errCode": "0", "msg": "success"}
    print("scanap:path:{} ".format(request.path))
    print("scanap:args:{}".format(request.args))

    if "devicepwd" in request.args and request.args["devicepwd"] == systemConfig["devicepwd"]:
        print("reset after 5s.")
        createDefaultConfig()
        createConfigTimer(5)
        whenGotoConfigMode = utime.time() - MAX_CONFIG_MODE_TIME_IN_SECONDS + 5
    else:
        res["errCode"] = "-1"
        res["msg"] = "invalid device passwd."

    return ujson.dumps(res)


#重启命令http://192.168.30.254/restart?devicepwd=pengping
@app.get('/restart')
def handler(request):
    global whenGotoConfigMode
    whenGotoConfigMode = utime.time()
    res = {"errCode": "0", "msg": "success"}
    print("scanap:path:{} ".format(request.path))
    print("scanap:args:{}".format(request.args))

    if "devicepwd" in request.args and request.args["devicepwd"] == systemConfig["devicepwd"]:
        print("reboot after 5s.")
        createConfigTimer(5)
        whenGotoConfigMode = utime.time() - MAX_CONFIG_MODE_TIME_IN_SECONDS + 5
    else:
        res["errCode"] = "-1"
        res["msg"] = "invalid device passwd."

    return ujson.dumps(res)


def runWebApp(name):
    print("start web app:{}...".format(name))
    app.run(host='0.0.0.0', port=80, debug=False, ssl=None)


try:
    _thread.stack_size(32 * 1024)
    _thread.start_new_thread(runWebApp, ("Thread:WebApp",))
except OSError as e:
    print(f"Error starting thread: {e}")


def sysTask():
    global runTimeCounter
    global totalRunTime
    global startTime
    global pm5350Data
    runTimeCounter = utime.time()
    totalRunTime += (runTimeCounter - startTime)
    startTime = runTimeCounter


runCounter = 0
while True:
    sysTask()

    if runCounter % 300 == 0:
        print("-------------Before GC-------------")
        mp.mem_info()
        gc.collect()
        print("-------------After  GC-------------")
        mp.mem_info()

    if runCounter % 2 == 0:
        bspInstance.setLEDArray((0, 0, 0))
    else:
        bspInstance.setLEDArray(LEDArrayColor)
		
    if (runCounter % 3600) == 0:  # 每一个小时保存一次数据，但当前次方法30s运行一次，有风险
        saveData(None)
        print("Main:save data to db finish.")

    utime.sleep_ms(1000)
    runCounter += 1

print("start UART REPL...")
