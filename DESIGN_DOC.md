# PM5350P Monitor for ESP32S3 项目设计文档

## 1. 项目概述

### 1.1 项目背景
本项目是一个基于 ESP32-S3 的功率监测系统，通过 Modbus RTU 协议读取施耐德 PM5350P 电力监测仪表的数据，并提供 Web 界面进行配置和数据查看。

### 1.2 功能特性
- 实时读取三相电力参数（电流、电压、功率、功率因数、电能等）
- 支持 WiFi 连接和 AP 配置模式
- 提供 Web 服务器进行设备配置和状态查询
- 看门狗定时器保障系统稳定性
- 持久化存储系统配置

### 1.3 硬件平台
- **主控芯片**: ESP32-S3 (带 SPIRAM)
- **传感器**: HDC1080 温湿度传感器
- **功率监测**: 施耐德 PM5350P (Modbus RTU)
- **风扇控制**: 4 路 PWM 输出

---

## 2. 架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    应用层 (Application)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Web Server │  │  System Task │  │  Config Manager  │  │
│  │  (Microdot)  │  │ (Main Loop)  │  │    (DBUtils)     │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼───────────────────┼─────────────┘
          │                 │                   │
┌─────────▼─────────────────▼───────────────────▼─────────────┐
│                    服务层 (Service)                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   WiFi 管理  │  │   看门狗     │  │     BSP 层       │  │
│  │  (domain/)   │  │  (WDT/Timer) │  │   (driver/)      │  │
│  └──────┬───────┘  └──────────────┘  └────────┬─────────┘  │
└─────────┴──────────────────────────────────────┼─────────────┘
                                                │
┌───────────────────────────────────────────────▼─────────────┐
│                    硬件层 (Hardware)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐ │
│  │  PM5350P │ │ HDC1080  │ │   PWM    │ │    WiFi/AP     │ │
│  │(Modbus)  │ │ (I2C)    │ │(风扇控制)│ │   网络接口     │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

| 模块层级 | 模块名称 | 文件路径 | 职责说明 |
|---------|---------|---------|---------|
| 应用层 | Web Server | `lib/microdot.py`, `main.py` | HTTP 请求处理、路由分发 |
| 应用层 | System Task | `main.py` | 主循环任务、定时数据采集 |
| 应用层 | Config Manager | `domain/DBUtils.py` | 系统配置持久化存储 |
| 服务层 | WiFi 管理 | `domain/wifi.py` | WiFi 连接、AP 模式管理 |
| 服务层 | BSP 层 | `driver/bsp.py` | 硬件抽象、传感器管理 |
| 驱动层 | PM5350P | `driver/PM5350P.py` | Modbus RTU 通信驱动 |
| 驱动层 | HDC1080 | `driver/hdc1080.py` | 温湿度传感器驱动 |
| 驱动层 | Modbus | `lib/modbus/` | Modbus 协议实现 |

---

## 3. 核心模块设计

### 3.1 主程序模块 (`main.py`)

#### 3.1.1 功能职责
- 系统初始化（配置加载、硬件初始化）
- WiFi 连接管理（正常模式/AP 配置模式）
- Web 服务器启动
- 主循环任务调度
- 看门狗定时器管理

#### 3.1.2 状态机设计

```
┌─────────────────┐     连接失败/首次启动     ┌─────────────────┐
│   Normal Mode   │◄─────────────────────────│   Config Mode   │
│   (正常模式)     │─────────────────────────►│   (配置模式)    │
│  - 连接WiFi      │   WiFi配置成功           │  - 启动AP       │
│  - 广播IP        │   重启后进入             │  - Web配置      │
│  - 数据采集      │                          │  - 超时重启     │
└─────────────────┘                          └─────────────────┘
```

#### 3.1.3 关键变量

| 变量名 | 类型 | 说明 |
|-------|------|------|
| `systemConfig` | dict | 系统配置字典 |
| `startTime` | int | 启动时间戳 |
| `totalRunTime` | int | 累计运行时间（秒） |
| `runCounter` | int | 主循环计数器 |
| `whenGotoConfigMode` | int | 进入配置模式时间 |

### 3.2 BSP 模块 (`driver/bsp.py`)

#### 3.2.1 功能职责
- 硬件资源初始化和管理
- 传感器数据采集
- PWM 风扇控制
- LED 状态控制

#### 3.2.2 类结构

```python
class BSP:
    def __init__(self):
        # I2C 初始化
        self.softI2C = SoftI2C(scl=Pin(3), sda=Pin(8), freq=100000)
        # LED 控制 (引脚2)
        self.__LED = Pin(2, Pin.OUT, value=0)
        # PM5350P 实例
        self.__pm5350pInstance = None
        # PWM 风扇控制 (引脚3, 46, 9, 10)
        self.__fan1PwmPin = None
        self.__fan2PwmPin = None
        self.__fan3PwmPin = None
        self.__fan4PwmPin = None
        # 传感器数据对象
        self.__sensorData = SensorData()
        # HDC1080 传感器
        self.__hdc1080 = HDC1080(self.softI2C)
        # 传感器读取定时器 (5秒周期)
        self.__sensorReadTimer = Timer(0)
```

#### 3.2.3 引脚分配

| 引脚 | 功能 | 说明 |
|-----|------|------|
| IO2 | LED 控制 | ESP32-S3 板载 LED |
| IO3 | I2C SCL / PWM1 | 共享引脚 |
| IO8 | I2C SDA | HDC1080 数据 |
| IO9 | PWM3 | 风扇 MOS 控制 |
| IO10 | PWM4 | 风扇 MOS 控制 |
| IO17 | UART1 TX | Modbus 发送 |
| IO18 | UART1 RX | Modbus 接收 |
| IO46 | PWM2 | 风扇转速控制 |

### 3.3 PM5350P 驱动 (`driver/PM5350P.py`)

#### 3.3.1 功能职责
- Modbus RTU 协议通信
- 电力参数读取（电流、电压、功率、电能等）
- 数据解析和转换

#### 3.3.2 寄存器映射

| 寄存器地址 | 长度 | 数据类型 | 描述 |
|-----------|------|---------|------|
| 3000-3011 | 12 | float32[6] | A/B/C/N/G/Avg 相电流 |
| 3020-3037 | 18 | float32[9] | 线电压、相电压 |
| 3054-3061 | 8 | float32[4] | A/B/C/总功率 (kW) |
| 3078-3085 | 8 | float32[4] | A/B/C/总功率因数 |
| 3110-3111 | 2 | float32 | 频率 (Hz) |
| 3200-3227 | 28 | datetime/int64 | 电能数据 |

#### 3.3.3 输出数据结构

```python
pm5350Data = {
    'Ia': float,      # A相电流 (A)
    'Ib': float,      # B相电流 (A)
    'Ic': float,      # C相电流 (A)
    'In': float,      # N相电流 (A)
    'Ig': float,      # G相电流 (A)
    'Iavg': float,    # 平均电流 (A)
    'Vab': float,     # AB线电压 (V)
    'Vbc': float,     # BC线电压 (V)
    'Vca': float,     # CA线电压 (V)
    'Vll': float,     # 平均线电压 (V)
    'Van': float,     # A相电压 (V)
    'Vbn': float,     # B相电压 (V)
    'Vcn': float,     # C相电压 (V)
    'Pa': float,      # A相功率 (kW)
    'Pb': float,      # B相功率 (kW)
    'Pc': float,      # C相功率 (kW)
    'Ptotal': float,  # 总功率 (kW)
    'PFa': float,     # A相功率因数
    'PFb': float,     # B相功率因数
    'PFc': float,     # C相功率因数
    'PFtotal': float, # 总功率因数
    'ErestTime': int, # 电能复位时间
    'Eaed': int,      # 有功电能 (Wh)
    'Freq': float     # 频率 (Hz)
}
```

### 3.4 WiFi 管理模块 (`domain/wifi.py`)

#### 3.4.1 功能职责
- WiFi STA 模式连接
- WiFi AP 模式启动/停止
- 网络状态检测
- AP 扫描

#### 3.4.2 关键函数

| 函数名 | 功能 | 参数 | 返回值 |
|-------|------|------|--------|
| `connectToWifi(ssid, pwd)` | 连接 WiFi | ssid: 网络名称, pwd: 密码 | bool: 是否成功 |
| `startAP(apname, appwd)` | 启动 AP | apname: AP名称, appwd: 密码 | bool: 是否成功 |
| `stopAP()` | 停止 AP | 无 | bool: 是否成功 |
| `isConnected()` | 检查连接状态 | 无 | bool: 是否连接 |
| `getStationIP()` | 获取 STA IP | 无 | str: IP地址 |
| `scanAP()` | 扫描可用 AP | 无 | dict: {ssid: rssi} |
| `testWifiConnect(ssid, pwd)` | 测试 WiFi 连接 | ssid, pwd | bool: 是否成功 |

### 3.5 数据库模块 (`domain/DBUtils.py`)

#### 3.5.1 功能职责
- 基于 btree 的键值存储
- 系统配置持久化
- 运行时间统计存储

#### 3.5.2 关键函数

| 函数名 | 功能 | 参数 | 返回值 |
|-------|------|------|--------|
| `save(kv)` | 保存键值对 | kv: dict | 无 |
| `get(k)` | 获取值 | k: str | value |
| `delete(keys)` | 删除键 | keys: list | 无 |
| `multiGet(keys)` | 批量获取 | keys: list | dict |

---

## 4. Web API 接口设计

### 4.1 接口总览

| 接口路径 | HTTP 方法 | 功能描述 |
|---------|----------|---------|
| `/` | GET | 返回主页 (index.html) |
| `/static/<path>` | GET | 静态资源访问 |
| `/status` | GET | 获取系统状态和传感器数据 |
| `/scanap` | GET | 扫描可用 WiFi 网络 |
| `/setwifi` | GET | 设置 WiFi 配置 |
| `/reset` | GET | 恢复出厂设置 |
| `/restart` | GET | 重启设备 |

### 4.2 接口详细设计

#### 4.2.1 `/status` - 获取系统状态

**请求参数:**

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|-----|------|
| `devicepwd` | string | 是 | 设备密码 |
| `mode` | string | 是 | `get` 获取状态 |

**成功响应 (errCode=0):**

```json
{
    "errCode": "0",
    "mode": "normal",
    "sw1name": "S1",
    "sw2name": "S2",
    "devicename": "PM5350P",
    "serverurl": "192.168.1.124",
    "temp": 25.5,
    "humi": 60.0,
    "wetBulbTemp": 18.2,
    "presure": 101325,
    "luminance": 450,
    "pm25": 12,
    "runTime": 3600,
    "totalRunTime": 86400,
    "Ia": 10.5,
    "Ib": 11.2,
    "Ic": 10.8,
    "Ptotal": 5.5,
    "Freq": 50.0
}
```

#### 4.2.2 `/scanap` - 扫描 WiFi

**请求参数:** 无

**成功响应:**

```json
{
    "cissco_2g": -58,
    "IOT_2G": -65,
    "TP-LINK_ABC": -72
}
```

#### 4.2.3 `/setwifi` - 设置 WiFi

**请求参数:**

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|-----|------|
| `ssid` | string | 是 | WiFi 名称 |
| `pwd` | string | 是 | WiFi 密码 |
| `serverurl` | string | 是 | 服务器地址 |
| `devicepwd` | string | 是 | 设备密码 |
| `devicename` | string | 是 | 设备名称 |
| `sw1name` | string | 是 | 开关1名称 |
| `sw2name` | string | 是 | 开关2名称 |

**成功响应:**

```json
{
    "errCode": "0",
    "msg": "connect wifi success and node will reboot after 5s.",
    "APName": "cissco_2g",
    "url": "192.168.1.100"
}
```

#### 4.2.4 `/reset` - 恢复出厂设置

**请求参数:**

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|-----|------|
| `devicepwd` | string | 是 | 设备密码 |

**成功响应:**

```json
{
    "errCode": "0",
    "msg": "success"
}
```

#### 4.2.5 `/restart` - 重启设备

**请求参数:**

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|-----|------|
| `devicepwd` | string | 是 | 设备密码 |

**成功响应:**

```json
{
    "errCode": "0",
    "msg": "success"
}
```

---

## 5. 系统配置设计

### 5.1 默认配置

```python
defaulteSystemConfig = {
    "deviceusername": "admin",           # 设备用户名
    "devicepwd": "pengping",             # 设备密码
    "devicetype": "NodeMCU",             # 设备类型
    "devicename": "PM5350P",             # 设备名称
    "APName": "PM5350P",                 # AP 名称
    "APPwd": "Changeme_123",             # AP 密码
    "wifiname": "cissco_2g",             # WiFi 名称
    "wifipwd": "13438045703",            # WiFi 密码
    "serverurl": "192.168.1.124",        # 服务器地址
    "mode": "normal",                    # 运行模式
    "sw1name": "S1",                     # 开关1名称
    "sw2name": "S2",                     # 开关2名称
    "num1name": "Tree temprature",       # 数值1名称
    "num2name": "Tree humidity",         # 数值2名称
    "rangename": "Tree light",           # 范围名称
    "latitude": 30.67831,                # 纬度
    "longitude": 104.0375,               # 经度
    "altitude": 498,                     # 海拔
    "pwm1freq": 25000,                   # PWM1 频率
    "pwm1default": 0,                    # PWM1 默认值
    "pwm1min": 15,                       # PWM1 最小值
    "pwm1max": 100,                      # PWM1 最大值
    "pwm2freq": 25000,                   # PWM2 频率
    "pwm2default": 0,                    # PWM2 默认值
    "pwm2min": 15,                       # PWM2 最小值
    "pwm2max": 100,                      # PWM2 最大值
    "pwm3freq": 25000,                   # PWM3 频率
    "pwm3default": 0,                    # PWM3 默认值
    "pwm3min": 15,                       # PWM3 最小值
    "pwm3max": 100,                      # PWM3 最大值
    "pwm4freq": 25000,                   # PWM4 频率
    "pwm4default": 0,                    # PWM4 默认值
    "pwm4min": 15,                       # PWM4 最小值
    "pwm4max": 100,                      # PWM4 最大值
    "fanHThreshold": 36,                 # 风扇启动温度
    "fanLThreshold": 31.5,               # 风扇停止温度
    "modbusSlaveAddr": 6,                # Modbus 从站地址
    "modbusBadud": 38400                 # Modbus 波特率
}
```

---

## 6. 主循环流程

### 6.1 初始化阶段

```
1. 加载系统配置 (DBUtils.get)
   └─ 配置不存在 → 创建默认配置

2. 初始化 BSP (bspInstance.setConfig)
   ├─ 初始化 I2C 总线
   ├─ 初始化 HDC1080 传感器
   ├─ 初始化 PWM 风扇控制
   └─ 初始化 PM5350P (Modbus)

3. 初始化看门狗定时器 (WDT, 60秒)
   └─ 创建喂狗定时器 (Timer 1, 5秒周期)

4. WiFi 连接处理
   ├─ 模式=normal → 尝试连接 WiFi
   │   ├─ 连接成功 → 启动 IP 广播线程
   │   └─ 连接失败 → 进入配置模式
   └─ 模式=config → 启动 AP, 创建超时定时器
```

### 6.2 主循环

```
while True:
    1. 更新运行时间统计
    2. 每90次循环 → 执行 GC 垃圾回收
    3. 每3600次循环 → 保存运行时间到数据库
    4. 延时 1000ms
    5. 计数器 +1
```

### 6.3 传感器读取定时器 (5秒周期)

```
timerHandler(timer):
    1. 读取 HDC1080 温湿度
    2. 计算湿球温度
    3. 读取 PM5350P 电力参数
```

---

## 7. 异常处理与稳定性

### 7.1 看门狗机制

- **超时时间**: 60 秒
- **喂狗周期**: 5 秒 (Timer 1)
- **触发条件**: 系统卡死超过 60 秒自动复位

### 7.2 WiFi 连接超时

- **超时时间**: 35 秒
- **重试机制**: 每秒重试一次
- **失败处理**: 自动切换到 AP 配置模式

### 7.3 配置模式超时

- **超时时间**: 300 秒 (5分钟)
- **处理方式**: 超时后自动重启设备

### 7.4 Modbus 通信异常

```python
try:
    # Modbus 读取操作
    temp = self.modubsrtu.read_holding_registers(...)
except OSError:
    print("no data received.")
    return {}
except ValueError as e:
    print("ValueError exception:{}".format(e))
    return {}
```

---

## 8. 目录结构

```
PM5350PMonitor4ESP32S3/
├── Doc/                    # 文档资料
│   ├── BH1750.pdf          # BH1750 传感器文档
│   ├── BMP280.pdf          # BMP280 传感器文档
│   ├── ESP32开发板引脚.webp # ESP32 引脚图
│   ├── GXTH35.pdf          # GXTH35 传感器文档
│   ├── HDC1080.pdf         # HDC1080 传感器文档
│   ├── PMS5003I颗粒物传感器中文说明书.pdf
│   ├── 开发笔记.txt         # 开发笔记
│   └── 新建 DOC 文档.doc
├── domain/                 # 业务逻辑层
│   ├── AAC.py              # AAC 算法（湿球温度计算）
│   ├── DBUtils.py          # 数据库工具
│   ├── FanFSM.py           # 风扇状态机
│   ├── MathTool.py         # 数学工具（浮点转换）
│   ├── cfgManager.py       # 配置管理器
│   ├── fileUtils.py        # 文件工具
│   ├── getFsInfo.py        # 文件系统信息
│   ├── sensorData.py       # 传感器数据类
│   └── wifi.py             # WiFi 管理
├── driver/                 # 驱动层
│   ├── PM5350P.py          # PM5350P Modbus 驱动
│   ├── SHT20.py            # SHT20 传感器驱动
│   ├── bh1750.py           # BH1750 传感器驱动
│   ├── bmp280.py           # BMP280 传感器驱动
│   ├── bsp.py              # 板级支持包
│   ├── co2Sensor.py        # CO2 传感器驱动
│   ├── csmc.py             # CSMC 传感器驱动
│   ├── enumEV.py           # 事件枚举
│   ├── enumSysStatus.py    # 系统状态枚举
│   ├── hdc1080.py          # HDC1080 传感器驱动
│   ├── htu21d.py           # HTU21D 传感器驱动
│   ├── htu21d2.py          # HTU21D2 传感器驱动
│   └── pms5003.py          # PMS5003 传感器驱动
├── firmware/               # 固件文件
│   └── ESP32_GENERIC_S3-SPIRAM_OCT-20260406-v1.28.0.bin
├── lib/                    # 第三方库
│   ├── modbus/             # Modbus 协议库
│   │   ├── uModBusConst.py
│   │   ├── uModBusFunctions.py
│   │   ├── uModBusSerial.py
│   │   └── uModBusTCP.py
│   └── microdot.py         # Microdot Web 框架
├── resource/               # 资源文件
│   └── system.config       # 系统配置模板
├── source/                 # 源代码（开发日志）
│   └── 开发日志.txt
├── static/                 # Web 静态资源
│   ├── chart.umd.js        # 图表库
│   ├── favicon.ico         # 网站图标
│   ├── index - 本地调试.html
│   ├── index.html          # 主页
│   ├── jquery.min.js       # jQuery
│   ├── spectre.min.css     # CSS 框架
│   └── sweetalert.min.js   # 弹窗库
├── testfile/               # 测试文件
│   ├── Mbslave_PM5350P.mbs # Modbus 从站配置
│   ├── test.json           # 测试数据
│   ├── testAP.py           # AP 测试
│   ├── testFile.py         # 文件测试
│   └── testrequest.py      # 请求测试
├── .gitignore              # Git 忽略配置
├── LICENSE                 # 许可证
├── README.md               # 项目说明
├── boot.py                 # 启动脚本
└── main.py                 # 主程序
```

---

## 9. 部署说明

### 9.1 固件烧录

1. 使用 ESP-IDF 或 esptool.py 烧录固件
2. 固件文件: `firmware/ESP32_GENERIC_S3-SPIRAM_OCT-20260406-v1.28.0.bin`
3. 烧录地址: 0x00000

### 9.2 文件上传

使用 ampy 或 webrepl 上传以下文件：
- `boot.py`
- `main.py`
- `lib/` 目录
- `driver/` 目录
- `domain/` 目录
- `static/` 目录

### 9.3 首次启动

1. 设备启动后自动进入 AP 配置模式
2. 连接 SSID: `PM5350P`, 密码: `Changeme_123`
3. 访问 `http://192.168.4.1` 配置 WiFi
4. 配置成功后设备自动重启并连接 WiFi

---

## 10. 版本历史

| 版本 | 日期 | 说明 |
|-----|------|------|
| v1.0 | 初始版本 | 基础功能实现 |
| v1.1 | - | 添加 PM5350P 支持 |
| v1.2 | - | 优化 WiFi 连接逻辑 |
