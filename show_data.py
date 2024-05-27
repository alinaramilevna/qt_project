import hashlib
import sys
import io
import csv
import sqlite3
import uuid

from tools.checking_password import check_password, PasswordError

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox, QInputDialog, QPushButton

template = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Form</class>
 <widget class="QWidget" name="Form">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>492</width>
    <height>319</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Form</string>
  </property>
  <widget class="QComboBox" name="camera_comboBox">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>20</y>
     <width>121</width>
     <height>22</height>
    </rect>
   </property>
  </widget>
  <widget class="QComboBox" name="time_comboBox">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>70</y>
     <width>121</width>
     <height>22</height>
    </rect>
   </property>
  </widget>
  <widget class="QPushButton" name="show_button">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>120</y>
     <width>121</width>
     <height>23</height>
    </rect>
   </property>
   <property name="text">
    <string>OK</string>
   </property>
  </widget>
  <widget class="QPushButton" name="delete_button">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>160</y>
     <width>121</width>
     <height>23</height>
    </rect>
   </property>
   <property name="text">
    <string>Удалить</string>
   </property>
  </widget>
  <widget class="QTextEdit" name="coords_text_edit">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>240</y>
     <width>121</width>
     <height>51</height>
    </rect>
   </property>
  </widget>
  <widget class="QPushButton" name="save_in_csv_button">
   <property name="geometry">
    <rect>
     <x>20</x>
     <y>200</y>
     <width>121</width>
     <height>23</height>
    </rect>
   </property>
   <property name="text">
    <string>Скачать данные в .csv</string>
   </property>
  </widget>
  <widget class="QPushButton" name="create_new_password_btn">
   <property name="geometry">
    <rect>
     <x>150</x>
     <y>270</y>
     <width>121</width>
     <height>23</height>
    </rect>
   </property>
   <property name="text">
    <string>Сменить пароль</string>
   </property>
  </widget>
 </widget>
 <resources/>
 <connections/>
</ui>
'''


class ShowDataBaseWidget(QWidget):
    def __init__(self):
        super().__init__()
        f = io.StringIO(template)
        uic.loadUi(f, self)

        self.coords_text_edit.setReadOnly(True)
        self.coords_text_edit.setText('Текущие координаты: \n(None, None)')

        self.show_button.clicked.connect(self.show_data)
        self.delete_button.clicked.connect(self.delete_data)
        self.camera_comboBox.currentIndexChanged.connect(self.update_times)
        self.save_in_csv_button.clicked.connect(self.save_data_in_csv)
        self.create_new_password_btn.clicked.connect(self.create_new_password)
        self.connection = sqlite3.connect('db/frames_db.sqlite')
        pathes = self.connection.cursor().execute('SELECT path FROM cameras').fetchall()
        self.camera_comboBox.addItems([x[0] for x in pathes])
        self.update_times()

    def update_times(self):
        '''Необходима, чтобы при изменении camera_comboBox либо удаления из данных time_comboBox менялся сразу'''
        self.time_comboBox.clear()
        # Делаем в комбобоксах строчки с временем(time_to_show, т.к. полное время до мс будет не слишком красиво смотреться),
        # + айди, т.к. мы обрезаем до минут время, а таких кадров несколько, то мы сможем ориентироваться в них только с помощью айди
        try:
            times = self.connection.cursor().execute(
                f'SELECT time_to_show, id FROM frames WHERE camera_id = {int(self.camera_comboBox.currentText()) + 1}').fetchall()
            # print(times)  # отладка
        except TypeError:
            times = self.connection.cursor().execute(
                f'SELECT time_to_show, id FROM frames WHERE camera_id = (SELECT id from cameras WHERE path = '
                f'{self.camera_comboBox.currentText()}) ').fetchall()

        times = [' #'.join([i[0], str(i[1])]) for i in times]
        self.time_comboBox.addItems([x for x in times])

    def show_data(self):
        try:
            curr_time, curr_id = str(self.time_comboBox.currentText()).split(' #')
            query = f'SELECT upper_left_coords, screenshot FROM frames WHERE time_to_show = "{curr_time}" and id = {curr_id}'
            res = self.connection.cursor().execute(query).fetchall()[0]

        except ValueError:  # если time_comboBox пустой
            self.label = QLabel(self)
            self.label.setGeometry(150, 20, 300, 230)
            self.label.setText('Некорректные данные')
            return

        coords, image = res
        self.coords_text_edit.setText(f'Текущие координаты: \n{str(coords)}')

        pixmap = QPixmap()
        pixmap.loadFromData(image)

        self.label = QLabel(self)
        self.label.setGeometry(150, 20, 300, 230)
        self.label.setScaledContents(True)
        self.label.setPixmap(pixmap.scaled(300, 230))
        self.label.show()


    def delete_data(self):
        valid = QMessageBox.question(self, 'Подтверждение действия', 'Вы действительно хотите удалить запись?',
                                     QMessageBox.Yes,
                                     QMessageBox.No)
        if valid == QMessageBox.Yes:
            id = str(self.time_comboBox.currentText()).split(' #')[1]

            cur = self.connection.cursor()
            cur.execute(f'DELETE from frames WHERE id = {id}')
            self.connection.commit()

            self.update_times()
            QMessageBox.information(self, 'OK', 'Запись успешно удалена')
            self.show_data()

    def save_data_in_csv(self):
        try:
            name_of_file = f'frames_{self.camera_comboBox.currentText()}.csv'

            cursor = self.connection.cursor()
            data = cursor.execute(f'SELECT id, time, upper_left_coords '
                                  f'FROM frames WHERE camera_id = (SELECT id FROM '
                                  f'cameras WHERE path = {self.camera_comboBox.currentText()})').fetchall()

            with open(name_of_file, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=';')
                csv_writer.writerow(['frames_id', 'time', 'upper_left_coords'])
                csv_writer.writerows(data)

            QMessageBox.information(self, 'Статус', f'Файл успешно загружен с названием {name_of_file}')
        except Exception as error:
            QMessageBox.information(self, 'Ошибка', f'Упс, что-то пошло не так!\n{error}')

    def create_new_password(self):
        '''Для смены пароля'''
        valid = QMessageBox.question(self, 'Password change', 'Желаете поменять пароль?', QMessageBox.Yes,
                                     QMessageBox.No)
        if valid == QMessageBox.Yes:
            password, ok_pressed = QInputDialog.getText(self, 'Ввод пароля',
                                                        'Введите новый пароль.\nПароль должен быть длиной не менее 8 символов,\nДолжен содержать цифры,\nбуквы в разных регистрах.')
            if ok_pressed:
                try:
                    check_password(password)  # Проверка корректности пароля
                except PasswordError as error_message:  # Пароль не соответствует требованиям
                    QMessageBox.information(self, 'Ошибка',
                                            'Пароль не соответствует требованиям:\n' + str(error_message))
                else:
                    self.update_password(password)  # Если всё хорошо, меняем пароль
                    QMessageBox.information(self, 'OK', 'Пароль успешно изменён')

    def update_password(self, password):
        '''Обновляем пароль в базе данных'''
        salt = uuid.uuid4().hex
        hash_object = hashlib.sha256(password.encode() + salt.encode())
        hex_dig = hash_object.hexdigest()  # хэш нового пароля

        # засовываем все это в базу данных
        con = sqlite3.connect('db/passwords.sqlite')
        cur = con.cursor()
        cur.execute('''INSERT INTO password_history(hash, salt) VALUES(?, ?)''', (hex_dig, salt,))
        con.commit()
        con.close()


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ShowDataBaseWidget()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
