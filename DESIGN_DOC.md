# PM5350P Monitor for ESP32-S3 项目设计文档

## 1. 项目概述

### 1.1 项目背景
本项目是一个基于 ESP32-S3 微控制器的电力参数与环境监测系统，通过 Modbus RTU 协议读取施耐德 PM5350P 电力监测仪表数据，同时集成温湿度等环境传感器，提供 Web 界面进行远程配置和实时数据可视化。

### 1.2 功能特性
- **电力监测**：实时读取三相电压、电流、功率、功率因数、频率、累计电能
- **环境监测**：温度（HDC1080）、相对湿度、湿球温度（算法计算）
- **扩展传感器接口**：气压、照度、PM2.5（硬件支持，软件预留）
- **Web 配置界面**：设备参数配置、WiFi 配置、阈值设置
- **实时图表**：温度、湿度、功率、高/低温度阈值的历史趋势曲线
- **风扇控制**：4 路 PWM 输出，支持频率和占空比调节
- **系统稳定性**：看门狗定时器（60s）、配置持久化存储、WiFi 断线重连
- **双运行模式**：正常运行模式 / AP 配置模式

### 1.3 硬件平台
| 组件 | 型号 / 规格 | 接口 | 用途 |
|-----|------------|------|------|
| 主控 | ESP32-S3 | - | 主控制器，带 PSRAM |
| 温湿度传感器 | HDC1080 | I2C (SCL=IO3, SDA=IO8) | 温度、湿度 |
| 电力监测仪 | 施耐德 PM5350P | Modbus RTU (UART1) | 电力参数 |
| 风扇驱动 | 4 路 MOS 管 | PWM (IO46/9/10/11) | 散热风扇控制 |
| LED 指示 | WS2812 + 独立 LED | GPIO2, GPIO48 | 运行状态指示 |

### 1.4 软件栈
- **固件**：MicroPython (ESP32-S3-SPIRAM-OCT)
- **Web 框架**：Microdot (轻量级 WSGI 框架)
- **前端图表**：Chart.js
- **前端 CSS**：Spectre.css
- **协议**：HTTP (端口 80)、Modbus RTU (UART1)
- **存储**：MicroPython btree 数据库（键值持久化）

---

## 2. 架构设计

### 2.1 整体架构图

```
┌────────────────────────────────────────────────────────────┐
│                      前端 (Browser)                         │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  设备控制面板    │  │  数据可视化图表  │                │
│  │ (Spectre CSS)    │  │   (Chart.js)      │                │
│  └────────┬─────────┘  └─────────┬─────────┘                │
└───────────┼────────────────────────┼─────────────────────────┘
            │  HTTP GET (每 5 秒轮询) │
            ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Web 服务层 (Microdot)                      │
│  GET /status      GET /scanap     GET /setwifi              │
│  GET /reset       GET /restart    GET /static/*              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  业务逻辑层 (main.py)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 配置管理模块  │  │ 主循环调度器 │  │ 运行模式管理      │  │
│  │ (DBUtils)     │  │ (1s tick)     │  │ normal/config     │  │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬────────┘  │
└─────────┼──────────────────┼────────────────────┼───────────┘
          │                  │                    │
          ▼                  ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  BSP 层 (driver/bsp.py)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ 传感器读取   │  │ PWM 风扇控制  │  │ LED 状态控制     │  │
│  │ (5s 定时器)  │  │ (4 路 PWM)    │  │ (心跳闪烁)       │  │
│  └──────┬───────┘  └──────────────┘  └──────────────────┘  │
└─────────┼───────────────────────────────────────────────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
┌─────────┐  ┌──────────────┐
│ HDC1080 │  │  PM5350P     │
│ (I2C)   │  │ (Modbus RTU) │
└─────────┘  └──────────────┘
```

### 2.2 模块职责划分

| 层级 | 模块 | 文件路径 | 核心职责 |
|-----|------|---------|---------|
| 入口 | 主程序 | `main.py` | 初始化、主循环、HTTP 路由 |
| 应用层 | 配置数据库 | `domain/DBUtils.py` | btree 键值存储 |
| 应用层 | 风扇状态机 | `domain/FanFSM.py` | 温度触发风扇控制 |
| 应用层 | 空气算法 | `domain/AAC.py` | 湿球温度计算 |
| 应用层 | WiFi 管理 | `domain/wifi.py` | WiFi STA/AP 模式 |
| 应用层 | 数学工具 | `domain/MathTool.py` | Modbus 数据类型转换 |
| 应用层 | 传感器数据模型 | `domain/sensorData.py` | 传感器数据封装 |
| 应用层 | 文件工具 | `domain/fileUtils.py` | 文件存在性检查 |
| 驱动层 | BSP | `driver/bsp.py` | 硬件抽象层、传感器定时读取 |
| 驱动层 | PM5350P | `driver/PM5350P.py` | Modbus 寄存器读取 |
| 驱动层 | HDC1080 | `driver/hdc1080.py` | I2C 温湿度驱动 |
| 驱动层 | 预留 | `driver/bmp280.py`, `bh1750.py`, `pms5003.py` | 传感器驱动预留 |
| 第三方库 | Web 框架 | `lib/microdot.py` | HTTP 服务器 |
| 第三方库 | Modbus | `lib/modbus/` | Modbus 协议栈 |
| 前端 | 单页应用 | `static/index.html` | 数据展示与配置界面 |

---

## 3. 核心模块设计

### 3.1 主程序模块 (`main.py`)

#### 3.1.1 启动流程

```
Boot
  │
  ▼
1. 加载系统配置 (DBUtils)
   ├─ 从 btree 读取 systemConfig (JSON 字符串)
   └─ 不存在则使用默认配置
  │
  ▼
2. 初始化 BSP (bspInstance.setConfig)
   ├─ I2C 总线初始化
   ├─ HDC1080 传感器初始化
   ├─ PWM 通道初始化
   ├─ 定时器启动 (5s 读取传感器)
   └─ WS2812 LED 初始化
  │
  ▼
3. 看门狗启动 (WDT, 60s 超时)
   └─ Timer(0) 每 5s 喂狗
  │
  ▼
4. WiFi 模式判断
   ├─ mode == "normal" → 尝试连接 WiFi
   │   ├─ 连接成功 → 启动 IP 广播线程
   │   │   └─ (devicename_192.168.x.x 的 SSID 作为 AP 广播)
   │   └─ 连接失败 → 切换到 config 模式
   └─ mode == "config" → 启动 AP 配置模式
       └─ SSID: PM5350P_<IP>, 密码: Changeme_123
  │
  ▼
5. Web 服务器启动 (独立线程, 端口 80)
  │
  ▼
6. 主循环 (while True, 1s tick)
   ├─ 更新运行时间统计
   ├─ LED 心跳闪烁
   ├─ 每 300 次循环 → GC 垃圾回收
   └─ 每 3600 次循环 → 保存运行时间到数据库
```

#### 3.1.2 运行模式状态机

```
┌─────────────────┐      WiFi 连接失败 / 首次启动      ┌─────────────────┐
│   Normal Mode   │ ◄───────────────────────────────── │   Config Mode   │
│  (正常运行模式) │    配置成功后自动重启进入          │ (AP 配置模式)    │
│  - HTTP 服务     │                                     │  - 启动 AP       │
│  - 数据采集     │                                     │  - Web 配置界面 │
│  - 图表刷新     │                                     │  - 300s 超时重启 │
└─────────────────┘                                     └─────────────────┘
```

#### 3.1.3 关键全局变量

| 变量名 | 类型 | 说明 |
|-------|------|------|
| `systemConfig` | dict | 完整系统配置（JSON 序列化存储到 btree） |
| `defaulteSystemConfig` | dict | 出厂默认配置 |
| `totalRunTime` | int | 累计运行时间（秒，持久化存储） |
| `whenGotoConfigMode` | int | 进入配置模式的时间戳 |
| `bspInstance` | BSP | BSP 单例 |
| `app` | Microdot | Web 应用实例 |

### 3.2 BSP 模块 (`driver/bsp.py`)

#### 3.2.1 硬件抽象

| 资源 | 引脚 | 配置 |
|-----|------|------|
| I2C SCL | IO3 | 100kHz |
| I2C SDA | IO8 | - |
| 独立 LED | IO2 | GPIO 输出，心跳闪烁 |
| WS2812 LED | IO48 | RGB 状态指示 |
| PWM1 (MOS1) | IO46 | 风扇 MOS 管 1 |
| PWM2 (MOS2) | IO9 | 风扇 MOS 管 2 / 转速信号 |
| PWM3 (MOS3) | IO10 | 风扇 MOS 管 3 |
| PWM4 (MOS4) | IO11 | 风扇 MOS 管 4 |
| UART1 TX | IO17 | Modbus RTU 发送 |
| UART1 RX | IO18 | Modbus RTU 接收 |

#### 3.2.2 PWM 占空比计算

BSP 中的 PWM 计算逻辑是项目的核心算法之一：

```
输入参数:
  - percent: 目标百分比 (0~100)
  - config.pwm1freq: PWM 频率 (Hz)
  - config.pwm1min: 最小占空比 (%)
  - config.pwm1max: 最大占空比 (%)

计算过程:
  base = (pwm1min / 100) * pwm1freq           ── 最小占空比对应的时钟周期数
  full = (pwm1max - pwm1min) / 100 * pwm1freq  ── 可调范围
  duty = 1023 * (full * percent/100 + base) / pwm1freq

应用:
  fan1 (IO46): 直接控制 MOS，duty=0 关闭，duty=1023 全开
  fan2 (IO9):  用于转速信号 (PWM 占空比输出)
  fan3 (IO10): 同步控制 MOS
  fan4 (IO11): 预留
```

#### 3.2.3 传感器定时读取

Timer(1) 以 5000ms 周期触发：

```
timerHandler:
  ├─ hdc1080TimerHandler
  │   ├─ 读取温度 (℃)
  │   ├─ 读取相对湿度 (RH%)
  │   └─ 调用 AAC.ts() 计算湿球温度
  │
  └─ pm5350pTimerHandler (当前已注释)
      └─ 读取 PM5350P 寄存器数据
```

### 3.3 湿球温度算法 (`domain/AAC.py`)

#### 3.3.1 算法原理

湿球温度通过迭代法求解：给定干球温度 T 和相对湿度 RH，找到湿球温度 Tw，使得：

```
RH = P_atm * [h_g(Tw) - h_a(T) + d(Tw,100%) * v(Tw)]
     / [e_s(Tw) * (h_g(Tw) - h_a(T) + d(Tw,100%) * v(Tw) + 0.622 * v(T))]

其中:
  e_s(T) = 611.2 * exp(17.67 * T / (243.5 + T))   饱和水汽压 (Pa)
  h_a(T) = 1.01 * T                                干空气焓 (kJ/kg)
  v(T) = 2501 + 1.85 * T                           水汽焓 (kJ/kg)
  d(T, RH) = 0.622 * RH * e_s(T) / (P - RH*e_s(T)) 含湿量 (kg/kg)
  P = 101325 Pa (标准大气压)
```

#### 3.3.2 迭代求解过程

```
ts(T_dry, RH, diff=0.1):
  1. 初始猜测: Tw = T_dry - 5
  2. 循环:
     ├─ 计算 RH_calc = rh(T_dry, Tw)
     ├─ 若 |RH_calc - RH| < diff, 退出
     ├─ 若 RH_calc > RH, Tw -= 0.01
     ├─ 否则 Tw += 0.01
     └─ 超过 10000 次则失败返回 -9999
  3. 返回 round(Tw, 2)
```

### 3.4 PM5350P Modbus 驱动 (`driver/PM5350P.py`)

#### 3.4.1 寄存器映射

| 寄存器起始 | 长度 | 数据类型 | 含义 | JSON 字段 |
|-----------|------|---------|------|----------|
| 3000 | 2 (float32) | A 相电流 | `Ia` | A |
| 3002 | 2 | float32 | B 相电流 | `Ib` | A |
| 3004 | 2 | float32 | C 相电流 | `Ic` | A |
| 3006 | 2 | float32 | N 相电流 | `In` | A |
| 3008 | 2 | float32 | G 相电流 | `Ig` | A |
| 3010 | 2 | float32 | 平均电流 | `Iavg` | A |
| 3020 | 2 | float32 | AB 线电压 | `Vab` | V |
| 3022 | 2 | float32 | BC 线电压 | `Vbc` | V |
| 3024 | 2 | float32 | CA 线电压 | `Vca` | V |
| 3028 | 2 | float32 | A 相电压 | `Van` | V |
| 3054 | 2 | float32 | 总功率 | `Ptotal` | kW |
| 3078 | 2 | float32 | 总功率因数 | `PFtotal` | - |
| 3110 | 2 | float32 | 频率 | `Freq` | Hz |
| 3200 | 4 (int64) | 电能复位时间 | `ErestTime` | - |
| 3204 | 4 | int64 | 总有功电能 | `Eaed` | Wh |

#### 3.4.2 字节序处理

Modbus 寄存器为大端 (Big-Endian)，使用 `struct.unpack('>f')` 解析 float32，`struct.unpack('>q')` 解析 int64。在 `domain/MathTool.py` 中封装实现。

### 3.5 数据库模块 (`domain/DBUtils.py`)

使用 MicroPython 内置的 `btree` 模块实现键值存储，底层是文件系统上的单个文件。

| 键 | 值格式 | 说明 |
|----|--------|------|
| `systemConfig` | JSON 字符串 | 完整系统配置字典 |
| `totalRunTime` | 字符串数字 | 累计运行时间（秒） |

---

## 4. 系统配置设计

### 4.1 默认配置 (`defaulteSystemConfig`)

```json
{
    "deviceusername": "admin",
    "devicepwd": "pengping",
    "devicetype": "NodeMCU",
    "devicename": "PM5350P",
    "mode": "normal",

    "APName": "PM5350P",
    "APPwd": "Changeme_123",

    "wifiname": "cissco_2g",
    "wifipwd": "13438045703",
    "wifinameDefault": "IOT_2G",
    "wifipwdDefault": "13438045703",

    "serverurl": "192.168.1.124",
    "serverurlDefault": "http://3a892544f7.qicp.vip",

    "latitude": 30.67831,
    "longitude": 104.0375,
    "altitude": 498,

    "sw1name": "S1",
    "sw2name": "S2",
    "num1name": "Tree temprature",
    "num2name": "Tree humidity",
    "rangename": "Tree light",

    "pwm1freq": 25000,
    "pwm1default": 0,
    "pwm1min": 15,
    "pwm1max": 100,
    "pwm2freq": 25000,
    "pwm2default": 0,
    "pwm2min": 15,
    "pwm2max": 100,
    "pwm3freq": 25000,
    "pwm3default": 0,
    "pwm3min": 15,
    "pwm3max": 100,
    "pwm4freq": 25000,
    "pwm4default": 0,
    "pwm4min": 15,
    "pwm4max": 100,

    "fanHThreshold": 36,
    "fanLThreshold": 31.5,

    "modbusSlaveAddr": 6,
    "modbusBadud": 38400
}
```

### 4.2 配置字段说明

| 字段 | 类型 | 可在线修改 | 说明 |
|-----|------|-----------|------|
| `fanHThreshold` | float | 是 | 风扇全速阈值温度 (℃) |
| `fanLThreshold` | float | 是 | 风扇启动阈值温度 (℃) |
| `pwm1freq` | int | 是 | PWM 通道 1 频率 (Hz) |
| `pwm1min` | int | 是 | PWM 最小占空比 (%) |
| `pwm1max` | int | 是 | PWM 最大占空比 (%) |
| `sw1` / `sw2` | bool | 是 | 开关 1/2 状态 |
| `wifiname` / `wifipwd` | string | 否 (需重启) | WiFi 凭据 |
| `mode` | string | 否 (需重启) | `normal` / `config` |

---

## 5. Web API 接口设计

### 5.1 接口总览

| 路径 | 方法 | 鉴权 | 说明 |
|-----|------|------|------|
| `/` | GET | 否 | 返回主页 HTML |
| `/static/*` | GET | 否 | 静态资源 (CSS/JS/图标) |
| `/status` | GET | 是 (`devicepwd`) | 获取状态 / 修改参数 |
| `/scanap` | GET | 否 | 扫描附近 WiFi |
| `/setwifi` | GET | 否 | 配置 WiFi 并重启 |
| `/reset` | GET | 是 | 恢复出厂配置 |
| `/restart` | GET | 是 | 重启设备 |

### 5.2 `/status` 接口

**请求查询状态 (`mode=get`)**

```
GET /status?mode=get&devicepwd=pengping
```

**响应 (errCode=0)**

```json
{
    "errCode": "0",
    "mode": "normal",
    "sw1": true,
    "sw2": false,

    "devicename": "PM5350P",
    "devicepwd": "pengping",
    "deviceusername": "admin",

    "fanHThreshold": 36,
    "fanLThreshold": 31.5,
    "pwm1freq": 25000,
    "pwm1min": 15,
    "pwm1max": 100,

    "temp": 28.45,
    "humi": 51.13,
    "wetBulbTemp": 20.87,
    "presure": -9999,
    "luminance": -9999,
    "pm25": -9999,

    "Ia": 10.5,
    "Ib": 11.2,
    "Ic": 10.8,
    "In": 0.2,
    "Iavg": 10.83,
    "Vab": 220.5,
    "Vbc": 221.0,
    "Vca": 219.8,
    "Ptotal": 5.5,
    "PFtotal": 0.95,
    "Freq": 50.02,
    "Eaed": 1234567,

    "runTime": 52903,
    "totalRunTime": 179257,
    "ver": "1.1"
}
```

> **无效值约定**：传感器未连接时返回 `-9999`，前端据此判断是否显示有效数据。

**请求修改参数 (`mode=set`)**

```
GET /status?mode=set&devicepwd=pengping
    &fanHThreshold=38
    &fanLThreshold=32
    &pwm1freq=25000
    &pwm1min=15
    &pwm1max=100
    &sw1=true
    &sw2=false
```

**成功响应**：`{"errCode": "0", "msg": "set finish."}`

**失败响应**：`{"errCode": "-1", "msg": "invalid device password."}`

### 5.3 `/scanap` 接口

```
GET /scanap
```

返回附近 WiFi SSID 列表及 RSSI：

```json
{
    "cissco_2g": -58,
    "IOT_2G": -72,
    "TP-LINK-Office": -65
}
```

### 5.4 `/setwifi` 接口

```
GET /setwifi?ssid=MyWiFi&pwd=secret
    &serverurl=192.168.1.1&devicepwd=pengping
    &devicename=PM5350P&sw1name=Fan&sw2name=Pump
```

- 成功 → 保存配置 → 等待 5 秒 → 自动重启
- 重启后尝试以 `normal` 模式连接新 WiFi

### 5.5 `/reset` 与 `/restart` 接口

```
GET /reset?devicepwd=pengping      → 恢复出厂配置 + 重启
GET /restart?devicepwd=pengping    → 仅重启
```

---

## 6. 前端架构设计 (`static/index.html`)

### 6.1 架构模式

前端采用**工厂模式 + 模块化**组织，避免使用 ES6 class（保证兼容性）。

```
App 初始化 (document.ready)
  │
  ├─ createDeviceData()           ── 设备数据模型（JSON 解析）
  ├─ createDataBuffer(350)        ── 数据环形缓冲区（350 点 ≈ 29 分钟）
  │
  ├─ createChartManager('monitorChart').init()  ── Chart.js 图表
  │
  ├─ Views:
  │   ├─ createSensorView()       ── 传感器数值显示
  │   ├─ createControlView()      ── 开关状态
  │   ├─ createSettingsView()     ── 阈值/PWM 设置
  │   └─ createDeviceInfoView()   ── 设备名称/服务器信息
  │
  ├─ createRefreshController(...) ── 5 秒轮询调度
  └─ createEventController(...)   ── 按钮点击事件

刷新循环:
  ┌─────────────────────────────────────────────┐
  │  setInterval(5000ms):                        │
  │    └─ refresh()                              │
  │       ├─ GET /status?mode=get                │
  │       ├─ deviceModel.update(resJson)         │
  │       ├─ 各 view.update(deviceModel)         │
  │       ├─ dataBuffer.add(resJson)             │
  │       ├─ plotData = dataBuffer.getPlotData() │
  │       └─ chart.updatePlotData(plotData)      │
  └─────────────────────────────────────────────┘
```

### 6.2 数据缓冲机制 (`createDataBuffer`)

- 固定大小环形缓冲区（350 条 = 5s × 350 ≈ 29.2 分钟）
- 满后丢弃最旧数据（`buffer.shift()`），追加最新数据
- 每次 `getPlotData()` 从最后一条数据读取阈值（因为阈值是配置常量，不随时间变化）
- 传感器值 `-9999` 映射为 `undefined`（Chart.js 自动跳过断点）

### 6.3 图表数据集

| 数据集 | 标签 | 颜色 | 数据源 | 初始可见 |
|-------|------|------|--------|---------|
| 0 | 温度 | rgb(75, 132, 192) | 缓冲 temp[] | 是 |
| 1 | 湿度 | rgb(175, 92, 192) | 缓冲 humi[] | 否 (hidden) |
| 2 | 功率 | rgb(175, 92, 92) | Ptotal (最新值) | 是 |
| 3 | 高阈值 | rgb(255, 0, 0) | fanHThreshold (配置值) | 是 |
| 4 | 低阈值 | rgb(0, 255, 0) | fanLThreshold (配置值) | 是 |

### 6.4 刷新调度逻辑

```
shouldRefresh() = !isEditing && !hasPendingRequest && !isUserEditing()

isUserEditing(): 检测当前焦点是否在 input/textarea 中，避免用户输入被刷新覆盖
```

---

## 7. 稳定性与异常处理

### 7.1 看门狗机制

```
machine.WDT(timeout=60000)        ── 60 秒不喂狗触发硬重启
Timer(0).init(period=5000)         ── 每 5 秒喂狗一次
```

### 7.2 配置模式超时

- 进入 AP 配置模式后，创建 Timer(3) 每 10 秒检查
- 超过 300 秒（5 分钟）仍在配置模式 → 自动重启
- 任何 HTTP 请求都会重置 `whenGotoConfigMode`，保证配置时不超时

### 7.3 Modbus 通信异常

Modbus 读取失败时返回空对象 `{}`，上层忽略本次数据，不阻塞系统运行。

### 7.4 传感器无效值

- 传感器读取失败 / 未连接时返回 `-9999`
- 前端检测到 `-9999` → 显示默认值 `----`
- 图表中映射为 `undefined` → 该点不绘制

---

## 8. 目录结构

```
PM5350PMonitor4ESP32S3/
├── main.py                    # 主程序（启动、主循环、Web 路由）
├── boot.py                    # 启动脚本（目前为空）
│
├── domain/                    # 业务逻辑层
│   ├── DBUtils.py             # btree 数据库封装
│   ├── AAC.py                 # 湿球温度算法
│   ├── FanFSM.py              # 风扇状态机（当前 main.py 未引用）
│   ├── wifi.py                # WiFi STA/AP 管理
│   ├── sensorData.py          # 传感器数据模型
│   ├── MathTool.py            # Modbus 数据类型转换
│   ├── fileUtils.py           # 文件工具
│   └── getFsInfo.py           # 文件系统信息工具
│
├── driver/                    # 驱动层
│   ├── bsp.py                 # 板级支持包（PWM/LED/定时器）
│   ├── PM5350P.py             # 施耐德电力仪表驱动
│   ├── hdc1080.py             # HDC1080 温湿度驱动
│   ├── bmp280.py              # 气压计驱动（预留）
│   ├── bh1750.py              # 照度计驱动（预留）
│   ├── pms5003.py             # PM2.5 传感器驱动（预留）
│   ├── SHT20.py               # SHT20 驱动（预留）
│   ├── co2Sensor.py           # CO2 驱动（预留）
│   ├── enumSysStatus.py       # 系统状态枚举（预留）
│   └── enumEV.py              # 事件枚举（预留）
│
├── lib/                       # 第三方库
│   ├── microdot.py            # Microdot Web 框架
│   └── modbus/                # Modbus 协议栈
│       ├── uModBusConst.py
│       ├── uModBusFunctions.py
│       ├── uModBusSerial.py
│       └── uModBusTCP.py
│
├── static/                    # Web 前端资源
│   ├── index.html             # 单页应用（HTML + CSS + JS 一体）
│   ├── chart.umd.js           # Chart.js (V4)
│   ├── spectre.min.css        # Spectre CSS 框架
│   ├── jquery.min.js          # jQuery (用于 DOM/HTTP 请求)
│   └── favicon.ico            # 网站图标
│
├── Doc/                       # 硬件资料
├── firmware/                  # MicroPython 固件
├── testfile/                  # 测试脚本与测试数据
└── DESIGN_DOC.md              # 本文档
```

---

## 9. 已知实现细节与注意事项

### 9.1 `FanFSM.py` 未被主程序引用

项目中实现了完整的风扇状态机（温度触发的自动转速控制），但 `main.py` 并未实例化和调用它。当前风扇由前端手动通过 PWM 参数设置控制。如需启用自动温控风扇，需在 `main.py` 中添加：

```python
import domain.FanFSM as FanFSM
fanFSM = FanFSM.FSM(bspInstance, systemConfig)
# 然后在主循环中调用 fanFSM.run()
```

### 9.2 PM5350P 读取定时器被注释

`driver/bsp.py:timerHandler` 中 `self.pm5350pTimerHandler(timer)` 被注释掉了，意味着电力数据仅在前端请求时由 `/status` 接口中的 `bspInstance.readPm5350p()` 实时读取，不会自动更新到 BSP 内部缓存。

### 9.3 线程安全性

- Web 服务器运行在独立线程中（`_thread.start_new_thread`）
- 数据库操作在 Web 线程和主线程中都可能发生，存在并发风险
- 实际运行中由于 MicroPython GIL 和操作频率低，通常可正常工作

### 9.4 IP 广播机制

正常模式下，系统会同时启动一个隐藏的 AP，SSID 为 `设备名_IP地址`（如 `PM5350P_192.168.1.100`），方便用户发现设备的 IP。

### 9.5 HTTP 鉴权

- `/status`、`/reset`、`/restart` 需要 `devicepwd` 参数
- 默认密码 `pengping`
- 密码错误返回 `errCode: "-1"`

---

## 10. 版本信息

| 项目 | 版本 |
|-----|------|
| 设备固件版本 | 1.1 (systemConfig.ver) |
| MicroPython | ESP32-S3-SPIRAM-OCT |
| Modbus 地址 | 6 (可配置) |
| Modbus 波特率 | 38400 (可配置) |
