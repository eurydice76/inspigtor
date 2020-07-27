import glob
import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

import inspigtor
from inspigtor.__pkginfo__ import __version__
from inspigtor.gui.dialogs.property_plotter_dialog import PropertyPlotterDialog
from inspigtor.gui.models.pigs_data_model import PigsDataModel
from inspigtor.gui.models.pandas_data_model import PandasDataModel
from inspigtor.gui.views.pigs_view import PigsView
from inspigtor.gui.widgets.copy_pastable_tableview import CopyPastableTableView
from inspigtor.gui.widgets.intervals_widget import IntervalsWidget
from inspigtor.gui.widgets.logger_widget import QTextEditLogger
from inspigtor.gui.widgets.statistics_widget import StatisticsWidget
from inspigtor.readers.picco2_reader import PiCCO2FileReader


class MainWindow(QtWidgets.QMainWindow):
    """This class implements the main window of the inspigtor application.
    """

    pig_selected = QtCore.pyqtSignal(PiCCO2FileReader, list)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Build the signal/slots.
        """

        self._data_table.customContextMenuRequested.connect(self.on_show_data_table_menu)
        self._pigs_list.double_clicked_empty.connect(self.on_load_experiment_data)
        self._intervals_widget.record_interval_selected.connect(self.on_record_interval_selected)
        self._intervals_widget.update_properties.connect(self.on_update_properties)
        self.pig_selected.connect(self._intervals_widget.on_update_record_intervals)
        self._selected_property_combo.currentTextChanged.connect(self.on_change_selected_property)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(self._pigs_list)

        selected_property_layout = QtWidgets.QHBoxLayout()
        selected_property_layout.addWidget(self._selected_property_label)
        selected_property_layout.addWidget(self._selected_property_combo)
        vlayout.addLayout(selected_property_layout)

        hlayout.addLayout(vlayout)

        hlayout.addWidget(self._tabs)

        main_layout.addLayout(hlayout, stretch=3)

        main_layout.addWidget(self._data_table, stretch=3)

        main_layout.addWidget(self._logger.widget, stretch=2)

        self._main_frame.setLayout(main_layout)

    def build_menu(self):
        """Build the menu.
        """

        file_action = QtWidgets.QAction(QtGui.QIcon('file.png'), '&File', self)
        file_action.setShortcut('Ctrl+O')
        file_action.setStatusTip('Open experimental directories')
        file_action.triggered.connect(self.on_load_experiment_data)

        exit_action = QtWidgets.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.on_quit_application)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')

        file_menu.addAction(file_action)
        file_menu.addAction(exit_action)

    def build_widgets(self):
        """Build the widgets.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._pigs_list = PigsView()
        self._pigs_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self._pigs_list.setDragEnabled(True)
        pigs_model = PigsDataModel()
        self._pigs_list.setModel(pigs_model)
        self._pigs_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._selected_property_label = QtWidgets.QLabel('Selected property')

        self._selected_property_combo = QtWidgets.QComboBox()

        self._data_table = CopyPastableTableView()
        self._data_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 1200, 1000)

        self.setWindowTitle("inspigtor {}".format(__version__))

        self._tabs = QtWidgets.QTabWidget()

        self._intervals_widget = IntervalsWidget(pigs_model, self)
        self._statistics_widget = StatisticsWidget(pigs_model, self)

        self._tabs.addTab(self._intervals_widget, 'Intervals')
        self._tabs.addTab(self._statistics_widget, 'Statistics')

        self._logger = QTextEditLogger(self)
        self._logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self._logger)
        logging.getLogger().setLevel(logging.INFO)

        self._progress_label = QtWidgets.QLabel('Progress')
        self._progress_bar = QtWidgets.QProgressBar()
        self.statusBar().showMessage("inspigtor {}".format(__version__))
        self.statusBar().addPermanentWidget(self._progress_label)
        self.statusBar().addPermanentWidget(self._progress_bar)

        icon_path = os.path.join(inspigtor.__path__[0], "icons", "icon.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.show()

    def init_progress_bar(self, n_steps):
        """Initializes the progress bar.

        Args:
            n_steps (int): the total number of steps of the task to monitor
        """

        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_steps)

    def init_ui(self):
        """Initializes the ui.
        """

        self._reader = None

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    def on_change_selected_property(self, selected_property):
        """Event fired when the user change the property to compute the statistics with.

        Args:
            selected_property (str): the selected property

        """

        self._pigs_list.model().selected_property = selected_property

    def on_load_experiment_data(self):
        """Event fired when the user loads expriment data by clicking on File -> Open or double clicking on the data list view when it is empty.
        """

        # Pop up a file browser
        csv_files = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', '', 'Data Files (*.csv)')[0]
        if not csv_files:
            return

        pigs_model = self._pigs_list.model()

        n_csv_files = len(csv_files)
        self.init_progress_bar(n_csv_files)

        n_loaded_files = 0

        # Loop over the pig directories
        for progress, csv_file in enumerate(csv_files):

            if pigs_model.findItems(csv_file, QtCore.Qt.MatchExactly):
                continue

            item = QtGui.QStandardItem(csv_file)
            try:
                # Reads the csv file and bind it to the model's item
                reader = PiCCO2FileReader(csv_file)
            except IOError as err:
                logging.error(str(err))
                continue
            item.setData(reader, 257)

            # The tooltip will be the parameters found in the csv file
            item.setData("\n".join([": ".join([k, v]) for k, v in reader.parameters.items()]), QtCore.Qt.ToolTipRole)
            pigs_model.appendRow(item)

            n_loaded_files += 1
            self.update_progress_bar(progress+1)

        # Create a signal/slot connexion for row changed event
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

        self._pigs_list.setCurrentIndex(pigs_model.index(0, 0))

        logging.info('Loaded successfully {} files over {}'.format(n_loaded_files, n_csv_files))

    def on_plot_property(self, checked, selected_property):
        """Plot one property of the PiCCO file.

        Args:
            selected_property (str): the property to plot
        """

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

    def on_record_interval_selected(self, row_min, row_max):
        """Event fired when the user clicks on one record interval. This will gray the corresponding data for better readability.

        Args:
            row_min (int): the first index of the record interval
            row_max (int): the last of the record interval (excluded)
        """

        model = self._data_table.model()

        # Color in grey the selected record interval
        model.setColoredRows(dict([(r, QtGui.QColor('gray')) for r in range(row_min, row_max)]))

        # Displace the cursor of the data table to the first index of the selected record interval
        index = model.index(row_min, 0)
        self._data_table.setCurrentIndex(index)

    def on_select_pig(self, index):
        """Event fired when a pig is selected.

        Args:
            index (PyQt5.QtCore.QModelIndex): the index of the pig in the corresponding list view
        """

        item = self._pigs_list.model().item(index.row(), index.column())

        reader = item.data(257)
        if reader is None:
            return

        # Update the data table with the selected data
        data = reader.data
        self._data_table.setModel(PandasDataModel(data))

        reader = item.data(257)
        record_intervals = reader.record_intervals
        if record_intervals is None:
            record_intervals = []

        self.pig_selected.emit(reader, record_intervals)

    def on_show_data_table_menu(self, point):
        """Event fired when the user right-clicks on the data table.

        This will pop up a contextual menu.
        """

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

    def on_update_properties(self, properties):
        """Event fired when a pig is loaded.

        This will refresh the properties combo box with the properties available in the corresponding PiCCO file.

        Args:
            properties (list of str): the properties
        """

        # Reset the property combobox
        self._selected_property_combo.clear()
        self._selected_property_combo.addItems(properties)
        index = self._selected_property_combo.findText('APs', QtCore.Qt.MatchFixedString)
        if index >= 0:
            self._selected_property_combo.setCurrentIndex(index)

    def update_progress_bar(self, step):
        """Updates the progress bar.

        Args:
            step (int): the step
        """

        self._progress_bar.setValue(step)
