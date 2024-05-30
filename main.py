import sys

from PyQt5.QtWidgets import QApplication
from main_window import VideoAnalyzer, except_hook

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoAnalyzer()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
