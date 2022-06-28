import sys
import os
import binascii
import re
import hus
import config
import pyqtgraph as pg
import argparse
import time
from utils import log, dataSave
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QLabel
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtGui import QIcon, QFont
from PyQt5 import QtCore


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(QMainWindow, self).__init__(parent)
        self.ui = hus.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon("static/ico.ico"))

        # 创建实例
        self.com = QSerialPort()  # Qt 串口类
        self.my_log = log.Log(self.ui.textEdit_log, self.ui.statusBar, is_save=False)  # 输出日志
        self.my_config = config.Config()  # 配置项
        self.my_uart = config.UART(self.my_log, self.com)  # 串口类

        self.timer = QtCore.QTimer(self)  # 初始化一个定时器
        self.set_pg()  # 设置graph

        # 丢一个label到statusBar中
        self.label_cnt = QLabel(self)  # status 中显示发送接受数据
        self.ui.statusBar.addPermanentWidget(self.label_cnt)

        # 设置信号/槽
        self.ui_create_signal_slot()

        # 标志位
        self.flag_connect = False
        self.flag_showData = False
        self.flag_showWarning = False

        # 初始化
        self.com_get()  # 刷新串口
        self.checkbox_change()  # checkbox数据到标志位
        self.show_data()

        self.my_log.system("上位机初始化成功。")

    def ui_create_signal_slot(self):
        self.ui.pushButton_connect.clicked.connect(self.com_connect)  # 连接按钮点击
        self.ui.pushButton_refresh.clicked.connect(self.com_get)
        self.ui.pushButton_data_send.clicked.connect(self.com_send)  # 发送数据按钮点击
        self.ui.checkBox_receive_data_show.stateChanged.connect(self.checkbox_change)  # checkbox数据到标志位
        self.ui.checkBox_saveLog.stateChanged.connect(self.checkbox_change)  # checkbox数据到标志位
        self.ui.checkBox_set_window.stateChanged.connect(self.checkbox_change)  # checkbox数据到标志位
        self.ui.action_about.triggered.connect(lambda: QMessageBox.about(self, "关于", config.about))
        self.ui.action_tips.triggered.connect(lambda: QMessageBox.about(self, "说明", config.tips))
        self.ui.pushButton_parameter_read.clicked.connect(
            lambda: self.my_uart.send_order(self.my_uart.order_read_parameter))
        self.ui.pushButton_set_cleanLog.clicked.connect(lambda: self.file_clean("log"))
        self.ui.pushButton_set_cleanDatabase.clicked.connect(lambda: self.file_clean("record"))
        self.ui.pushButton_saveData.clicked.connect(
            lambda: dataSave.write_data(self.my_uart.data, f"record/{self.my_log.get_time('数据保存成功')}")
        )  # 保存接受数据
        self.ui.pushButton_clearData.clicked.connect(self.my_uart.clear_data)

        self.com.readyRead.connect(self.com_receive)  # 接收数据
        self.timer.timeout.connect(self.show_data)  # 计时结束调用operate()方法

        self.ui.pushButton_start.clicked.connect(lambda: self.my_uart.send_order(self.my_uart.order_start))
        self.ui.pushButton_stop.clicked.connect(lambda: self.my_uart.send_order(self.my_uart.order_stop))
        self.ui.pushButton_clibRC.clicked.connect(lambda: self.my_uart.send_order(self.my_uart.order_clibRC))
        self.ui.pushButton_calibration_voltage.clicked.connect(
            lambda: self.my_uart.send_order(self.my_uart.order_calibration_voltage)
        )
        self.ui.checkBox_mpptWork.stateChanged.connect(
            lambda: self.my_uart.send_order(self.my_uart.order_mpptWork, [int(self.ui.checkBox_mpptWork.isChecked())])
        )
        self.ui.checkBox_dcdcWork.stateChanged.connect(
            lambda: self.my_uart.send_order(self.my_uart.order_dcdcWord, [int(self.ui.checkBox_dcdcWork.isChecked())])
        )

    def keyPressEvent(self, event):  # 重新实现了keyPressEvent()事件处理器。
        # 按住键盘事件
        # 这个事件是PyQt自带的自动运行的，当我修改后，其内容也会自动调用
        if event.key() == QtCore.Qt.Key_Escape:  # 当我们按住键盘是esc按键时
            self.close()  # 关闭程序

    def closeEvent(self, evt):
        self.com.close()
        evt.accept()

    def set_pg(self):
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')

        pg.setConfigOptions(antialias=True)
        pen_red = pg.mkPen(color=(255, 78, 0), width=1)  # Red: 255 78 0
        pen_blue = pg.mkPen(color=(0, 128, 255), width=1)  # Blue: 0 128 255
        pen_purple = pg.mkPen(color=(135, 0, 191), width=1)  # Purple: 135 0 191
        pen_yellow = pg.mkPen(color=(255, 212, 0), width=1)  # Yellow 255 212 0
        font = QFont()
        font.setFamily("Microsoft YaHei")

        # 1
        self.plotWidget_pv = pg.PlotWidget()  # 实例化一个绘图部件
        self.plotWidget_pv.setStyleSheet("")
        self.plotWidget_pv.setObjectName("plotWidget_pv")
        self.plotWidget_pv.setXRange(min=0, max=self.my_config.graph_x, padding=0)
        # self.plotWidget_pv.setYRange(min=0, max=self.my_config.graph_y, padding=0)
        self.ui.verticalLayout_graph.addWidget(self.plotWidget_pv)  # 添加绘图部件到网格布局层
        self.plotWidget_pv.setLabel('bottom', 'CNT', **{'font-family': 'Microsoft YaHei'})
        self.plotWidget_pv.setLabel('left', 'Value', **{'font-family': 'Microsoft YaHei'})
        self.plotWidget_pv.setTitle("PV", **{'font-family': 'Microsoft YaHei'})
        item = self.plotWidget_pv.getPlotItem()
        item.titleLabel.item.setFont(font)
        # 设置刻度字体
        self.plotWidget_pv.getAxis("bottom").setStyle(tickFont=font)
        self.plotWidget_pv.getAxis("left").setStyle(tickFont=font)

        self.curve_1 = self.plotWidget_pv.plot(name="Input Voltage", pen=pen_red)
        self.curve_2 = self.plotWidget_pv.plot(name="Input Current", pen=pen_blue)
        self.curve_3 = self.plotWidget_pv.plot(name="Output Voltage", pen=pen_purple)
        self.curve_4 = self.plotWidget_pv.plot(name="Output Current", pen=pen_yellow)

        # 2
        self.plotWidget_dcdc1 = pg.PlotWidget()  # 实例化一个绘图部件
        self.plotWidget_dcdc1.setStyleSheet("")
        self.plotWidget_dcdc1.setObjectName("plotWidget_dcdc1")
        self.plotWidget_dcdc1.setXRange(min=0, max=self.my_config.graph_x, padding=0)
        # self.plotWidget_dcdc1.setYRange(min=0, max=self.my_config.graph_y, padding=0)

        self.ui.verticalLayout_graph_2.addWidget(self.plotWidget_dcdc1)  # 添加绘图部件到网格布局层

        self.plotWidget_dcdc1.setLabel('bottom', 'CNT', **{'font-family': 'Microsoft YaHei'})
        self.plotWidget_dcdc1.setLabel('left', 'Value', **{'font-family': 'Microsoft YaHei'})
        self.plotWidget_dcdc1.setTitle("DCDC1", **{'font-family': 'Microsoft YaHei'})
        item = self.plotWidget_dcdc1.getPlotItem()
        item.titleLabel.item.setFont(font)
        # 设置刻度字体
        self.plotWidget_dcdc1.getAxis("bottom").setStyle(tickFont=font)
        self.plotWidget_dcdc1.getAxis("left").setStyle(tickFont=font)

        self.curve_5 = self.plotWidget_dcdc1.plot(name="Input Voltage", pen=pen_red)
        self.curve_6 = self.plotWidget_dcdc1.plot(name="Input Current", pen=pen_blue)
        self.curve_7 = self.plotWidget_dcdc1.plot(name="Output Voltage", pen=pen_purple)
        self.curve_8 = self.plotWidget_dcdc1.plot(name="Output Current", pen=pen_yellow)

    # -----------------以下为逻辑部分---------------------

    def com_get(self):
        """
        获取存在的串口并加入到comboBox_uart
        :return: None
        """
        if self.flag_connect:
            self.my_log.system("请先断开连接再刷新。")
            return
        self.ui.comboBox_uart.clear()
        com = QSerialPort()
        com_list = QSerialPortInfo.availablePorts()
        for info in com_list:
            com.setPort(info)
            if com.open(QSerialPort.ReadWrite):
                self.ui.comboBox_uart.addItem(info.portName())
                com.close()

    def com_connect(self):
        """
        连接/断开串口
        :return:None
        """
        if self.flag_connect:
            # 此时已连接，需要断开连接
            self.ui.comboBox_uart.setEnabled(True)
            self.ui.comboBox_baudrate.setEnabled(True)
            self.ui.pushButton_connect.setText('连接')
            self.flag_connect = False
            self.com.close()  # 关闭串口
            self.timer.start(0)  # 设置计时间隔 100ms 并启动

            # 退出读取线程
            self.my_uart.flag_stop = True
            self.my_uart.quit()

            self.my_log.system("串口断开连接。")
            self.my_log.system("读取线程关闭。")
        else:
            com_name = self.ui.comboBox_uart.currentText()
            com_baud = int(self.ui.comboBox_baudrate.currentText())
            self.com.setPortName(com_name)
            try:
                if not self.com.open(QSerialPort.ReadWrite):
                    self.my_log.system('串口打开失败', 'red')
                    self.com_get()
                    return
            except Exception as e:
                self.my_log.system('串口打开失败 - {}'.format(e), 'red')
                self.com_get()
                return
            self.ui.comboBox_uart.setEnabled(False)
            self.ui.comboBox_baudrate.setEnabled(False)
            self.ui.pushButton_connect.setText('断开')
            self.com.setBaudRate(com_baud)
            self.flag_connect = True
            self.timer.start(self.ui.spinBox_showTimer.value())  # 设置计时间隔 self.ui.spinBox_showTimer.value() ms 并启动

            self.my_uart.start()
            self.my_uart.flag_stop = False  # 设置标志位

            self.my_log.system("串口连接成功。")
            self.my_log.system("定时器设置成功。")
            self.my_log.system("开启读取线程成功。")

    def com_receive(self):
        try:
            rxData = bytes(self.com.readAll())
            self.my_uart.buffer.append(rxData)
        except Exception as e:
            self.my_log.system('串口接收数据错误 - {}'.format(e), 'red')
            return None

        if self.flag_showData:
            if self.ui.checkBox_receive_data_type.isChecked():  # hex
                Data = binascii.b2a_hex(rxData).decode('ascii')
                hexStr = ' '.join(re.findall('(.{2})', Data))
                show_data = hexStr + ' '
            else:
                try:
                    show_data = rxData.decode('UTF-8')
                except Exception as e:
                    show_data = ""
                    self.my_log.system('串口接收数据错误 - {}'.format(e), 'red')
            self.ui.textEdit_data_receive.append(show_data)

    def com_send(self):
        """
        串口发送数据
        :return:None
        """
        txData = self.ui.textEdit_data_send.toPlainText()
        if len(txData) == 0:
            return None
        if not self.ui.checkBox_send_data_type.isChecked():
            self.my_uart.send_bytes(txData.encode('UTF-8'))
        else:
            Data = txData.replace(' ', '')
            # 如果16进制不是偶数个字符, 去掉最后一个, [ ]左闭右开
            if len(Data) % 2 == 1:
                Data = Data[0:len(Data) - 1]
            # 如果遇到非16进制字符
            if Data.isalnum() is False:
                self.my_log.system('串口发送 - 数据包含非十六进制数', 'red')
            try:
                hexData = binascii.a2b_hex(Data)
            except Exception as e:
                self.my_log.system('串口发送 - 转换编码错误 - {}'.format(e), 'red')
                return
            # 发送16进制数据, 发送格式如 ‘31 32 33 41 42 43’, 代表'123ABC'
            try:
                self.my_uart.send_bytes(hexData)
            except Exception as e:
                self.my_log.system('串口发送 - 十六进制发送错误 - {}'.format(e), 'red')
                return

    def checkbox_change(self):
        self.flag_showData = self.ui.checkBox_receive_data_show.isChecked()
        self.my_log.is_save = self.ui.checkBox_saveLog.isChecked()
        if self.ui.checkBox_set_window.isChecked():
            self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            self.show()
        else:
            # 取消置顶
            # 这里窗口会闪一下 不懂什么bug
            self.setWindowFlags(QtCore.Qt.WindowType.Window)
            self.show()

    def file_clean(self, directory):
        reply = QMessageBox.question(self,
                                     '警告',
                                     "是否要删除？确定删除后将会退出程序。",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.my_log.system('执行删除文件夹 "{}" 命令。'.format(directory))
        else:
            return None

        for root, dirs, files in os.walk(directory):
            # print(root, dirs, files)
            for file in files:
                try:
                    os.remove(root + '/' + file)
                except Exception as e:
                    self.my_log.system(e)
        self.close()

    def show_data(self):
        # voltage / current information
        data_to_component = [
            # pv
            [0x01, "pv_input_voltage", self.curve_1, self.ui.lcdNumber_pv_input_voltage],
            [0x01, "pv_input_current", self.curve_2, self.ui.lcdNumber_pv_input_current],
            [0x01, "pv_output_voltage", self.curve_3, self.ui.lcdNumber_pv_output_voltage],
            [0x01, "pv_output_current", self.curve_4, self.ui.lcdNumber_pv_output_current],
            # dcdc1
            [0x02, "dcdc1_input_voltage", self.curve_5, self.ui.lcdNumber_dcdc1_input_voltage],
            [0x02, "dcdc1_input_current", self.curve_6, self.ui.lcdNumber_dcdc1_input_current],
            [0x02, "dcdc1_output_voltage", self.curve_7, self.ui.lcdNumber_dcdc1_output_voltage],
            [0x02, "dcdc1_output_current", self.curve_8, self.ui.lcdNumber_dcdc1_output_current],
            # dcdc2
            [0x03, "dcdc2_input_voltage", self.curve_1, self.ui.lcdNumber_dcdc2_input_voltage],
            [0x03, "dcdc2_input_current", self.curve_2, self.ui.lcdNumber_dcdc2_input_current],
            [0x03, "dcdc2_output_voltage", self.curve_3, self.ui.lcdNumber_dcdc2_output_voltage],
            [0x03, "dcdc2_output_current", self.curve_4, self.ui.lcdNumber_dcdc2_output_current],
        ]
        data_sys_info = [
            [0x01, self.ui.lcdNumber_power_pv, "pv_input_voltage", "pv_input_current"],
            [0x02, self.ui.lcdNumber_power_dcdc1, "dcdc1_input_voltage", "dcdc1_input_current"],
            [0x03, self.ui.lcdNumber_power_dcdc2, "dcdc2_input_voltage", "dcdc2_input_current"],
        ]
        data_pwm = [
            [self.ui.lcdNumber_pwm_1, self.my_uart.pwm_value[0]],
            [self.ui.lcdNumber_pwm_2, self.my_uart.pwm_value[1]],
            [self.ui.lcdNumber_pwm_3, self.my_uart.pwm_value[2]],
        ]
        data_rc = [
            self.ui.progressBar_thr,
            self.ui.progressBar_yaw,
            self.ui.progressBar_pitch,
            self.ui.progressBar_roll,
            self.ui.progressBar_aux1,
            self.ui.progressBar_aux2,
            self.ui.progressBar_aux3,
            self.ui.progressBar_aux4,
        ]

        # show voltage / current
        n = self.my_config.graph_x + 1
        for tmp in data_to_component:
            query_data = self.my_uart.data[tmp[0]].get(tmp[1])
            if len(query_data) > n:
                y = query_data[-n:]
            else:
                y = query_data
            x = [i for i in range(len(y))]
            if tmp[0] == 0x01 or tmp[0] == 0x02:
                tmp[2].setData(x, y)
            tmp[3].display(str(self.my_uart.data[tmp[0]].get(tmp[1])[-1]))

        # show system information : power /
        for tmp in data_sys_info:
            power = self.my_uart.data[tmp[0]].get(tmp[2])[-1] * self.my_uart.data[tmp[0]].get(tmp[3])[-1]
            tmp[1].display("{:.3f}".format(power))

        # show system pwm
        for tmp in data_pwm:
            tmp[0].display("{:.1f}".format(tmp[1]))

        # show status bar
        self.label_cnt.setText("Rx:{: >8d}  Tx:{: >8d}  CorrectRate:{:0>3d}%  ".format(
            self.my_uart.count_receive,
            self.my_uart.count_send,
            int(self.my_uart.receive_correct_rate * 100)
        ))

        # show battery
        self.ui.lcdNumber_battery_voltage.display(str(self.my_uart.data[0x04].get("battery_voltage")[-1]))
        self.ui.progressBar_battery.setValue(int(self.my_uart.data[0x04].get("battery_soc")[-1]))

        # show rc data
        for index, progress in enumerate(data_rc):
            progress.setValue(int(self.my_uart.rc_value[index]))

        # heart
        delta_t = time.time() - self.my_uart.heart[-1]

        if delta_t > 5:
            if not self.flag_showWarning:
                self.my_log.system("系统心跳包过期！", 'red')
                self.flag_showWarning = True
            self.ui.label_system_status.setText("系统失联！！！")
            self.ui.label_system_status.setStyleSheet("background-color:rgb(255, 0, 0)")
        else:
            self.flag_showWarning = False
            self.ui.label_system_status.setText("系统正常运行")
            self.ui.label_system_status.setStyleSheet("background-color:rgb(0, 255, 0)")


if __name__ == '__main__':
    myapp = QApplication(sys.argv)
    myWin = MainWindow()

    parser = argparse.ArgumentParser(description="Hybrid unmanned ship control software")
    parser.add_argument('--version', '-v', action='version', version='version : v 0.01', help='show the version')
    parser.add_argument('--debug', '-d', default=False, help="debug mode")
    parser.add_argument('--port', '-p', help="serial port name")
    parser.add_argument('--rate', '-r', help="serial baudRate")
    parser.add_argument('--top', '-t', help="window on top")
    args = parser.parse_args()
    if args.debug:
        myWin.my_log.system('当前debug模式', 'red')
        myWin.my_log.system('已开启log保存', 'red')
        myWin.ui.checkBox_saveLog.setChecked(True)
        myWin.checkbox_change()
    if args.port and args.rate:
        index_port = myWin.ui.comboBox_uart.findText(str(args.port).upper())
        index_rate = myWin.ui.comboBox_baudrate.findText(str(args.rate))
        if index_port != -1 and index_rate != -1:
            myWin.ui.comboBox_uart.setCurrentIndex(index_port)
            myWin.ui.comboBox_baudrate.setCurrentIndex(index_rate)
            myWin.my_log.system(f"连接端口:{args.port} 波特率:{args.rate}", 'red')
            myWin.ui.pushButton_connect.click()
        else:
            myWin.my_log.system("port/rate 参数不存在", 'red')
    if args.top:
        myWin.ui.checkBox_set_window.setChecked(int(args.top))

    myWin.show()
    sys.exit(myapp.exec_())
