import glob
import os
import sys

import numpy as np

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

import inspigtor
from inspigtor.__pkginfo__ import __version__
from inspigtor.readers.picco2_reader import PiCCO2FileReader
from inspigtor.gui.dialogs.property_plotter_dialog import PropertyPlotterDialog
from inspigtor.gui.dialogs.stats_results_dialog import StatsResultsDialog
from inspigtor.gui.models.pandas_data_model import PandasDataModel
from inspigtor.gui.widgets.multiple_directories_selector import MultipleDirectoriesSelector
from inspigtor.gui.widgets.pigs_view import PigsView


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Set the signal:slots of the main window
        """

        self._compute_button.clicked.connect(self.on_compute_averages)
        self._search_valid_intervals_button.clicked.connect(self.on_search_valid_intervals)
        self._search_intervals_button.clicked.connect(self.on_search_record_intervals)
        self._pigs_list.double_clicked_empty.connect(self.on_open_experimental_dirs)
        self._data_table.customContextMenuRequested.connect(self.on_show_data_table_menu)

    def build_layout(self):
        """Build the layout of the main window.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hl1 = QtWidgets.QHBoxLayout()

        self._valid_interval_layout = QtWidgets.QHBoxLayout()
        self._valid_interval_layout.addWidget(self._valid_property_combo)
        self._valid_interval_layout.addWidget(self._search_valid_intervals_button)

        hl111 = QtWidgets.QHBoxLayout()

        hl111.addWidget(self._times_groupbox)
        hl1111 = QtWidgets.QHBoxLayout()

        hl1111.addWidget(self._t_record_label)
        hl1111.addWidget(self._t_record)
        hl1111.addWidget(self._t_offset_label)
        hl1111.addWidget(self._t_offset)
        hl1111.addWidget(self._t_merge_label)
        hl1111.addWidget(self._t_merge)

        self._times_groupbox.setLayout(hl1111)

        hl112 = QtWidgets.QHBoxLayout()
        hl112.addWidget(self._search_intervals_button)

        hl113 = QtWidgets.QHBoxLayout()
        hl113.addWidget(self._compute_property_combo)
        hl113.addWidget(self._compute_button)

        vl11 = QtWidgets.QVBoxLayout()
        vl11.addWidget(self._pigs_list)
        vl11.addLayout(self._valid_interval_layout)
        vl11.addLayout(hl111)
        vl11.addLayout(hl112)
        vl11.addLayout(hl113)

        hl1.addLayout(vl11)
        hl1.addWidget(self._intervals_list)

        main_layout.addLayout(hl1)

        main_layout.addWidget(self._data_table)

        self._main_frame.setLayout(main_layout)

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

        self._pigs_list = PigsView()
        model = QtGui.QStandardItemModel()
        self._pigs_list.setModel(model)
        self._pigs_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._valid_property_combo = QtWidgets.QComboBox()
        self._search_valid_intervals_button = QtWidgets.QPushButton('Search valid intervals')

        self._times_groupbox = QtWidgets.QGroupBox('Times (s)')

        self._t_record_label = QtWidgets.QLabel('Record')
        self._t_record_label.setToolTip('The duration of for which the time will be considered for further analysis.')
        self._t_record = QtWidgets.QSpinBox()
        self._t_record.setMinimum(0)
        self._t_record.setMaximum(10000)
        self._t_record.setValue(300)

        self._t_offset_label = QtWidgets.QLabel('Offset')
        self._t_offset_label.setToolTip('The offset preceeding each recording.')
        self._t_offset = QtWidgets.QSpinBox()
        self._t_offset.setMinimum(0)
        self._t_offset.setValue(60)

        self._t_merge_label = QtWidgets.QLabel('Merge')
        self._t_merge_label.setToolTip('The time used to merge those intervals whose gap in time is smaller than the input value.')
        self._t_merge = QtWidgets.QSpinBox()
        self._t_merge.setMinimum(0)
        self._t_merge.setValue(0)

        self._search_intervals_button = QtWidgets.QPushButton('Search record intervals')

        self._compute_property_combo = QtWidgets.QComboBox()
        self._compute_button = QtWidgets.QPushButton('Compute averages')

        self._intervals_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._data_table = QtWidgets.QTableView()
        self._data_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

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

        model = self._pigs_list.model()

        n_pigs = model.rowCount()

        if n_pigs == 0:
            return

        selected_property = self._compute_property_combo.currentText()

        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_pigs)

        # Loop over the pigs
        for row in range(n_pigs):

            # Fetch the pig's reader
            model_index = model.index(row, 0)
            current_item = model.item(row, 0)
            reader = model.data(model_index, 257)
            data = reader.data

            # Fetch the record interval
            record_intervals = model.data(model_index, 258)

            results = {'selected_property': selected_property, 'stats': []}

            # Compute for each record interval the average and standard deviation of the selected property
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

    def on_plot_property(self, checked, selected_property):
        """Plot one property of the PiCCO file.

        Args:
            selected_property (str): the property to plot
        """

        data_model = self._data_table.model()

        pigs_model = self._pigs_list.model()

        # Fetch the selected reader
        selected_row = self._pigs_list.currentIndex().row()
        reader = pigs_model.item(selected_row, 0).data(257)

        # Build the x and y values
        xs = []
        ys = []
        for i, v in enumerate(reader.data[selected_property][:]):
            try:
                value = float(v)
            except ValueError:
                pass
            else:
                xs.append(i)
                ys.append(value)

        if not ys:
            return

        # Pops up a plot of the selected property
        dialog = PropertyPlotterDialog(self)
        dialog.plot_property(selected_property, xs, ys)
        dialog.show()

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

        t_record = self._t_record.value()
        t_offset = self._t_offset.value()
        t_merge = self._t_merge.value()

        model = self._pigs_list.model()

        n_pigs = model.rowCount()
        if n_pigs == 0:
            return

        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_pigs)

        for row in range(n_pigs):
            model_index = model.index(row, 0)
            reader = model.data(model_index, 257)
            record_intervals = reader.get_record_intervals(t_record, t_offset=t_offset, t_merge=t_merge)

            # Set the record intervals as new data (id 258)
            current_item = model.item(row, 0)
            current_item.setData(record_intervals, 258)
            current_item.setData({}, 259)

            self._progress_bar.setValue(row+1)

        self.on_select_pig(model.index(0, 0))

    def on_search_valid_intervals(self):

        pigs_model = self._pigs_list.model()

        n_pigs = pigs_model.rowCount()
        if n_pigs == 0:
            return

        selected_property = self._valid_property_combo.currentText()

        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_pigs)

        for row in range(n_pigs):

            current_item = pigs_model.item(row, 0)
            reader = current_item.data(257)

            reader.set_valid_intervals(selected_property=selected_property)

            self._progress_bar.setValue(row+1)

    def on_select_interval(self, index):
        """Event handler for interval selection.

        It will grey the data table for the corresponding interval
        """

        model = self._intervals_list.model()

        item = model.item(index.row(), index.column())

        row_min, row_max = item.data()

        model = self._data_table.model()

        # Color in grey the selected record interval
        model.setColoredRows(dict([(r, QtGui.QColor('gray')) for r in range(row_min, row_max)]))

        # Displace the cursor of the data table to the first index of the selected record interval
        index = model.index(row_min, 0)
        self._data_table.setCurrentIndex(index)

    def on_select_pig(self, index):

        item = self._pigs_list.model().item(index.row(), index.column())

        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        reader = item.data(257)
        if reader is None:
            return

        # Update the data table with the selected data
        data = reader.data
        self._data_table.setModel(PandasDataModel(data))

        self._valid_property_combo.clear()
        self._valid_property_combo.addItems(data.columns)
        index = self._valid_property_combo.findText('APs', QtCore.Qt.MatchFixedString)
        if index >= 0:
            self._valid_property_combo.setCurrentIndex(index)

        self._compute_property_combo.clear()
        self._compute_property_combo.addItems(data.columns)
        index = self._compute_property_combo.findText('APs', QtCore.Qt.MatchFixedString)
        if index >= 0:
            self._compute_property_combo.setCurrentIndex(index)

        record_intervals = item.data(258)
        if record_intervals is None:
            return

        for i, interval in enumerate(record_intervals):
            item = QtGui.QStandardItem('interval {}'.format(i+1))
            item.setData(interval)
            model.appendRow(item)

    def on_show_data_table_menu(self, point):

        data_model = self._data_table.model()

        if data_model is None:
            return

        menu = QtWidgets.QMenu()

        plot_menu = QtWidgets.QMenu('Plot')

        pigs_model = self._pigs_list.model()
        reader = pigs_model.item(self._pigs_list.currentIndex().row(), 0).data(257)

        properties = reader.data.columns
        for prop in properties:
            action = plot_menu.addAction(prop)
            action.triggered.connect(lambda checked, prop=prop: self.on_plot_property(checked, prop))

        menu.addMenu(plot_menu)
        menu.exec_(QtGui.QCursor.pos())


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec_())
