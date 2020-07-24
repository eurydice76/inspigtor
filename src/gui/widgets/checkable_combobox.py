from PyQt5 import QtCore, QtWidgets


class CheckableComboBox(QtWidgets.QComboBox):
    """This class implements a QComboBox whose items are checkable.
    """

    def __init__(self):
        super(CheckableComboBox, self).__init__()

    def addItem(self, item, userData=None):
        """Add a new checkable item.

        Args:
            item (PyQt5.QtGui.QStandardItem): the itme to add
            userData (object): the data associated with item to add
        """
        super(CheckableComboBox, self).addItem(item, userData=userData)
        item = self.model().item(self.count()-1, 0)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setCheckState(QtCore.Qt.Checked)
