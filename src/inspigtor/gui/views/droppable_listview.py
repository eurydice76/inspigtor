"""
"""

import abc

from PyQt5 import QtCore, QtGui, QtWidgets


class DroppableListView(QtWidgets.QListView):

    __metaclass__ = abc.ABCMeta

    def __init__(self, pigs_model, *args, **kwargs):
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

    @abc.abstractmethod
    def dropEvent(self, event):
        """Event triggered when the dragged item is dropped into this widget.
        """

    def keyPressEvent(self, event):

        if event.key() == QtCore.Qt.Key_Delete:

            for sel_index in reversed(self.selectedIndexes()):
                self.model().remove_reader(sel_index.data(QtCore.Qt.DisplayRole))
                if self.model().rowCount() > 0:
                    index = self.model().index(self.model().rowCount()-1)
                    self.setCurrentIndex(index)

        else:
            super(PigsPoolListView, self).keyPressEvent(event)
