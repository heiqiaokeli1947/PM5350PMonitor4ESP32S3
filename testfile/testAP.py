from machine import Pin, PWM
import time
import network

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect('ssid', 'key')
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())
    
def redian():
    # 创建Wi-Fi接入点
    ap = network.WLAN(network.AP_IF)
    # 启用接入点
    ap.active(True)
    apname='laoliu_{}'.format(ap.ifconfig()[0])
    # 设置接入点参数
    ap.config(essid=apname, authmode=network.AUTH_WPA_WPA2_PSK, password='12345678')
    # 输出接入点IP地址
    print('AP IP address:', ap.ifconfig()[0])

redian()
