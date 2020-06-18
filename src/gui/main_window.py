import glob
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

import inspigtor
from inspigtor.__pkginfo__ import __version__
from inspigtor.gui.dialogs.property_plotter_dialog import PropertyPlotterDialog
from inspigtor.gui.models.pandas_data_model import PandasDataModel
from inspigtor.gui.views.pigs_view import PigsView
from inspigtor.gui.widgets.intervals_widget import IntervalsWidget
from inspigtor.gui.widgets.multiple_directories_selector import MultipleDirectoriesSelector
from inspigtor.gui.widgets.statistics_widget import StatisticsWidget
from inspigtor.readers.picco2_reader import PiCCO2FileReader


class MainWindow(QtWidgets.QMainWindow):

    pig_selected = QtCore.pyqtSignal(PiCCO2FileReader, list)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):

        self._data_table.customContextMenuRequested.connect(self.on_show_data_table_menu)
        self._pigs_list.double_clicked_empty.connect(self.on_open_experimental_dirs)
        self._intervals_widget.record_interval_selected.connect(self.on_record_interval_selected)

    def build_layout(self):
        """Build the layout of the main window.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self._pigs_list)
        hlayout.addWidget(self._tabs)

        main_layout.addLayout(hlayout)

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
        self._pigs_list.setDragEnabled(True)
        model = QtGui.QStandardItemModel()
        self._pigs_list.setModel(model)
        self._pigs_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._data_table = QtWidgets.QTableView()
        self._data_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 800, 800)

        self.setWindowTitle("inspigtor {}".format(__version__))

        self._tabs = QtWidgets.QTabWidget()

        self._intervals_widget = IntervalsWidget(self)
        self._statistics_widget = StatisticsWidget(self)

        self._tabs.addTab(self._intervals_widget, 'Intervals')
        self._tabs.addTab(self._statistics_widget, 'Statistics')

        self._progress_label = QtWidgets.QLabel('Progress')
        self._progress_bar = QtWidgets.QProgressBar()
        self.statusBar().showMessage("inspigtor {}".format(__version__))
        self.statusBar().addPermanentWidget(self._progress_label)
        self.statusBar().addPermanentWidget(self._progress_bar)

        icon_path = os.path.join(inspigtor.__path__[0], "icons", "icon.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.show()

    def init_progress_bar(self, n_steps):

        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(n_steps)

    def init_ui(self):
        """Set the widgets of the main window
        """

        self._reader = None

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    @property
    def intervals_widget(self):

        return self._intervals_widget

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

        self.init_progress_bar(len(experimental_dirs))

        filenames = []

        # Loop over the pig directories
        for progress, exp_dir in enumerate(experimental_dirs):

            exp_dir_basename = os.path.basename(exp_dir)
            data_files = glob.glob(os.path.join(exp_dir, 'Data*.csv'))

            # Loop over the Data*csv csv files found in the current oig directory
            for data_file in data_files:
                data_file_basename = os.path.basename(data_file)
                filename = os.path.join(exp_dir_basename, data_file_basename)
                item = QtGui.QStandardItem(filename)
                # Reads the csv file and bind it to the model's item
                reader = PiCCO2FileReader(data_file)
                item.setData(reader, 257)

                # The tooltip will be the parameters found in the csv file
                item.setData("\n".join([": ".join([k, v]) for k, v in reader.parameters.items()]), QtCore.Qt.ToolTipRole)
                model.appendRow(item)

                filenames.append(filename)

            self.update_progress_bar(progress+1)

        # Create a signal/slot connexion for row changed event
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

        self._pigs_list.setCurrentIndex(self._pigs_list.model().index(0, 0))

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

        model = self._data_table.model()

        # Color in grey the selected record interval
        model.setColoredRows(dict([(r, QtGui.QColor('gray')) for r in range(row_min, row_max)]))

        # Displace the cursor of the data table to the first index of the selected record interval
        index = model.index(row_min, 0)
        self._data_table.setCurrentIndex(index)

    def on_select_pig(self, index):

        item = self._pigs_list.model().item(index.row(), index.column())

        reader = item.data(257)
        if reader is None:
            return

        # Update the data table with the selected data
        data = reader.data
        self._data_table.setModel(PandasDataModel(data))

        record_intervals = item.data(258)
        if record_intervals is None:
            record_intervals = []

        self.pig_selected.emit(reader, record_intervals)

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

    @property
    def pigs_list(self):
        return self._pigs_list

    def update_progress_bar(self, step):

        self._progress_bar.setValue(step)


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()

    sys.exit(app.exec_())
