"""
"""

from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.views.droppable_listview import DroppableListView


class PigsPoolListView(DroppableListView):

    def __init__(self, pigs_model, *args, **kwargs):
        super(PigsPoolListView, self).__init__(*args, **kwargs)

        self._pigs_model = pigs_model

    def dropEvent(self, event):
        """Event triggered when the dragged item is dropped into this widget.
        """

        # Copy the mime data into a source model to get their underlying value
        source_model = QtGui.QStandardItemModel()
        source_model.dropMimeData(event.mimeData(), QtCore.Qt.CopyAction, 0, 0, QtCore.QModelIndex())

        target_model = self.model()
        if target_model is None:
            return

        # Drop only those items which are not present in this widget
        current_items = [target_model.data(target_model.index(i), QtCore.Qt.DisplayRole) for i in range(target_model.rowCount())]
        dragged_items = [source_model.item(i, 0).text() for i in range(source_model.rowCount())]
        for pig_name in dragged_items:
            if pig_name in current_items:
                continue

            reader = self._pigs_model.get_reader(pig_name)
            target_model.add_reader(reader)
