import csv
import io

from PyQt5 import QtCore, QtGui, QtWidgets


def copy_selection(tableview):
    """Copy the selected dqtq of q tqble view to the clipboqrd

    Args:
        tableview (PyQt5.QtWidgets.QTableView): the table view to copy data from
    """
    selection = tableview.selectedIndexes()
    if selection:
        rows = sorted(index.row() for index in selection)
        columns = sorted(index.column() for index in selection)
        rowcount = rows[-1] - rows[0] + 1
        colcount = columns[-1] - columns[0] + 1
        table = [[''] * colcount for _ in range(rowcount)]
        for index in selection:
            row = index.row() - rows[0]
            column = index.column() - columns[0]
            table[row][column] = index.data()
        stream = io.StringIO()
        csv.writer(stream).writerows(table)
        QtWidgets.QApplication.clipboard().setText(stream.getvalue())


class CopyFilter(QtCore.QObject):
    """This class implements an event filter when the user press Ctrl-C on a copy-pastable table view.
    """

    def eventFilter(self, source, event):
        """Event filter when the user press Ctrl-C on a copy-pastable table view.

        Args:
            source (inspigtor.gui.widgets.copy_pastable_tableview.CopyPastableTableView): the table view
            event (PyQt5.QtCore.QEvent): the event 
        """

        if (event.type() == QtCore.QEvent.KeyPress and event.matches(QtGui.QKeySequence.Copy)):
            copy_selection(source)
            return True
        return super(CopyFilter, self).eventFilter(source, event)


class CopyPastableTableView(QtWidgets.QTableView):
    """This class implements a table view whose selection can be copy and pasted to the clipboard
    """

    def __init__(self, *args, **kwargs):

        super(CopyPastableTableView, self).__init__(*args, **kwargs)

        copy_filter = CopyFilter(self)
        self.installEventFilter(copy_filter)
