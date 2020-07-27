import csv
import io

from PyQt5 import QtCore, QtWidgets


class PigsView(QtWidgets.QListView):
    """This class implements a QListView with double click event.
    """

    double_clicked_empty = QtCore.pyqtSignal()

    def mouseDoubleClickEvent(self, event):
        """Event called when the user double click on the empty list view.


        Args:
            event (PyQt5.QtCore.QEvent): the double click event.
        """

        if self.model().rowCount() == 0:
            self.double_clicked_empty.emit()

        return super(PigsView, self).mouseDoubleClickEvent(event)
