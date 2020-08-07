import csv
import io

from pdb import set_trace

from PyQt5 import QtCore, QtWidgets


def find_main_window():
    """Find and return the main window

    Returns:
        PyQt5.QtWidgets.QMainWindow: the main window (None if not found)
    """
    app = QtWidgets.QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QtWidgets.QMainWindow):
            return widget
    return None


def debug_trace():
    """Set a tracepoint in the Python debugger that works with Qt
    """

    QtCore.pyqtRemoveInputHook()
    set_trace()


def func_formatter(tick_val, tick_pos, labels):
    int_tick_val = int(round(tick_val))
    if int_tick_val in range(len(labels)):
        return labels[int_tick_val]
    else:
        return ''
