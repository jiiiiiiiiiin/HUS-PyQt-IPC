# 混合动力无人船 - 上位机


1. 光伏、DCDC1、DCDC2的输出电流都是通过 “输入电压 * 输入电流 / 输出电压” 计算得出，只具有参考意义。
2. 数据默认保存之‘record’文件夹中，使用数据库软件可打开。
3. 使用 com.readyRead 接受数据，使用 QThread 来解析数据（基本同步解析）。
4. 不能实时写入数据库，频繁的IO操作对导致解析很慢。
5. 数据使用csv格式保存，可以方便使用Matlab进行数据分析。

## 目录说明

- main.py 主文件
- pic_rc.py 资源文件
- hus.py ui文件
- config.py 配置文件、串口协议
- run.bat 直接运行
- requirements.txt
- utils
    - log.py 日志
    - protocol.py 串口解析程序 - 同communication.py
    - db.py 数据库文件 - 暂时没用
- test
    - uart_test.py 串口测试（发送、接受）
    - communication.py 分别为qt版、micropython版的通信协议。
- static
    - 资源文件
- log
    - 输出日志
- record
    - 保存的数据

## 协议说明

> 【帧头， 上位机地址， 下位机地址， 功能帧， 长度帧， ...数据...， 校验位， 帧尾】

- 帧头：`0xAA`
- 上位机地址：`0x01`
- 下位机地址：`0x01`
- 功能帧：见下方
- 长度帧：长度为 ` 7 + len(数据)`
- 数据：见下方
- 校验位：见下方
- 帧尾：`0xBB`

> 功能帧

| 功能帧 |    说明（所有数据发送时都乘以100，接收到后需要除以100）     |
| :----: | :---------------------------------------------------------: |
|  0x01  |           发送太阳能板、DCDC、电池的电压电流信息            |
|        |          数据组成：数据ID/电压V/电流A/电压V/电流A           |
|        |           ID 1: MPPT,2: DCDC1,3: DCDC2,4: BATTERY           |
|  0x02  | 发送PWM占空比 数据ID + value ；ID:1 PV ID:2 DCDC1 ID3:DCDC2 |
|  0x03  |                        参数读取接受                         |
|  0x04  |                          遥控数据                           |
|  0x05  |                  心跳包  500ms 超过5s报警                   |
|  0xA1  |                         发送字符串                          |
|        |                 string = str(byte, 'utf-8')                 |
|   -    |                              -                              |
|        |                 上位机发送至下位机 - 带反馈                 |
|  0xB1  |                        发送启动命令                         |
|  0xB2  |                        发送停机命令                         |
|  0xB3  |                      发送校准电压命令                       |
|  0xB4  |                      发送参数读取命令                       |
|        |        发送参数修改命令 发送数据由 参数名 参数值组成        |
|  0xB5  |                MPPT工作指令 1：工作 0：断开                 |
|  0xB6  |                       遥控器校准行程                        |
|  0xB7  |                DC/DC工作指令 1：工作 0：断开                |
|        |                                                             |

> 数据

```python
# 下位机通过一下两行将数据拆分
BYTE1 = lambda x: (x >> 8) & 0xff
BYTE2 = lambda x: (x >> 0) & 0xff

#  上位机通过以下将数据合成
bin16ToInt = lambda x: x if x < 0x8000 else x - 0x10000
bin32ToInt = lambda x: x if x < 0x80000000 else x - 0x100000000
```

> 校验

将`数据`求和后取余

```python
data = []  # 拆分后的数据
s = 0  # 求和后的s即为校验位
for i in data:
    s += i
s %= 256
```