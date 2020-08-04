from PyQt5 import QtWidgets


class MultipleDirectoriesSelector(QtWidgets.QFileDialog):
    def __init__(self, *args):

        super(MultipleDirectoriesSelector, self).__init__(*args)

        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        self.tree = self.findChild(QtWidgets.QTreeView)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.list = self.findChild(QtWidgets.QListView)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
