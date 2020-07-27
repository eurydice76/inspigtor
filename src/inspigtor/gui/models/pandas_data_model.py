from PyQt5 import QtCore, QtGui


class PandasDataModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(PandasDataModel, self).__init__()
        self._data = data
        self._colored_rows = {}

    def rowCount(self, parent=None):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.iloc[index.row(), index.column()])
            elif role == QtCore.Qt.BackgroundRole:
                return self._colored_rows.get(index.row(), QtGui.QColor('white'))

        return None

    def headerData(self, col, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._data.columns[col]
            else:
                return str(col)
        return None

    def setColoredRows(self, rows):

        self._colored_rows = rows

        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount(), self.columnCount()), [QtCore.Qt.BackgroundRole])
