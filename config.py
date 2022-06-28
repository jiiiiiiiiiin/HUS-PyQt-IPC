from utils import protocol
from PyQt5.QtSerialPort import QSerialPort
import time

about = """
    学校：南京工程学院 - 电力工程学院
    作者：陈玮
    班级：电力181
    学号：206180121
    毕设：混合动力无人船能源系统电源功率调度策略研究与实践
"""

tips = """
    1. 光伏、DCDC1、DCDC2的输出电流都是通过 “输入电压 * 输入电流 / 输出电压” 计算得出，只具有参考意义。
    2. 数据默认保存之‘record’文件夹中，使用数据库软件可打开。
    3. 使用 com.readyRead 接受数据，使用 QThread 来解析数据（基本同步解析）。
    4. 不能实时写入数据库，频繁的IO操作对导致解析很慢。
    5. ‘protocol.py'为串口解析程序，可以在’config.py‘中自定义通信协议。
"""


class Config:
    graph_x = 50
    graph_y = 100


class BasicInfo:
    ADDRESS_UPPER = 0x01  # 上位机
    ADDRESS_LOWER = 0x01  # 下位机
    DATA_HEAD = 0XAA  # 帧头
    DATA_END = 0XBB  # 帧尾

    CHECK = False  # 是否进行校验


class UART(protocol.Protocol):
    def __init__(self, my_log, uart: QSerialPort):
        super().__init__(BasicInfo(), uart)
        self.cnt = 0
        self.my_log = my_log
        self.data = {
            0x01: {
                "pv_input_voltage": [0],
                "pv_input_current": [0],
                "pv_output_voltage": [0],
                "pv_output_current": [0],
            },
            0x02: {
                "dcdc1_input_voltage": [0],
                "dcdc1_input_current": [0],
                "dcdc1_output_voltage": [0],
                "dcdc1_output_current": [0]
            },
            0x03: {
                "dcdc2_input_voltage": [0],
                "dcdc2_input_current": [0],
                "dcdc2_output_voltage": [0],
                "dcdc2_output_current": [0]
            },
            0x04: {
                "battery_voltage": [0],
                "battery_soc": [0]
            }
        }
        self.heart = [time.time()]
        self.pwm_value = [0, 0, 0]
        self.rc_value = [50] * 8
        self.rc_value[0] = 20
        self.count_receive = 163513

        self.order_start = 0xB1
        self.order_stop = 0xB2
        self.order_calibration_voltage = 0xB3
        self.order_read_parameter = 0xB4
        self.order_mpptWork = 0xB5
        self.order_clibRC = 0xB6
        self.order_dcdcWord = 0xB7

        self.clear_data()

    def receive(self, func, data_r):
        if func == 0x01:  # pv/dcdc/battery - 电压电流数据
            rd_index = int(data_r[0])
            rd_values = data_r[1:]

            keys = list(self.data[rd_index].keys())

            if len(keys) == len(rd_values):
                for index, i in enumerate(keys):
                    self.data[rd_index][i].append(rd_values[index])

        elif func == 0x02:  # pwm
            index, value = data_r
            self.pwm_value[int(index)] = value

        elif func == 0x03:  # 参数读取接受
            pass

        elif func == 0x04:  # 遥控数据
            # print(data_r)
            self.rc_value = data_r
        elif func == 0x05:
            self.heart.append(time.time())
        elif func == 0xA1:  # 字符串数据
            data_r = list(map(int, data_r))
            data_r = str(bytes(data_r), 'utf-8')
            data_color = data_r.split('//')[-1]
            data_string = data_r[0:len(data_r) - len(data_color) - 2]
            self.my_log.mcu(data_string, data_color)

        elif func > 0xB0:
            self.my_log.mcu("指令接受成功，指令代码：{}".format(hex(func)))
        else:
            pass

    def send_order(self, order, value=None):
        if value is None:
            value = [0x00, 0x00]
        self._send(order, value)
        self.my_log.system("指令发送成功，指令代码：{}".format(hex(order)))

    def clear_data(self):
        self.data = {
            0x01: {
                "pv_input_voltage": [0],
                "pv_input_current": [0],
                "pv_output_voltage": [0],
                "pv_output_current": [0],
            },
            0x02: {
                "dcdc1_input_voltage": [0],
                "dcdc1_input_current": [0],
                "dcdc1_output_voltage": [0],
                "dcdc1_output_current": [0]
            },
            0x03: {
                "dcdc2_input_voltage": [0],
                "dcdc2_input_current": [0],
                "dcdc2_output_voltage": [0],
                "dcdc2_output_current": [0]
            },
            0x04: {
                "battery_voltage": [0],
                "battery_soc": [0]
            }
        }
        self.heart = [time.time()]
        self.count_receive = 0
        self.count_send = 0
        self.my_log.system("数据清空完毕")
