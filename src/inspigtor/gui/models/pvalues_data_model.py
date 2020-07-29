from PyQt5 import QtCore, QtGui


class PValuesDataModel(QtCore.QAbstractTableModel):

    def __init__(self, data):
        super(PValuesDataModel, self).__init__()
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
            elif role == QtCore.Qt.ForegroundRole:
                row = index.row()
                column = index.column()
                p_value = self._data.iloc[row, column]
                if p_value < 0.05 and p_value > 0:
                    return QtGui.QBrush(QtCore.Qt.red)

        return None

    def headerData(self, idx, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self._data.columns[idx]
            else:
                return self._data.index[idx]
        return None
