from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import QCoreApplication, Qt

import sys
import live2d.v3 as live2d

from MainWindow import MainWindow



def main():
    live2d.enableLog(False)

    live2d.init()

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)

    app.setWindowIcon(QIcon("moeroid.ico"))

    window = MainWindow()
    window.show()

    app.aboutToQuit.connect(lambda: live2d.dispose())

    sys.exit(app.exec())


if __name__ == '__main__':
    main()