import io
import sqlite3
import sys
import hashlib
import warnings

from tools.cv2_functions import analyze_video, VideoError
from show_data import ShowDataBaseWidget

from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QInputDialog, QMessageBox, QDial

template = '''<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>MainWindow</class>
 <widget class="QMainWindow" name="MainWindow">
  <property name="geometry">
   <rect>
    <x>0</x>
    <y>0</y>
    <width>754</width>
    <height>504</height>
   </rect>
  </property>
  <property name="windowTitle">
   <string>Project!!!</string>
  </property>
  <widget class="QWidget" name="centralwidget">
   <widget class="QSpinBox" name="spinBox">
    <property name="geometry">
     <rect>
      <x>20</x>
      <y>10</y>
      <width>721</width>
      <height>22</height>
     </rect>
    </property>
    <property name="maximum">
     <number>100000000</number>
    </property>
    <property name="displayIntegerBase">
     <number>10</number>
    </property>
   </widget>
   <widget class="QPushButton" name="open_video_button">
    <property name="geometry">
     <rect>
      <x>20</x>
      <y>50</y>
      <width>311</width>
      <height>23</height>
     </rect>
    </property>
    <property name="text">
     <string>Включить видео</string>
    </property>
   </widget>
   <widget class="QPushButton" name="open_database_button">
    <property name="geometry">
     <rect>
      <x>380</x>
      <y>50</y>
      <width>361</width>
      <height>23</height>
     </rect>
    </property>
    <property name="text">
     <string>Открыть данные</string>
    </property>
   </widget>
   <widget class="QLabel" name="video_label">
    <property name="geometry">
     <rect>
      <x>30</x>
      <y>90</y>
      <width>111</width>
      <height>16</height>
     </rect>
    </property>
    <property name="text">
     <string>Нет видео</string>
    </property>
   </widget>
  </widget>
  <widget class="QMenuBar" name="menubar">
   <property name="geometry">
    <rect>
     <x>0</x>
     <y>0</y>
     <width>754</width>
     <height>21</height>
    </rect>
   </property>
  </widget>
  <widget class="QStatusBar" name="statusbar"/>
 </widget>
 <resources/>
 <connections/>
</ui>
'''

warnings.filterwarnings('ignore')
class VideoAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        f = io.StringIO(template)
        uic.loadUi(f, self)
        self.label = QLabel(self)
        self.label.setGeometry(30, 180, 500, 40)
        self.label.setText('Выберите чувствительность распознавания движения')

        self.cap = None
        self.last_frame = None
        self.min_area = 1200

        self.open_database_button.clicked.connect(self.checking_password)
        self.open_video_button.clicked.connect(self.open_video)

        self.dial_label = QLabel(self)
        self.dial_label.setGeometry(200, 230, 200, 100)
        self.dial_label.setText('Текущее значение: 1200')

        self.show_data_window = None

        self.make_cat()
        self.another_widget()

    def make_cat(self):
        '''Просто пусть будет:)'''
        self.cat_pixmap = QPixmap('kotik.jpg')
        self.cat_pixmap.scaled(100, 100)

        self.image = QLabel(self)
        self.image.setGeometry(600, 100, 100, 100)
        self.image.setScaledContents(True)
        self.image.setPixmap(self.cat_pixmap)

    def another_widget(self):  # требование по виджетам, которые не изучали
        self.dial = QDial(self)

        self.dial.setRange(800, 2000)
        self.dial.setValue(1200)
        self.dial.setGeometry(0, 210, 210, 100)

        self.dial.show()
        self.dial.valueChanged.connect(self.change_min_area)

    def change_min_area(self):
        self.dial_label.setText(f'Текущее значение: {self.dial.value()}')
        self.min_area = self.dial.value()

    def show_data(self):
        if self.show_data_window is None:
            self.show_data_window = ShowDataBaseWidget()
        self.show_data_window.show()

    def hash_password_to_check(self, password, salt):
        '''Принимает на вход пароль, введённый пользователем и соль от правильного пароля,
        возвращает хэшированный пароль, введёный пользователем'''
        hash_object = hashlib.sha256(password.encode() + salt.encode())
        return hash_object.hexdigest()

    def get_current_password_hash_and_salt(self):
        '''Возвращает текущий пароль, т.е. тот, который был последний добавлен в базу данных'''
        con = sqlite3.connect('db/passwords.sqlite')
        cur = con.cursor()
        return cur.execute('SELECT hash, salt FROM password_history ORDER BY id DESC LIMIT 1').fetchall()[0]

    def checking_password(self):
        password, ok = QInputDialog.getText(self, "Пароль", "Введите пароль:")
        if password == '' and not ok:
            return
        correct_password, salt = self.get_current_password_hash_and_salt()

        if ok and self.hash_password_to_check(password, salt) == correct_password:
            self.show_data()
        else:
            QMessageBox.information(self, 'Wrong password', 'Неверный пароль', QMessageBox.Ok)

    def open_video(self):
        path = self.spinBox.value()
        self.video_label.resize(300, 20)
        # Чтобы после включения видео пользователь не мог менять min_area
        self.dial.setDisabled(True)
        try:
            self.video_label.setText('Видео обрабатывается')
            analyze_video(path, min_area=self.min_area)
            self.video_label.setText('Видео не включено')
        except VideoError:
            self.video_label.setText('Нет подходящей камеры')
        self.dial.setEnabled(True)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)
