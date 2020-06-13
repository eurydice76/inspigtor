import glob
import os
import sys

import numpy as np

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

import inspigtor
from inspigtor.__pkginfo__ import __version__
from inspigtor.readers.picco2_reader import PiCCO2FileReader
from inspigtor.gui.dialogs.stats_results_dialog import StatsResultsDialog
from inspigtor.gui.models.pandas_data_model import PandasDataModel
from inspigtor.gui.widgets.multiple_directories_selector import MultipleDirectoriesSelector


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Set the signal:slots of the main window
        """

        self._compute_button.clicked.connect(self.on_compute_averages)
        self._search_intervals_button.clicked.connect(self.on_search_record_intervals)

    def build_layout(self):
        """Build the layout of the main window.
        """

        self._main_layout = QtWidgets.QVBoxLayout()

        self._hl1 = QtWidgets.QHBoxLayout()

        self._vl11 = QtWidgets.QVBoxLayout()
        self._vl11.addWidget(self._pigs_list)
        self._hl111 = QtWidgets.QHBoxLayout()
        self._hl111.addWidget(self._t_offset_label)
        self._hl111.addWidget(self._t_offset)
        self._hl111.addWidget(self._t_record_label)
        self._hl111.addWidget(self._t_record)

        self._hl112 = QtWidgets.QHBoxLayout()
        self._hl112.addWidget(self._search_intervals_button)

        self._hl113 = QtWidgets.QHBoxLayout()
        self._hl113.addWidget(self._selected_property_combo)
        self._hl113.addWidget(self._compute_button)

        self._vl11.addLayout(self._hl111)
        self._vl11.addLayout(self._hl112)
        self._vl11.addLayout(self._hl113)

        self._hl1.addLayout(self._vl11)
        self._hl1.addWidget(self._intervals_list)

        self._main_layout.addLayout(self._hl1)

        self._main_layout.addWidget(self._data_table)

        self._main_frame.setLayout(self._main_layout)

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

        self._t_offset_label = QtWidgets.QLabel()
        self._t_offset_label.setText('Offset (s)')
        self._t_offset = QtWidgets.QSpinBox()
        self._t_offset.setMinimum(0)
        self._t_offset.setValue(60)

        self._t_record_label = QtWidgets.QLabel()
        self._t_record_label.setText('Record (s)')
        self._t_record = QtWidgets.QSpinBox()
        self._t_record.setMinimum(0)
        self._t_record.setMaximum(10000)
        self._t_record.setValue(300)

        self._search_intervals_button = QtWidgets.QPushButton('Search record intervals')

        self._selected_property_combo = QtWidgets.QComboBox()
        self._compute_button = QtWidgets.QPushButton('Compute averages')

        self._intervals_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._data_table = QtWidgets.QTableView()
        self._data_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 800, 800)

        self.setWindowTitle("inspigtor {}".format(__version__))

        self._progress_label = QtWidgets.QLabel('Progress')
        self._progress_bar = QtWidgets.QProgressBar()
        self.statusBar().showMessage("inspigtor {}".format(__version__))
        self.statusBar().addPermanentWidget(self._progress_label)
        self.statusBar().addPermanentWidget(self._progress_bar)

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

    def on_compute_averages(self):
        """Computes the average of a given property
        """

        selected_property = self._selected_property_combo.currentText()

        model = self._pigs_list.model()

        n_pigs = model.rowCount()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_pigs)

        for row in range(n_pigs):
            model_index = model.index(row, 0)

            current_item = model.item(row, 0)

            reader = model.data(model_index, 257)
            data = reader.data

            record_intervals = model.data(model_index, 258)

            results = {'selected_property': selected_property, 'stats': []}

            for interval in record_intervals:
                first_index, last_index = interval
                values = []
                for i in range(first_index, last_index):
                    try:
                        values.append(float(data[selected_property].iloc[i]))
                    except ValueError:
                        continue
                if not values:
                    results['stats'].append(None)
                else:
                    avg = np.average(values)
                    std = np.std(values)
                    results['stats'].append((avg, std))

            current_item.setData(results, 259)
            self._progress_bar.setValue(row+1)

        dialog = StatsResultsDialog(self)
        dialog.exec_()

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

        model = QtGui.QStandardItemModel()
        self._pigs_list.setModel(model)

        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(len(experimental_dirs))

        # Loop over the pig directories
        for progress, exp_dir in enumerate(experimental_dirs):

            exp_dir_basename = os.path.basename(exp_dir)
            data_files = glob.glob(os.path.join(exp_dir, 'Data*.csv'))

            # Loop over the Data*csv csv files found in the current oig directory
            for data_file in data_files:
                data_file_basename = os.path.basename(data_file)
                item = QtGui.QStandardItem(os.path.join(exp_dir_basename, data_file_basename))
                # Reads the csv file and bind it to the model's item
                reader = PiCCO2FileReader(data_file)
                item.setData(reader, 257)

                # The tooltip will be the parameters found in the csv file
                item.setData("\n".join([": ".join([k, v]) for k, v in reader.parameters.items()]), QtCore.Qt.ToolTipRole)
                model.appendRow(item)

            self._progress_bar.setValue(progress+1)

        # Create a signal/slot connexion for row changed event
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

    def on_quit_application(self):
        """Event handler when the application is exited.
        """

        choice = QtWidgets.QMessageBox.question(self, 'Quit', "Do you really want to quit?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if choice == QtWidgets.QMessageBox.Yes:
            sys.exit()

    def on_search_record_intervals(self):
        """Event handler called when the search record intervals buton is clicked.

        Compute for the selected pig the record intervals.
        """

        t_offset = self._t_offset.value()
        t_record = self._t_record.value()

        model = self._pigs_list.model()

        n_pigs = model.rowCount()
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_pigs)

        for row in range(n_pigs):
            model_index = model.index(row, 0)
            reader = model.data(model_index, 257)
            record_intervals = reader.get_record_intervals(t_record,t_offset)

            # Set the record intervals as new data (id 258)
            current_item = model.item(row, 0)
            current_item.setData(record_intervals, 258)
            current_item.setData({}, 259)

            self._progress_bar.setValue(row+1)

        self.on_select_pig(model.index(0, 0))

    def on_select_interval(self, index):
        """Event handler for interval selection.

        It will grey the data table for the corresponding interval
        """

        model = self._intervals_list.model()

        item = model.item(index.row(), index.column())

        row_min, row_max = item.data()

        model = self._data_table.model()

        model.setColoredRows(dict([(r, QtGui.QColor('gray')) for r in range(row_min, row_max)]))

    def on_select_pig(self, index):

        item = self._pigs_list.model().item(index.row(), index.column())

        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        reader = item.data(257)
        if reader is None:
            return

        data = reader.data

        self._data_table.setModel(PandasDataModel(data))

        self._selected_property_combo.clear()
        self._selected_property_combo.addItems(data.columns)

        record_intervals = item.data(258)
        if record_intervals is None:
            return

        for i, interval in enumerate(record_intervals):
            item = QtGui.QStandardItem('interval {}'.format(i+1))
            item.setData(interval)
            model.appendRow(item)


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec_())
