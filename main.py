import sys

import numpy as np
from PyQt5 import QtWidgets
from PyQt5 import sip
from PyQt5.QtCore import (QCoreApplication, QMetaObject,
                          QSize, Qt)
from PyQt5.QtWidgets import *

legs = []
windows = []


# это класс самой задачи
class Task:
    def __init__(self, legs=3):
        self.legs = [list() for i in range(legs)]

    # Добавление источника в одну из ветвей
    def add_generator(self, leg_index: int, direction: str, voltage: float, resistance: float,
                      qt_object):
        self.legs[leg_index].append((resistance, direction, voltage, qt_object))

    # добавление резистора
    def add_resistor(self, leg_index: int, resistance: float, qt_object):
        self.legs[leg_index].append((resistance, qt_object))

    # добавление новой ветви и возвращение id этой ветви
    def add_new_line(self):
        self.legs.append(list())
        return len(self.legs) - 1

    # редактирование резистора
    def edit_resistor(self, leg_index, el_index, resistance):
        try:
            old = self.legs[leg_index][el_index]
            new = (resistance, old[1])
            self.legs[leg_index][el_index] = new
        except Exception as e:
            print(e)

    # редактирование источника
    def edit_generator(self, leg_index: int, el_index: int, direction: str, voltage: float,
                       resistance: float):
        old = self.legs[leg_index][el_index]
        new = (resistance, direction, voltage, old[-1])
        self.legs[leg_index][el_index] = new

    # добаление узла(нереализованное действие)
    def add_node(self, leg_index: int):
        self.legs[leg_index].append(Task_in_task())
        return self.legs[leg_index][-1]

    def get_node(self, leg_index: int, el_index: int):
        return self.legs[leg_index][el_index]

    # перевод всей задачи в нормальный вид(вид в котором могут читать функции методов)
    def normal(self) -> list:
        result = list()
        for el in self.legs:
            resistance_sum = 0
            voltage_sum = 0
            direction_sum = 'L'
            for el_in_el in el:
                if isinstance(el_in_el, tuple):
                    resistance_sum += el_in_el[0]
                    if len(el_in_el) == 4:
                        voltage_sum += el_in_el[2] * (-1 if el_in_el[1] == 'R' else 1)
                elif isinstance(el_in_el, Task_in_task):
                    resistance_sum += el_in_el.return_resistance()
            if voltage_sum < 0:
                voltage_sum *= -1
                direction_sum = 'R'
            result.append([resistance_sum, direction_sum, voltage_sum])
        return result


# Нереализованный класс нового узла.
class Task_in_task(Task):
    def __init__(self, legs=2):
        super().__init__(legs)

    # Нельзя добавлять генератор
    def add_generator(self, leg_index: int, direction: str, voltage: float, resistance: float,
                      qt_object):
        pass

    # Возврат сопротивления
    def return_resistance(self) -> float:
        result = 0
        print(self.legs)
        for i in range(len(self.legs)):
            try:
                result += 1 / sum(map(lambda a: a[0], self.legs[i]))
            except TypeError:
                pass
        return result ** -1


# Решение задачи MH методом и возврат значений токов
def MH_method(legs: list) -> dict:
    result = []
    dict_of_i = {}
    [dict_of_i.update({el + 1: []}) for el in range(len(legs))]
    for el in range(len(legs)):
        if legs[el][1] == 'R':
            minus_or_plus = -1
        else:
            minus_or_plus = 1
        r1 = round(sum([1 / el_2[0] for index, el_2 in enumerate(legs) if el != index]) ** -1, 2)
        i = round(legs[el][2] / (r1 + legs[el][0]), 2)
        dict_of_i[el + 1].append(i * minus_or_plus)
        uab = round(r1 * i, 2)
        for index, el_3 in enumerate([el_2[0] for el_2 in legs]):
            if index != el:
                dict_of_i[index + 1].append(round(uab / el_3 * -1 * minus_or_plus, 2))
    return dict_of_i


# Тоже самое, только для красивого вывода(для вывода решения)
def MH_method_for_out(legs: list):
    result = []
    dict_of_i = {}
    [dict_of_i.update({el + 1: []}) for el in range(len(legs))]
    for el in range(len(legs)):
        if legs[el][1] == 'R':
            minus_or_plus = -1
        else:
            minus_or_plus = 1
        r1 = round(sum([1 / el_2[0] for index, el_2 in enumerate(legs) if el != index]) ** -1, 2)
        yield r1
        i = round(legs[el][2] / (r1 + legs[el][0]), 2)
        dict_of_i[el + 1].append(i * minus_or_plus)
        yield str(el + 1), str(legs[el][2]) + '/' + str(r1 + legs[el][0])
        yield str(i * minus_or_plus)
        uab = round(r1 * i, 2)
        yield uab
        for index, el_3 in enumerate([el_2[0] for el_2 in legs]):
            if index != el:
                dict_of_i[index + 1].append(round(uab / el_3 * -1 * minus_or_plus, 2))
                yield str(index + 1), str(uab) + '/' + str(el_3)
                yield str(round(uab / el_3 * -1 * minus_or_plus, 2))
    yield dict_of_i


# Решение задачи MУH методом и возврат значений токов
def MYH_method(legs: list) -> dict:
    dict_of_i = {}
    gs = [round(1 / el[0], 3) for el in legs]
    edss = [-el[2] if el[1] == 'R' else el[2] for el in legs]
    uab = round(sum([gs[i] * edss[i] for i in range(len(legs))]) / sum(gs), 2)
    for i in range(len(legs)):
        dict_of_i[i + 1] = (edss[i] - uab) * gs[i]
    return dict_of_i


# Тоже самое, только для красивого вывода(для вывода решения)
def MYH_method_for_out(legs: list):
    dict_of_i = {}
    gs = [round(1 / el[0], 3) for el in legs]
    yield gs
    edss = [-el[2] if el[1] == 'R' else el[2] for el in legs]
    uab = round(sum([gs[i] * edss[i] for i in range(len(legs))]) / sum(gs), 2)
    yield uab
    for i in range(len(legs)):
        dict_of_i[i + 1] = (edss[i] - uab) * gs[i]
        yield f'I{i + 1} = ({edss[i]} - {uab}) * {gs[i]} = {round((edss[i] - uab) * gs[i], 4)}'
    yield dict_of_i


# Это вспомогательная функция для МУКУ метода,
# чтобы получить определённый порядок для создания системы уравнения
def MYKY_help_1(num: int) -> list:
    result = []
    x = 0
    for i in range(1, num + 1):
        if i == 1:
            result.append([i])
        elif i == num:
            result[x].append(i)
        else:
            result[x].append(i)
            x += 1
            result.append([i])
    return result


# Решение задачи MУКУ методом и возврат значений токов
def MYKY_method(legs: list):
    array = MYKY_help_1(len(legs))
    b = [0]
    for g in range(len(array)):
        one = legs[array[g][0] - 1][2] * (-1 if legs[array[g][0] - 1][1] == 'L' else 1)
        second = legs[array[g][1] - 1][2] * (-1 if legs[array[g][1] - 1][1] == 'R' else 1)
        b.append(one + second)
    a = [[1] * len(legs)]
    for g in range(len(array)):
        a.append(
            [(legs[i - 1][0] if array[g].index(i) == 1 else -legs[i - 1][0]) if i in array[g] else 0
             for i in
             range(1, len(legs) + 1)])  # заполнение матрицы
    a = np.array(a)
    b = np.array(b)
    x = np.linalg.solve(a, b)
    return x


# Тоже самое, только для красивого вывода(для вывода решения)
def MYKY_method_for_out(legs: list):
    array = MYKY_help_1(len(legs))
    b = [0]
    for g in range(len(array)):
        one = legs[array[g][0] - 1][2] * (-1 if legs[array[g][0] - 1][1] == 'L' else 1)
        second = legs[array[g][1] - 1][2] * (-1 if legs[array[g][1] - 1][1] == 'R' else 1)
        b.append(one + second)
    a = [[1] * len(legs)]
    for g in range(len(array)):
        a.append(
            [(legs[i - 1][0] if array[g].index(i) == 1 else -legs[i - 1][0]) if i in array[g] else 0
             for i in
             range(1, len(legs) + 1)])  # заполнение матрицы
    for el, el_2 in zip(a, b):
        yield '[' + ' '.join(list(map(str, el))) + ']' + '  ' + '[' + str(el_2) + ']'
    a = np.array(a)
    b = np.array(b)
    x = np.linalg.solve(a, b)
    yield x


class Decide(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(640, 768)
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.MYH = QLabel(Form)
        self.MYH.setObjectName(u"MYH")

        self.horizontalLayout.addWidget(self.MYH)

        self.line = QFrame(Form)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.MH = QLabel(Form)
        self.MH.setObjectName(u"MH")

        self.horizontalLayout.addWidget(self.MH)

        self.line_2 = QFrame(Form)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line_2)

        self.MYKY = QLabel(Form)
        self.MYKY.setObjectName(u"MYKY")

        self.horizontalLayout.addWidget(self.MYKY)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.tableWidget = QTableWidget(Form)
        self.tableWidget.setObjectName(u"tableWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)

        self.verticalLayout.addWidget(self.tableWidget)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)

    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(
            QCoreApplication.translate("Form", u"\u0420\u0435\u0448\u0435\u043d\u0438\u0435", None))
        self.MYH.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.MH.setText(QCoreApplication.translate("Form", u"TextLabel", None))
        self.MYKY.setText(QCoreApplication.translate("Form", u"TextLabel", None))


class Easy_mod_ui(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(600, 300)
        Form.setMaximumSize(QSize(600, 16777215))
        self.verticalLayout_2 = QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(-1, 0, -1, -1)
        self.spinBox = QSpinBox(Form)
        self.spinBox.setObjectName(u"spinBox")
        self.spinBox.setMinimum(2)
        self.spinBox.setValue(3)

        self.horizontalLayout.addWidget(self.spinBox)

        self.radioButton = QRadioButton(Form)
        self.radioButton.setObjectName(u"radioButton")
        self.radioButton.setChecked(True)

        self.horizontalLayout.addWidget(self.radioButton)

        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_2 = QLabel(Form)
        self.label_2.setObjectName(u"label_2")
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.label_2)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy1)
        self.label.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.label)

        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setAlignment(Qt.AlignCenter)

        self.horizontalLayout_7.addWidget(self.label_3)

        self.verticalLayout.addLayout(self.horizontalLayout_7)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.lineEdit_11 = QLineEdit(Form)
        self.lineEdit_11.setObjectName(u"lineEdit_11")

        self.horizontalLayout_6.addWidget(self.lineEdit_11)

        self.comboBox_6 = QComboBox(Form)
        self.comboBox_6.addItem("")
        self.comboBox_6.addItem("")
        self.comboBox_6.setObjectName(u"comboBox_6")
        sizePolicy2 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.comboBox_6.sizePolicy().hasHeightForWidth())
        self.comboBox_6.setSizePolicy(sizePolicy2)

        self.horizontalLayout_6.addWidget(self.comboBox_6)

        self.lineEdit_12 = QLineEdit(Form)
        self.lineEdit_12.setObjectName(u"lineEdit_12")

        self.horizontalLayout_6.addWidget(self.lineEdit_12)

        self.verticalLayout.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.lineEdit_7 = QLineEdit(Form)
        self.lineEdit_7.setObjectName(u"lineEdit_7")

        self.horizontalLayout_4.addWidget(self.lineEdit_7)

        self.comboBox_4 = QComboBox(Form)
        self.comboBox_4.addItem("")
        self.comboBox_4.addItem("")
        self.comboBox_4.setObjectName(u"comboBox_4")

        self.horizontalLayout_4.addWidget(self.comboBox_4)

        self.lineEdit_8 = QLineEdit(Form)
        self.lineEdit_8.setObjectName(u"lineEdit_8")

        self.horizontalLayout_4.addWidget(self.lineEdit_8)

        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.lineEdit_9 = QLineEdit(Form)
        self.lineEdit_9.setObjectName(u"lineEdit_9")

        self.horizontalLayout_5.addWidget(self.lineEdit_9)

        self.comboBox_5 = QComboBox(Form)
        self.comboBox_5.addItem("")
        self.comboBox_5.addItem("")
        self.comboBox_5.setObjectName(u"comboBox_5")

        self.horizontalLayout_5.addWidget(self.comboBox_5)

        self.lineEdit_10 = QLineEdit(Form)
        self.lineEdit_10.setObjectName(u"lineEdit_10")

        self.horizontalLayout_5.addWidget(self.lineEdit_10)

        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)

        self.pushButton = QPushButton(Form)
        self.pushButton.setObjectName(u"pushButton")

        self.verticalLayout_2.addWidget(self.pushButton)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)

    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.radioButton.setText(QCoreApplication.translate("Form", u"Easymod", None))
        self.label_2.setText(QCoreApplication.translate("Form",
                                                        u"\u0421\u043e\u043f\u0440\u043e\u0442\u0438\u0432\u043b\u0435\u043d\u0438\u0435",
                                                        None))
        self.label.setText(QCoreApplication.translate("Form",
                                                      u"\u041d\u0430\u043f\u0440\u0430\u0432\u043b\u0435\u043d\u0438\u0435",
                                                      None))
        self.label_3.setText(
            QCoreApplication.translate("Form", u"\u0412\u043e\u043b\u044c\u0442\u0430\u0436", None))
        self.comboBox_6.setItemText(0, QCoreApplication.translate("Form", u"L", None))
        self.comboBox_6.setItemText(1, QCoreApplication.translate("Form", u"R", None))

        self.comboBox_4.setItemText(0, QCoreApplication.translate("Form", u"L", None))
        self.comboBox_4.setItemText(1, QCoreApplication.translate("Form", u"R", None))

        self.comboBox_5.setItemText(0, QCoreApplication.translate("Form", u"L", None))
        self.comboBox_5.setItemText(1, QCoreApplication.translate("Form", u"R", None))

        self.pushButton.setText(QCoreApplication.translate("Form", u"Decide", None))
    # retranslateUi


class Decide_window(QMainWindow, Decide):
    dict_ = dict()

    def __init__(self):
        super().__init__()
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.setupUi(self.central_widget)
        result = ''
        MH_gen = MH_method_for_out(legs)
        for i in range(len(legs)):
            result += str(i + 1) + '.' + '\n'
            result += 'R1 = ' + str(next(MH_gen)) + '\n'
            result += 'I' + ' = '.join(next(MH_gen)) + ' = ' + next(MH_gen) + '\n'
            result += 'Uab = ' + str(next(MH_gen)) + '\n'
            for g in range(len(legs) - 1):
                result += 'I' + ' = '.join(next(MH_gen)) + ' = ' + next(MH_gen) + '\n'
        dict_ = next(MH_gen)
        result += '\n\nTrue currents: \n'
        for i in range(1, len(legs) + 1):
            result += 'I{} = {} = {}'.format(str(i), ' + '.join(map(str, dict_[i])),
                                             str(round(float(sum(dict_[i])), 2))) + '\n'
        self.dict_['MH'] = result
        self.MH.setText(result)

        result = ''
        MYH_gen = MYH_method_for_out(legs)
        gs = next(MYH_gen)
        for index, g in enumerate(gs):
            result += f'  g{index + 1} = 1/{legs[index][0]} = {g} Cм \n'
        result += f'  Uab = {next(MYH_gen)} \n'
        for i in range(len(legs)):
            result += '  ' + next(MYH_gen) + '\n'
        self.MYH.setText(result)
        self.dict_['MYH'] = result
        result = 'Matrix: \n'
        MYKY_gen = MYKY_method_for_out(legs)
        for i in range(len(legs)):
            result += next(MYKY_gen) + '\n'
        i = next(MYKY_gen)
        result += '\n\n'
        for g in range(len(legs)):
            result += f'I{g + 1} = ' + str(i[g]) + '\n'
        self.MYKY.setText(result)
        self.dict_['MYKY'] = result
        MYH = MYH_method(legs)
        MH = MH_method(legs)
        MYKY = MYKY_method(legs)
        res = [list() for i in range(len(legs))]
        res[0].append('МУН')
        res[1].append('МН')
        res[2].append('МУKУ')
        self.tableWidget.setColumnCount(len(legs) + 1)
        self.tableWidget.setRowCount(0)
        for i in range(len(legs)):
            self.tableWidget.setHorizontalHeaderItem(i + 1, QTableWidgetItem(f'I{i}'))
            res[0].append(MYH[i + 1])
            res[1].append(sum(MH[i + 1]))
            res[2].append(MYKY[i])
        for i, row in enumerate(res):
            print(row)
            self.tableWidget.setRowCount(
                self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                print(elem)
                self.tableWidget.setItem(
                    i, j, QTableWidgetItem(str(elem)))


def open_window(obj, x, y, w, h):
    global windows
    windows.append(obj())
    windows[-1].show()
    windows[-1].setGeometry(x, y + 20, w, h)


class Easy_mod(QMainWindow, Easy_mod_ui):
    now_lines = 3

    def __init__(self):
        super().__init__()
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.setupUi(self.central_widget)
        self.pushButton.pressed.connect(self.decide)
        self.spinBox.valueChanged.connect(self.lines)
        self.setMaximumSize(QSize(600, 16777215))
        self.radioButton.setEnabled(False)

    def decide(self):
        global legs
        legs = []
        print(1)
        x = 0
        for el in self.verticalLayout.children():
            if x == 0:
                x = 1
                continue
            try:
                int(el.itemAt(0).widget().text())
                int(el.itemAt(2).widget().text())
            except Exception as e:
                break
            legs.append([int(el.itemAt(0).widget().text()), el.itemAt(1).widget().currentText(),
                         int(el.itemAt(2).widget().text())])
        if len(legs) == self.now_lines:
            open_window(Decide_window, self.x() - 300, self.y(), self.width(), self.height())

    def lines(self, num):
        if self.now_lines < num:
            for i in range(num - self.now_lines):
                new_layout = QHBoxLayout(self.central_widget)
                new_layout.addWidget(QLineEdit(self))
                combo_box = QComboBox(self)
                combo_box.addItem('L')
                combo_box.addItem('R')
                new_layout.addWidget(combo_box)
                new_layout.addWidget(QLineEdit(self))
                self.verticalLayout.addLayout(new_layout)
        else:
            for i in range(self.now_lines - num):
                print(type(self.verticalLayout.children()[-(i + 1)]))
                self.deleteLayout(self.verticalLayout.children()[-(i + 1)])
        self.now_lines = num

    def deleteLayout(self, cur_lay):
        if cur_lay is not None:
            while cur_lay.count():
                item = cur_lay.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.deleteLayout(item.layout())
            sip.delete(cur_lay)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Easy_mod()
    ex.show()
    sys.exit(app.exec_())
