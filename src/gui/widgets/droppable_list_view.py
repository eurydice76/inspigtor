"""
"""

from PyQt5 import QtCore, QtGui, QtWidgets


class DroppableListView(QtWidgets.QListView):

    def __init__(self, *args, **kwargs):
        super(DroppableListView, self).__init__(*args, **kwargs)

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
        current_items = [self.model().item(i, 0).text() for i in range(self.model().rowCount())]
        dragged_items = [source_model.item(i, 0).text() for i in range(source_model.rowCount())]
        for item in dragged_items:
            if item in current_items:
                continue

            item = QtGui.QStandardItem(item)
            self.model().appendRow(item)

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Delete:

            for sel_index in reversed(self.selectedIndexes()):
                self.model().removeRow(sel_index.row())
