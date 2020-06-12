import glob
import os
import sys

import numpy as np

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

import inspigtor
from inspigtor.__pkginfo__ import __version__
from inspigtor.readers.PiCCO2Reader import PiCCO2FileReader
from inspigtor.gui.widgets.MultipleDirectoriesSelector import MultipleDirectoriesSelector
from inspigtor.gui.models.pandas_data_model import PandasDataModel


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Set the signal:slots of the main window
        """

        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

    def build_layout(self):
        """Build the layout of the main window.
        """

        self._vl = QtWidgets.QVBoxLayout()

        self._hl = QtWidgets.QHBoxLayout()

        self._hl.addWidget(self._pigs_list)
        self._hl.addWidget(self._intervals_list)

        self._vl.addLayout(self._hl)
        self._vl.addWidget(self._data_table)

        self._main_frame.setLayout(self._vl)

    def build_menu(self):
        """Build the menu of the main window.
        """

        file_action = QtWidgets.QAction(QtGui.QIcon('file.png'), '&File', self)
        file_action.setShortcut('Ctrl+O')
        file_action.setStatusTip('Open experimental directories')
        file_action.triggered.connect(self.on_open_experimental_dirs)

        exit_action = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.on_quit_application)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')

        file_menu.addAction(file_action)
        file_menu.addAction(exit_action)

    def build_widgets(self):
        """Build the widgets of the main window.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._pigs_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._pigs_list.setModel(model)
        self._pigs_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._intervals_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._data_table = QtWidgets.QTableView()
        self._data_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 800, 800)

        self.setWindowTitle("inspigtor {}".format(__version__))

        self.statusBar().showMessage("inspigtor {}".format(__version__))

        icon_path = os.path.join(inspigtor.__path__[0], "icons", "icon.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.show()

    def init_ui(self):
        """Set the widgets of the main window
        """

        self._reader = None

        self.build_menu()

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def on_open_experimental_dirs(self):
        """Opens several experimental directories.
        """

        # Pop up a file browser
        selector = MultipleDirectoriesSelector()
        if not selector.exec_():
            return

        experimental_dirs = selector.selectedFiles()
        if not experimental_dirs:
            return

        self._experimental_base_dir = os.path.dirname(experimental_dirs[0])

        model = QtGui.QStandardItemModel()
        self._pigs_list.setModel(model)
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

        for exp_dir in experimental_dirs:

            exp_dir_basename = os.path.basename(exp_dir)
            data_files = glob.glob(os.path.join(exp_dir, 'Data*.csv'))

            for data_file in data_files:
                data_file_basename = os.path.basename(data_file)
                data_file_basename = os.path.splitext(data_file_basename)[0]
                item = QtGui.QStandardItem('-'.join([exp_dir_basename, data_file_basename]))
                reader = PiCCO2FileReader(data_file)
                item.setData(reader)
                model.appendRow(item)

    def on_quit_application(self):
        """Event handler when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(self, 'Quit',
                                                "Do you really want to quit?",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def on_select_interval(self, index):
        """Event handler for interval selection.

        It will grey th data table for the corresponding interval
        """

        item = self._intervals_list.model().item(index.row(), index.column())

        row_min, row_max = item.data()

        model = self._data_table.model()

        model.setColoredRows(dict([(r, QtGui.QColor('gray')) for r in range(row_min, row_max)]))

    def on_select_pig(self, index):

        item = self._pigs_list.model().item(index.row(), index.column())

        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        reader = item.data()

        for i, interval in enumerate(reader):
            item = QtGui.QStandardItem('interval {}'.format(i+1))
            item.setData(interval)
            model.appendRow(item)

        data = reader.data

        self._data_table.setModel(PandasDataModel(data))


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec_())
