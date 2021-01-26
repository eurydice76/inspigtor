import logging

import numpy as np

from PyQt5 import QtCore, QtGui

from inspigtor.kernel.pigs.pigs_pool import PigsPool, PigsPoolError


class PigsPoolModel(QtCore.QAbstractListModel):
    """This model describes a pool of pigs.
    """

    Reader = QtCore.Qt.UserRole + 1

    reader_removed = QtCore.pyqtSignal(str)

    def __init__(self, parent, pigs_pool=None):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(PigsPoolModel, self).__init__(parent)

        if pigs_pool is None:
            self._pigs_pool = PigsPool()
        else:
            self._pigs_pool = pigs_pool

    def get_reader(self, filename):

        return self._pigs_pool.get_reader(filename)

    def add_reader(self, reader):
        """Add a reader to the internal pool.

        Args:
            reader (inspigtor.kernel.readers.picco2_reader.PiCCO2FileReader): the reader
        """

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())

        try:
            self._pigs_pool.add_reader(reader)
        except PigsPoolError as error:
            logging.error(str(error))

        self.endInsertRows()

    def remove_index(self, index):
        """Remove 
        """

        pigs = self._pigs_pool.pigs

        pig_names = list(pigs.keys())

        filename = pig_names[index]

        self.remove_reader(filename)

    def remove_reader(self, filename):

        pigs = self._pigs_pool.pigs

        pig_names = list(pigs.keys())

        index = pig_names.index(filename)

        self.beginRemoveRows(QtCore.QModelIndex(), index, index)

        self._pigs_pool.remove_reader(filename)

        self.endRemoveRows()

        self.reader_removed.emit(filename)

    def data(self, index, role):
        """
        """

        if not index.isValid():
            return QtCore.QVariant()

        pigs = self._pigs_pool.pigs

        pig_names = list(pigs.keys())

        selected_pig = pig_names[index.row()]

        reader = self._pigs_pool.get_reader(selected_pig)

        if role == QtCore.Qt.DisplayRole:
            return selected_pig
        elif role == QtCore.Qt.ToolTipRole:
            return "\n".join([": ".join([k, v]) for k, v in reader.parameters.items()])
        elif role == PigsPoolModel.Reader:
            return reader
        else:
            return QtCore.QVariant()

    def flags(self, index):

        default_flags = super(PigsPoolModel, self).flags(index)

        if index.isValid():
            return QtCore.Qt.ItemIsDragEnabled | default_flags

    def get_pig(self, pig_name):

        pigs = self._pigs_pool.pigs

        return pigs.get(pig_name, None)

    def rowCount(self, parent=None):

        return len(self._pigs_pool)
