import uio,ujson

config = uio.open("/test.json","r")

conf = ujson.loads(config.read())

print(conf)

if "a" in conf:
    conf["a"]="pengping"
    
newconf=ujson.dumps(conf)

print("newconf:{}".format(newconf))

