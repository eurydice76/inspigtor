from PyQt5 import QtCore, QtWidgets


class PigsView(QtWidgets.QListView):

    double_clicked_empty = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):

        super(PigsView, self).__init__(*args, **kwargs)

    def mouseDoubleClickEvent(self, event):

        if self.model().rowCount() == 0:
            self.double_clicked_empty.emit()

        return super(PigsView, self).mouseDoubleClickEvent(event)
