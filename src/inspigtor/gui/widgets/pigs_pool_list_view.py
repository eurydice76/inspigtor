"""
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class PigsPoolListView(QtWidgets.QListView):

    def __init__(self, pigs_model, *args, **kwargs):
        super(PigsPoolListView, self).__init__(*args, **kwargs)

        self._pigs_model = pigs_model

        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dragMoveEvent(self, event):
        """Event triggered when the dragged item is moved above the target widget.
        """

        event.accept()

    def dragEnterEvent(self, event):
        """Event triggered when the dragged item enter into this widget.
        """

        if event.mimeData().hasFormat('application/x-qabstractitemmodeldatalist'):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """Event triggered when the dragged item is dropped into this widget.
        """

        # Copy the mime data into a source model to get their underlying value
        source_model = QtGui.QStandardItemModel()
        source_model.dropMimeData(event.mimeData(), QtCore.Qt.CopyAction, 0, 0, QtCore.QModelIndex())

        # Drop only those items which are not present in this widget
        current_items = [self.model().data(self.model().index(i), QtCore.Qt.DisplayRole) for i in range(self.model().rowCount())]
        dragged_items = [source_model.item(i, 0).text() for i in range(source_model.rowCount())]
        for pig_name in dragged_items:
            if pig_name in current_items:
                continue

            reader = self._pigs_model.get_reader(pig_name)
            self.model().add_reader(reader)

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Delete:

            for sel_index in reversed(self.selectedIndexes()):
                self.model().remove_reader(sel_index.data(QtCore.Qt.DisplayRole))
                if self.model().rowCount() > 0:
                    index = self.model().index(self.model().rowCount()-1)
                    self.setCurrentIndex(index)

        else:
            super(PigsPoolListView, self).keyPressEvent(event)
