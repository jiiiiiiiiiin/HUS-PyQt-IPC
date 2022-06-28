"""
通信协议 - Qt版本
"""

from PyQt5.QtCore import QThread
from PyQt5.QtSerialPort import QSerialPort
import time


class ReceiveFlag(object):
    uart_buf = []
    _data_len = 0
    _data_cnt = 0
    state = 0
    _tmp_i = 0


class Protocol(QThread):
    def __init__(self, basic_info, uart: QSerialPort):
        super(Protocol, self).__init__()
        self.receive_flag = ReceiveFlag()
        self.uart = uart
        self.buffer = []

        self.add_upper = basic_info.ADDRESS_UPPER
        self.add_lower = basic_info.ADDRESS_LOWER
        self.data_head = basic_info.DATA_HEAD
        self.data_end = basic_info.DATA_END
        self.check = basic_info.CHECK

        # thread flag
        self.flag_stop = False

        # 误码率计算
        self.receive_correct = 1
        self.receive_error = 0
        self.receive_correct_rate = 1

        # COUNT
        self.count_receive = 0
        self.count_send = 0

        self.BYTE1 = lambda x: (int(x) >> 8) & 0xff
        self.BYTE2 = lambda x: (int(x) >> 0) & 0xff
        self.bin16ToInt = lambda x: x if x < 0x8000 else x - 0x10000
        self.bin32ToInt = lambda x: x if x < 0x80000000 else x - 0x100000000

    def run(self):
        while True:
            time.sleep(0.0001)
            if self.flag_stop:
                break
            buffer_length = len(self.buffer)
            if buffer_length != 0:
                buff = self.buffer.pop(0)
                for i in buff:
                    self.count_receive += 1
                    self.receive_prepare(i)

    def receive_prepare(self, data):
        """
        串口通信协议接收 - 状态机
        【帧头， 上位机地址， 下位机地址， 功能帧， 长度帧， ...数据...， 校验位， 帧尾】
        :param data:
        :return: None
        """
        self.receive_correct_rate = self.receive_correct / (self.receive_error + self.receive_correct)
        if self.receive_flag.state == 0:
            self.receive_flag.uart_buf = []  # 清空缓冲区，准备下次接收数据
            if data == self.data_head:  # 帧头
                self.receive_flag.uart_buf.append(data)  # 0
                self.receive_flag.state = 1
            else:
                self.receive_flag.state = -1

        elif self.receive_flag.state == 1:  # 上位机地址
            if data == self.add_upper:
                self.receive_flag.uart_buf.append(data)  # 1
                self.receive_flag.state = 2
            else:
                self.receive_flag.state = -1

        elif self.receive_flag.state == 2:  # 下位机地址
            if data == self.add_lower:
                self.receive_flag.uart_buf.append(data)  # 2
                self.receive_flag.state = 3
            else:
                self.receive_flag.state = -1

        elif self.receive_flag.state == 3:  # 功能字
            if data < 0xFF:
                self.receive_flag.state = 4
                self.receive_flag.uart_buf.append(data)  # 3 功能
            else:
                self.receive_flag.state = -1

        elif self.receive_flag.state == 4:  # 数据个数
            if data < 0xFF:
                self.receive_flag.state = 5
                self.receive_flag.uart_buf.append(data - 7)  # 4 数据个数
                self.receive_flag._data_len = data - 7
                # print("数据长度", data)
            else:
                self.receive_flag.state = -1

        elif self.receive_flag.state == 5:  # 数据
            self.receive_flag._tmp_i += 1
            self.receive_flag.uart_buf.append(data)
            if self.receive_flag._tmp_i == self.receive_flag._data_len:
                self.receive_flag._tmp_i = 0
                self.receive_flag.state = 6

        elif self.receive_flag.state == 6:  # 校验位
            self.receive_flag.state = 7
            self.receive_flag.uart_buf.append(data)

        elif self.receive_flag.state == 7:  # 帧尾
            if data == self.data_end:  # 帧头
                self.receive_flag.uart_buf.append(data)  # 0
                self.receive_analyse(self.receive_flag.uart_buf)
                self.receive_correct += 1
                self.receive_flag.uart_buf = []  # 清空缓冲区，准备下次接收数据

            self.receive_flag.state = 0

        else:
            self.receive_flag.state = 0

        if self.receive_flag.state == -1:
            #  接受错误
            self.receive_error += 1
            self.receive_flag.state = 0

    def receive_analyse(self, data_buf):
        #  数据分析
        func, length = data_buf[3:5]

        # 校验
        data_s = data_buf[-2]
        tmp_s = 0
        if self.check:
            for i in range(length):
                tmp_s += data_buf[i + 5]
            if tmp_s % 256 == data_s:
                self.receive_error = 0
            else:
                return None

        # 数据合成
        data = []
        for i in range(length // 2):
            data.append(self.bin16ToInt((data_buf[i * 2 + 5] << 8) | data_buf[i * 2 + 6]) / 100)
        # print(data)
        try:
            self.receive(func, data)
        except Exception as e:
            print("error")

    def send_bytes(self, d):
        self.uart.write(d)
        self.count_send += len(d)

    def _send(self, func, values):
        length = len(values) * 2 + 7
        data = [
            self.data_head,
            self.add_upper,
            self.add_lower,
            func,
            length
        ]
        s = 0
        for value in values:
            b1, b2 = self.BYTE1(value * 100), self.BYTE2(value * 100)
            data.append(b1)
            data.append(b2)
            s += b1 + b2
        s %= 256
        data.append(s)
        data.append(self.data_end)

        self.send_bytes(bytes(data))
        return data

    def receive(self, func, data):
        #  这里用户自定义数据处理过程
        pass
