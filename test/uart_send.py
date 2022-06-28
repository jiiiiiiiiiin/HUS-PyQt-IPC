import serial
import time


class LowerMachine:
    def __init__(self, uart_id, baud_rate):
        self.uart = serial.Serial(uart_id, baud_rate, timeout=0.5)
        # self.ser.open()

        # 【帧头， 上位机地址， 下位机地址， 功能帧， 长度帧， ...数据...， 校验位， 帧尾】
        self.data_head = 0xAA  # 帧头
        self.data_end = 0xBB  # 帧尾
        self.data_target = 0x01  # 下位机发送的目标设备地址
        self.data_source = 0x01  # 下位机地址

        self.BYTE1 = lambda x: (int(x) >> 8) & 0xff
        self.BYTE2 = lambda x: (int(x) >> 0) & 0xff

        self.bin16ToInt = lambda x: x if x < 0x8000 else x - 0x10000
        self.bin32ToInt = lambda x: x if x < 0x80000000 else x - 0x100000000

    def send(self, func, values):
        length = len(values) * 2 + 7
        data = [
            self.data_head,
            self.data_target,
            self.data_source,
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

        self.uart.write(bytes(data))
        return data

    def send_circuit(self, source, vin, iin, uo, io):
        # source : for example: PV:0x01
        return self.send(0x01, [source, vin, iin, uo, io])

    def send_text(self, content, color='green'):
        content_bytes = bytes(content + '//' + color, encoding='utf-8')
        return self.send(0xA1, content_bytes)


def analysis(data):
    # 【帧头， 上位机地址， 下位机地址， 功能帧， 长度帧， ...数据...， 校验位， 帧尾】
    head, target, source, func, length = data[0:5]
    s = data[-2]
    end = data[-1]

    if head == 0xAA and target == source == 0x01 and end == 0xBB:
        print("解析成功")
    else:
        print("失败")
        return None

    bin16ToInt = lambda x: x if x < 0x8000 else x - 0x10000

    data_s = data[-2]
    data = data[5:-2]
    print("接受数据", data)

    s = 0
    for i in range(len(data) // 2):
        s += data[i * 2] + data[i * 2 + 1]

    if s % 256 == data_s:
        print("校验成功")


    tmp = []
    for i in range(len(data) // 2):
        tmp.append(int(bin16ToInt((data[i * 2] << 8) | data[i * 2 + 1]) / 100))

    if func == 0x01:
        print(tmp)

    elif func == 0xA1:
        tmp = str(bytes(tmp), 'utf-8')
        color = tmp.split('//')[-1]
        string = tmp[0:len(tmp) - len(color) - 2]
        print(string, color)



if __name__ == '__main__':
    import math

    lower_machine = LowerMachine("com2", 500000)
    # for i in range(10):
    #     d = lower_machine.send_text("陈玮*////green {}".format(i), color='pink')
    # analysis(d)
    i = 0
    while True:
        lower_machine.send(0x04, [i] * 8)
        i += 1
        i %= 101
        time.sleep(0.1)
    # while True:
    #     for i in range(50):
    #         # lower_machine.send_circuit()
    #         lower_machine.send_circuit(2, -30+i, i, 15+i, 2*i)
    #         lower_machine.send_circuit(1, -10+i, i, 15+i, 2*i)
    #         time.sleep(0.05)
