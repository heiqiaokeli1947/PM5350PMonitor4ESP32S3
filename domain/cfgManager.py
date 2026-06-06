import uio,ujson

configFilePath='/resource/system.config'
DEFAULT_CONFIG={"deviceusername":"admin","devicepwd":"pengping","wifipwdDefault":"13438045703","devicetype":"NodeMCU","num2name":"Tree humidity","APName":"PM5350P","sw2name":"S2","id":1,"wifiname":"cissco_2g","ver":"1.1","serverurl":"192.168.1.124","APNetMask":"255.255.255.0","altitude":498.0,"wifinameDefault":"IOT_2G","latitude":30.67831,"serverurlDefault":"http://3a892544f7.qicp.vip","APPwd":"19880612","devicename":"PM5350P","num1name":"Tree temprature","rangename":"Tree light","mode":"normal","sw1name":"S1","wifipwd":"13438045703","APGateway":"192.168.1.1","APIP":"123","longitude":104.0375,"pwm1freq":25000,"pwm1default":0,"pwm1min":15,"pwm1max":100,"pwm2freq":25000,"pwm2default":0,"pwm2min":15,"pwm2max":100,"pwm3freq":25000,"pwm3default":0,"pwm3min":15,"pwm3max":100,"pwm4freq":25000,"pwm4default":0,"pwm4min":15,"pwm4max":100,"fanHThreshold":36,"fanLThreshold":31.5,"modbusSlaveAddr":6,"modbusBadud":38400}

def createDefaultConfig():
    try:
        with uio.open(configFilePath,"w") as f:
            conf=ujson.dumps(DEFAULT_CONFIG)
            f.write(conf)
    except OSError:
        print("create default config file error.")


def loadCfg():
    try:
        with uio.open(configFilePath,"r") as f:
            conf = ujson.loads(f.read())
            print("conf in file:{}".format(conf))
            return conf
    except OSError:
        print("read cfg failed,I will create default config.")
        createDefaultConfig()
        return DEFAULT_CONFIG
        
def saveCfg(newCfg):
    try:
        with uio.open(configFilePath,"w") as f:
            conf=ujson.dumps(newCfg)
            print("new conf:{}".format(conf))
            f.write(conf)
    except OSError:
        print("save cfg failed.")