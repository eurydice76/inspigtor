import csv
import io

from PyQt5 import QtCore, QtWidgets


class DoubleClickableListView(QtWidgets.QListView):
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

        return super(DoubleClickableListView, self).mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        """Event called when the user press a keyboard key.
        """

        model = self.model()
        if model is None:
            return

        if event.key() == QtCore.Qt.Key_Delete:

            for sel_index in reversed(self.selectedIndexes()):
                self.model().remove_index(sel_index.row())
