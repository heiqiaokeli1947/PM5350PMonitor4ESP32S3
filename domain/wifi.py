# 操作esp32引脚
from machine import Pin

# 操作时间 延迟几秒等
import time

# 网络相关的函数
import network

import sys

# esp32 引脚2是一颗自带的 led的灯
light = Pin(2, Pin.OUT)


def connectToWifi(ssid, pwd):
    # wifi模式
    wlan = network.WLAN(network.STA_IF)
    # 激活
    wlan.active(True)
    print("init wifi...")
    try:
        #  连接超时设置
        start_time = time.time()
        print("start time:{}".format(start_time))
        if not wlan.isconnected():
            print("try to connect ssid:{} pwd:{}".format(ssid, pwd))
            wlan.connect(ssid, pwd)
            while not wlan.isconnected():
                print("connect failed,sleep 1s")
                time.sleep(1)
                # 15秒内没连接上就是超时了
                print("now time:{}".format(time.time()))
                us = time.time() - start_time
                print("use time:{}".format(us))
                if us > 35:
                    print("connect wifi timeout.")
                    #wlan.active(False)
                    return False
            print("connect success.")
            light.value(1)
            # 打印 网络信息
            print("ifconfig:", wlan.ifconfig())
            return True
        else:
            print("connect success.")
            light.value(0)
            # 打印 网络信息
            print("ifconfig:", wlan.ifconfig())
            return True
    except Exception as e:
        sys.print_exception(e)
        print('connect exception.')
        #wlan.active(False)
        return False
    finally:
        print('connectWiFi finish')


def getStationIP():
    wlan = network.WLAN(network.STA_IF)
    if wlan.active and wlan.isconnected():
        return wlan.ifconfig()[0]
    else:
        return "Station not active or not connected."


def testWifiConnect(ssid, pwd):
    print("try to connect ssid:{} pwd:{}".format(ssid, pwd))
    # wifi模式
    wlan = network.WLAN(network.STA_IF)
    # 激活
    print("init wifi...")
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)

    try:
        #  连接超时设置
        start_time = time.time()
        print("start time:{}".format(start_time))
        wlan.connect(ssid, pwd)
        while not wlan.isconnected():
            print("sleep 1s then retry.")
            time.sleep(1)
            # 15秒内没连接上就是超时了
            #print("now time:{}".format(time.time()))
            us = time.time() - start_time
            #print("use time:{}".format(us))
            if us > 35:
                print("test connect failed by timeout.")
                return False
        # 打印 网络信息
        print("test connect success! ifconfig:", wlan.ifconfig())
        return True
    except Exception as e:
        sys.print_exception(e)
        print('test connect exception.')
        #wlan.active(False)
        return False
    finally:
        print('test connect WiFi finish.')


def startAP(apname, appwd, forConfig=False):
    try:
        # 创建Wi-Fi接入点
        ap = network.WLAN(network.AP_IF)
        # 启用接入点
        #ap.active(False)
        #time.sleep(1)
        ap.active(True)
        if forConfig:
            tmpName = apname + "_" + ap.ifconfig()[0]
        else:
            tmpName = apname
        print("start ap:{},{}".format(tmpName, appwd))
        # 设置接入点参数
        ap.config(essid=tmpName, authmode=network.AUTH_WPA_WPA2_PSK, password=appwd)
        # 输出接入点IP地址
        print('AP IP address:{}'.format(tmpName))
        return True
    except Exception as e:
        sys.print_exception(e)
        print('start AP exception.')
        #ap.active(False)
        return False
    finally:
        print('start AP finish.')


def startBroadcastAP(apname, appwd):
    try:
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=apname, authmode=network.AUTH_WPA_WPA2_PSK, password=appwd)
        return True
    except Exception as e:
        sys.print_exception(e)
        print('start AP exception.')
        return False
    finally:
        print('start AP finish.')


def getAPIP():
    ap = network.WLAN(network.AP_IF)
    if ap.active():
        return ap.ifconfig()[0]
    else:
        return "AP not active."


def stopAP():
    try:
        print('stop AP...')
        ap = network.WLAN(network.AP_IF)
        ap.active(False)
        return True
    except Exception as e:
        sys.print_exception(e)
        print('stop AP exception.')
        #ap.active(False)
        return False
    finally:
        print('stop AP finish.')


def isConnected():
    wlan = network.WLAN(network.STA_IF)
    return wlan.isconnected()


def scanAP():
    try:
        print('scan AP...')
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        res = wlan.scan()  #(ssid, bssid, channel, RSSI, security, hidden)
        result = {}
        for item in res:
            if len(item[0]) != 0:
                result[item[0]] = item[3]
        print('Find AP:{}'.format(result))
        return result
    except Exception as e:
        sys.print_exception(e)
        print('scan AP exception.')
        return {}
    finally:
        print('scan AP finish.')