import collections
import glob
import logging
import os
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

import inspigtor
from inspigtor.__pkginfo__ import __version__
from inspigtor.gui.dialogs.individual_averages_dialog import IndividualAveragesDialog
from inspigtor.gui.dialogs.property_plotter_dialog import PropertyPlotterDialog
from inspigtor.gui.models.pigs_pool_model import PigsPoolModel
from inspigtor.gui.models.pandas_data_model import PandasDataModel
from inspigtor.gui.views.copy_pastable_tableview import CopyPastableTableView
from inspigtor.gui.views.double_clickable_listview import DoubleClickableListView
from inspigtor.gui.widgets.intervals_widget import IntervalsWidget
from inspigtor.gui.widgets.logger_widget import QTextEditLogger
from inspigtor.gui.widgets.multiple_directories_selector import MultipleDirectoriesSelector
from inspigtor.gui.widgets.statistics_widget import StatisticsWidget
from inspigtor.kernel.readers.picco2_reader import PiCCO2FileReader, PiCCO2FileReaderError
from inspigtor.kernel.utils.progress_bar import progress_bar


class MainWindow(QtWidgets.QMainWindow):
    """This class implements the main window of the inspigtor application.
    """

    pig_selected = QtCore.pyqtSignal(PiCCO2FileReader, list)

    add_new_group = QtCore.pyqtSignal(str)

    display_group_averages = QtCore.pyqtSignal()

    display_group_effect_statistics = QtCore.pyqtSignal()

    display_time_effect_statistics = QtCore.pyqtSignal()

    display_premortem_statistics = QtCore.pyqtSignal()

    export_group_statistics = QtCore.pyqtSignal()

    display_group_medians = QtCore.pyqtSignal()

    import_groups_from_directories = QtCore.pyqtSignal(dict)

    def __init__(self, parent=None):
        """Constructor.
        """

        super(MainWindow, self).__init__(parent)

        self.init_ui()

    def build_events(self):
        """Build the signal/slots.
        """

        self._data_table.customContextMenuRequested.connect(self.on_show_data_table_menu)
        self._pigs_list.double_clicked_empty.connect(self.on_load_experiment_data)
        self._pigs_list.customContextMenuRequested.connect(self.on_show_pigs_list_menu)
        self._intervals_widget.record_interval_selected.connect(self.on_record_interval_selected)
        self._intervals_widget.update_properties.connect(self.on_update_properties)
        self.pig_selected.connect(self._intervals_widget.on_update_record_intervals)
        self._selected_property_combo.currentTextChanged.connect(self.on_change_selected_property)
        self._show_individual_averages_button.clicked.connect(self.on_show_individual_averages)
        self._pigs_list.model().reader_removed.connect(self._statistics_widget.on_remove_reader)

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

        vlayout.addWidget(self._show_individual_averages_button)

        hlayout.addLayout(vlayout)

        hlayout.addWidget(self._tabs)

        main_layout.addLayout(hlayout, stretch=3)

        main_layout.addWidget(self._data_table, stretch=3)

        main_layout.addWidget(self._logger.widget, stretch=2)

        self._main_frame.setLayout(main_layout)

    def build_menu(self):
        """Build the menu.
        """

        menubar = self.menuBar()

        file_menu = menubar.addMenu('&File')

        file_action = QtWidgets.QAction('&Open PiCCO2 file', self)
        file_action.setShortcut('Ctrl+O')
        file_action.setStatusTip('Open PiCCO2 (csv) files')
        file_action.triggered.connect(self.on_load_experiment_data)
        file_menu.addAction(file_action)

        dir_action = QtWidgets.QAction('&Open PiCCO2 directories', self)
        dir_action.setShortcut('Ctrl+I')
        dir_action.setStatusTip('Open PiCCO2 (csv) files')
        dir_action.triggered.connect(self.on_load_experimental_dirs)
        file_menu.addAction(dir_action)

        file_menu.addSeparator()

        exit_action = QtWidgets.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit inspigtor')
        exit_action.triggered.connect(self.on_quit_application)
        file_menu.addAction(exit_action)

        group_menu = menubar.addMenu('&Groups')
        add_group_action = QtWidgets.QAction('&Add group', self)
        add_group_action.setShortcut('Ctrl+R')
        add_group_action.setStatusTip('Add new group')
        add_group_action.triggered.connect(self.on_add_new_group)
        group_menu.addAction(add_group_action)

        import_groups_action = QtWidgets.QAction('&Import from directories', self)
        import_groups_action.setShortcut('Ctrl+U')
        import_groups_action.setStatusTip('Import and create groups from a list of directories')
        import_groups_action.triggered.connect(self.on_import_groups_from_directories)
        group_menu.addAction(import_groups_action)

        group_menu.addSeparator()

        display_group_averages_action = QtWidgets.QAction('&Display averages', self)
        display_group_averages_action.setShortcut('Ctrl+D')
        display_group_averages_action.setStatusTip('Display averages and std for each group')
        display_group_averages_action.triggered.connect(self.on_display_group_averages)
        group_menu.addAction(display_group_averages_action)

        display_group_medians_action = QtWidgets.QAction('Display &medians', self)
        display_group_medians_action.setShortcut('Ctrl+M')
        display_group_medians_action.setStatusTip('Display averages and std for each group')
        display_group_medians_action.triggered.connect(self.on_display_group_medians)
        group_menu.addAction(display_group_medians_action)

        export_group_statistics = QtWidgets.QAction('&Export descriptive statistics', self)
        export_group_statistics.setShortcut('Ctrl+E')
        export_group_statistics.setStatusTip('Export descriptive statistics (average, std, quartile ...)')
        export_group_statistics.triggered.connect(self.on_export_group_statistics)
        group_menu.addAction(export_group_statistics)

        group_menu.addSeparator()

        statistics_menu = menubar.addMenu('&Statistics')

        group_effect_action = QtWidgets.QAction('Group effect', self)
        group_effect_action.setShortcut('Ctrl+G')
        group_effect_action.setStatusTip('Display group effect statistics')
        group_effect_action.triggered.connect(self.on_display_group_effect_statistics)
        statistics_menu.addAction(group_effect_action)

        time_effect_action = QtWidgets.QAction('Time effect', self)
        time_effect_action.setShortcut('Ctrl+T')
        time_effect_action.setStatusTip('Display time effect statistics')
        time_effect_action.triggered.connect(self.on_display_time_effect_statistics)
        statistics_menu.addAction(time_effect_action)

        premortem_action = QtWidgets.QAction('Premortem', self)
        premortem_action.setShortcut('Ctrl+P')
        premortem_action.setStatusTip('Display premortem statistics')
        premortem_action.triggered.connect(self.on_display_premortem_statistics)
        statistics_menu.addAction(premortem_action)

    def build_widgets(self):
        """Build the widgets.
        """

        self._main_frame = QtWidgets.QFrame(self)

        self._pigs_list = DoubleClickableListView()
        self._pigs_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self._pigs_list.setDragEnabled(True)
        pigs_model = PigsPoolModel(self)
        self._pigs_list.setModel(pigs_model)
        self._pigs_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._pigs_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self._selected_property_label = QtWidgets.QLabel('Selected property')

        self._selected_property_combo = QtWidgets.QComboBox()

        self._show_individual_averages_button = QtWidgets.QPushButton('Show individual averages')

        self._data_table = CopyPastableTableView()
        self._data_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._data_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.setCentralWidget(self._main_frame)

        self.setGeometry(0, 0, 1200, 1100)

        self.setWindowTitle("inspigtor {}".format(__version__))

        self._tabs = QtWidgets.QTabWidget()

        self._intervals_widget = IntervalsWidget(pigs_model, self)
        self._statistics_widget = StatisticsWidget(pigs_model, self)

        self._tabs.addTab(self._intervals_widget, 'Intervals')
        self._tabs.addTab(self._statistics_widget, 'Groups')

        self._logger = QTextEditLogger(self)
        self._logger.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self._logger)
        logging.getLogger().setLevel(logging.INFO)

        self._progress_label = QtWidgets.QLabel('Progress')
        self._progress_bar = QtWidgets.QProgressBar()
        progress_bar.set_progress_widget(self._progress_bar)
        self.statusBar().showMessage("inspigtor {}".format(__version__))
        self.statusBar().addPermanentWidget(self._progress_label)
        self.statusBar().addPermanentWidget(self._progress_bar)

        icon_path = os.path.join(inspigtor.__path__[0], "icons", "inspigtor.png")
        self.setWindowIcon(QtGui.QIcon(icon_path))

        self.show()

    def init_ui(self):
        """Initializes the ui.
        """

        self._reader = None

        self.build_widgets()

        self.build_layout()

        self.build_menu()

        self.build_events()

    @property
    def intervals_widget(self):

        return self._intervals_widget

    def on_add_new_group(self):
        """Event fired when the user clicks on 'Add group' menu button.
        """

        group, ok = QtWidgets.QInputDialog.getText(self, 'Enter group name', 'Group name', QtWidgets.QLineEdit.Normal, 'group')

        if ok and group:
            self.add_new_group.emit(group)

    def on_change_selected_property(self, selected_property):
        """Event fired when the user change the property to compute the statistics with.

        Args:
            selected_property (str): the selected property

        """

        # Update the pigs model with the newly selected property
        self._pigs_list.model().selected_property = selected_property

    def on_display_group_averages(self):
        """Event fired when the user clicks on 'Display group averages plot' menu button.
        """

        self.display_group_averages.emit()

    def on_display_group_medians(self):
        """Event fired when the user clicks on 'Display group medians plot' menu button.
        """

        self.display_group_medians.emit()

    def on_display_group_effect_statistics(self):
        """Event fire when the user clicks on 'Display group effect' menu button.
        """

        self.display_group_effect_statistics.emit()

    def on_display_time_effect_statistics(self):
        """Event fire when the user clicks on 'Display time effect' menu button.
        """

        self.display_time_effect_statistics.emit()

    def on_display_premortem_statistics(self):
        """Event fire when the user clicks on 'Display premortem statistics' menu button.
        """

        self.display_premortem_statistics.emit()

    def on_export_group_statistics(self):
        """Event fired when the user clicks on the 'Export statistics' menu button.
        """

        self.export_group_statistics.emit()

    def on_import_groups_from_directories(self):
        """Event fired when the user clicks on Groups -> Import from directories menu button.
        """

        # Pop up a file browser
        selector = MultipleDirectoriesSelector()
        if not selector.exec_():
            return

        experimental_dirs = selector.selectedFiles()
        if not experimental_dirs:
            return

        pigs_model = self._pigs_list.model()

        progress_bar.reset(len(experimental_dirs))

        n_loaded_dirs = 0

        groups = collections.OrderedDict()

        # Loop over the pig directories
        for progress, exp_dir in enumerate(experimental_dirs):

            data_files = glob.glob(os.path.join(exp_dir, '*.csv'))

            # Loop over the Data*csv csv files found in the current oig directory
            for data_file in data_files:
                try:
                    reader = PiCCO2FileReader(data_file)
                except PiCCO2FileReaderError as error:
                    logging.error(str(error))
                    continue
                else:
                    pigs_model.add_reader(reader)
                    groups.setdefault(os.path.basename(exp_dir), []).append(data_file)

            n_loaded_dirs += 1
            progress_bar.update(progress+1)

        # Create a signal/slot connexion for row changed event
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

        self._pigs_list.setCurrentIndex(pigs_model.index(0, 0))

        self.import_groups_from_directories.emit(groups)

        logging.info('Imported successfully {} groups out of {} directories'.format(n_loaded_dirs, len(experimental_dirs)))

    def on_load_experiment_data(self):
        """Event fired when the user loads expriment data by clicking on File -> Open or double clicking on the data list view when it is empty.
        """

        # Pop up a file browser
        csv_files = QtWidgets.QFileDialog.getOpenFileNames(self, 'Open data files', '', 'Data Files (*.csv)')[0]
        if not csv_files:
            return

        pigs_model = self._pigs_list.model()

        n_csv_files = len(csv_files)
        progress_bar.reset(n_csv_files)

        n_loaded_files = 0

        # Loop over the pig directories
        for progress, csv_file in enumerate(csv_files):

            if pigs_model.get_pig(csv_file) is not None:
                continue

            try:
                reader = PiCCO2FileReader(csv_file)
            except PiCCO2FileReaderError as error:
                logging.error(str(error))
                continue
            else:
                pigs_model.add_reader(reader)
                n_loaded_files += 1
            finally:
                progress_bar.update(progress+1)

        # Create a signal/slot connexion for row changed event
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

        self._pigs_list.setCurrentIndex(pigs_model.index(0, 0))

        logging.info('Loaded successfully {} files out of {}'.format(n_loaded_files, n_csv_files))

    def on_load_experimental_dirs(self):
        """Opens several experimental directories.
        """

        # Pop up a file browser
        selector = MultipleDirectoriesSelector()
        if not selector.exec_():
            return

        experimental_dirs = selector.selectedFiles()
        if not experimental_dirs:
            return

        pigs_model = self._pigs_list.model()

        progress_bar.reset(len(experimental_dirs))

        n_loaded_dirs = 0

        # Loop over the pig directories
        for progress, exp_dir in enumerate(experimental_dirs):

            data_files = glob.glob(os.path.join(exp_dir, '*.csv'))

            # Loop over the csv files found in the current oig directory
            for data_file in data_files:
                try:
                    reader = PiCCO2FileReader(data_file)
                except PiCCO2FileReaderError as error:
                    logging.error(str(error))
                    continue
                else:
                    pigs_model.add_reader(reader)

            n_loaded_dirs += 1
            progress_bar.update(progress+1)

        # Create a signal/slot connexion for row changed event
        self._pigs_list.selectionModel().currentChanged.connect(self.on_select_pig)

        self._pigs_list.setCurrentIndex(pigs_model.index(0, 0))

        logging.info('Loaded successfully {} directories out of {}'.format(n_loaded_dirs, len(experimental_dirs)))

    def on_plot_property(self, checked, selected_property):
        """Plot one property of the PiCCO file.

        Args:
            selected_property (str): the property to plot
        """

        pigs_model = self._pigs_list.model()

        # Fetch the selected reader
        selected_row = self._pigs_list.currentIndex().row()
        index = pigs_model.index(selected_row, 0)
        reader = pigs_model.data(index, pigs_model.Reader)

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

        reader = self._pigs_list.model().data(index, PigsPoolModel.Reader)

        if reader == QtCore.QVariant():
            self._data_table.setModel(None)
            return

        # Update the data table with the selected data
        data = reader.data
        self._data_table.setModel(PandasDataModel(data))

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

        menu.addSeparator()

        plot_menu = QtWidgets.QMenu('Plot')

        pigs_model = self._pigs_list.model()
        index = pigs_model.index(self._pigs_list.currentIndex().row(), 0)
        reader = pigs_model.data(index, pigs_model.Reader)

        properties = reader.data.columns
        for prop in properties:
            action = plot_menu.addAction(prop)
            action.triggered.connect(lambda checked, prop=prop: self.on_plot_property(checked, prop))

        menu.addMenu(plot_menu)
        menu.exec_(QtGui.QCursor.pos())

    def on_show_individual_averages(self):
        """Event fired when the menu button for the average of a selected property over a group is clicked.
        """

        pigs_model = self._pigs_list.model()
        n_pigs = pigs_model.rowCount()
        if n_pigs == 0:
            return

        dialog = IndividualAveragesDialog(pigs_model, self)
        dialog.show()

    def on_show_pigs_list_menu(self, point):
        """Event fired when the user right-clicks on the pigs list.

        This will pop up a contextual menu.
        """

        menu = QtWidgets.QMenu()

        write_summary_menu = QtWidgets.QMenu('Write summary')

        pigs_model = self._pigs_list.model()
        if pigs_model.rowCount() == 0:
            return

        current_row = self._pigs_list.currentIndex().row()

        reader = pigs_model.data(pigs_model.index(current_row), pigs_model.Reader)

        properties = reader.data.columns
        for prop in properties:
            action = write_summary_menu.addAction(prop)
            action.triggered.connect(lambda checked, prop=prop: self.on_write_summary(checked, prop))

        menu.addMenu(write_summary_menu)

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

    def on_write_summary(self, checked, selected_property):
        """Event fired when the user click on the 'Write summary' menu button of pigs list contextual menu.
        """

        pigs_model = self._pigs_list.model()

        if pigs_model.rowCount() == 0:
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Write summary as ...', filter="Excel files (*.xls *.xlsx)")
        if not filename:
            return

        filename_noext, ext = os.path.splitext(filename)
        if ext not in ['.xls', '.xlsx']:
            logging.warning('Bad file extension for output excel file {}. It will be replaced by ".xlsx"'.format(filename))
            filename = filename_noext + '.xlsx'

        index = self._pigs_list.currentIndex()
        reader = pigs_model.data(index, pigs_model.Reader)
        try:
            reader.write_summary(filename)
        except PiCCO2FileReaderError as e:
            logging.error(str(e))

    @property
    def selected_property(self):

        return self._selected_property_combo.currentText()
