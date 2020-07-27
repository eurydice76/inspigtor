#!/usr/bin/env python3

import sys

from PyQt5 import QtWidgets

from inspigtor.gui.main_window import MainWindow


def main():
    app = QtWidgets.QApplication(sys.argv)
    _ = MainWindow()
    app.exec_()


if __name__ == "__main__":

    main()
