from PyQt5.QtWidgets import QApplication, QMainWindow


def find_main_window():
    app = QApplication.instance()
    for widget in app.topLevelWidgets():
        if isinstance(widget, QMainWindow):
            return widget
    return None
