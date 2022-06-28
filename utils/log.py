import time
from PyQt5 import QtWidgets




class Log:
    def __init__(self, text_component: QtWidgets.QTextEdit, status_bar: QtWidgets.QStatusBar, is_save=False):
        self.text_component = text_component
        self.status_bar = status_bar
        self.is_print = False
        self.is_save = is_save
        self.show_to_statusBar = True
        self.str_time = str(time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))
        self.filename = r'log/{}.log'.format(self.str_time)
        if self.is_save:
            with open(self.filename, 'w', encoding='utf-8') as f:
                pass

    def out(self, level, content, color):
        text = "[{}] {:.>8s}: {}".format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), level, content)
        self.text_component.append('<font color="{}">{}</font>'.format(color, text))

        if self.show_to_statusBar:
            self.status_bar.showMessage("日志：{}".format(content))

        if self.is_save:
            with open(self.filename, 'a+', encoding='utf-8') as f:
                f.write(text + '\n')
        if self.is_print:
            print(text)
        return text

    def system(self, content, color='blue'):
        return self.out(self.system.__name__, content, color)

    def mcu(self, content, color=''):
        return self.out(self.mcu.__name__, content, color)

    def get_time(self, out=None):
        if out:
            self.system(out)
        return str(time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()))


if __name__ == '__main__':
    pass
