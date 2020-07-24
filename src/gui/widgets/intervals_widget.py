from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.dialogs.interval_settings_dialog import IntervalSettingsDialog
from inspigtor.gui.utils.helper_functions import find_main_window
from inspigtor.gui.widgets.checkable_combobox import CheckableComboBox
from inspigtor.gui.widgets.coverages_widget import CoveragesWidget


class IntervalsWidget(QtWidgets.QWidget):
    """This class implements the widget that store intervals settings.
    """

    record_interval_selected = QtCore.pyqtSignal(int, int)

    update_properties = QtCore.pyqtSignal(list)

    def __init__(self, pigs_model, parent=None):
        super(IntervalsWidget, self).__init__(parent)

        self._pigs_model = pigs_model

        self.init_ui()

    def build_events(self):
        """Build the signal/slots.
        """

        self._clear_intervals_settings_button.clicked.connect(self.on_clear_interval_settings)
        self._add_intervals_settings_button.clicked.connect(self.on_add_interval_settings)
        self._search_record_intervals_button.clicked.connect(self.on_search_record_intervals)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hl1 = QtWidgets.QHBoxLayout()

        hl11 = QtWidgets.QHBoxLayout()

        hl11.addWidget(self._times_groupbox)
        hl111 = QtWidgets.QHBoxLayout()
        hl111.addWidget(self._intervals_settings_combo)
        hl111.addWidget(self._clear_intervals_settings_button)
        hl111.addWidget(self._add_intervals_settings_button)
        self._times_groupbox.setLayout(hl111)

        hl12 = QtWidgets.QHBoxLayout()
        hl12.addWidget(self._search_record_intervals_button)

        vl11 = QtWidgets.QVBoxLayout()
        vl11.addLayout(hl11)
        vl11.addLayout(hl12)
        vl11.addWidget(self._coverages_widget)
        vl11.addStretch()

        hl1.addLayout(vl11, stretch=0)
        hl1.addWidget(self._intervals_list)

        main_layout.addLayout(hl1)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
        """

        self._times_groupbox = QtWidgets.QGroupBox('Times (s)')

        self._intervals_settings_combo = CheckableComboBox()
        self._intervals_settings_combo.setFixedWidth(200)

        self._clear_intervals_settings_button = QtWidgets.QPushButton('Clear')

        self._add_intervals_settings_button = QtWidgets.QPushButton('Add interval')

        self._search_record_intervals_button = QtWidgets.QPushButton('Search record intervals')

        self._intervals_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._coverages_widget = CoveragesWidget(self._pigs_model, self)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def on_add_interval_settings(self):
        """Event fired when the user add a new interval.
        """

        dialog = IntervalSettingsDialog(self)

        if dialog.exec_():
            interval_settings = interval_settings = dialog.value()
            item_text = '{} {} {:d} {:d}'.format(*interval_settings)

            self._intervals_settings_combo.addItem(item_text, userData=interval_settings)

    def on_clear_interval_settings(self):
        """Event fired when the user clears the intervals defined so far.
        """

        self._intervals_settings_combo.clear()

    def on_search_record_intervals(self):
        """Event handler called when the search record intervals button is clicked.

        Compute the record intervals for the selected pig.
        """

        interval_settings = []
        for row in range(self._intervals_settings_combo.count()):
            item = self._intervals_settings_combo.model().item(row, 0)
            if item.checkState() == QtCore.Qt.Unchecked:
                continue
            interval = self._intervals_settings_combo.itemData(row)
            interval_settings.append(interval)

        main_window = find_main_window()
        if main_window is None:
            return

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            return

        main_window.init_progress_bar(n_pigs)

        for row in range(n_pigs):
            model_index = self._pigs_model.index(row, 0)
            reader = self._pigs_model.data(model_index, 257)
            reader.set_record_intervals(interval_settings)
            main_window.update_progress_bar(row+1)

        main_window.on_select_pig(self._pigs_model.index(0, 0))

    def on_select_interval(self, index):
        """Event handler for interval selection.

        It will grey the data table for the corresponding interval

        Args:
            index (PyQt5.QtCore.QModelIndex): the index corresponding to the selected interval
        """

        model = self._intervals_list.model()

        item = model.item(index.row(), index.column())

        row_min, row_max = item.data()

        self.record_interval_selected.emit(row_min, row_max)

    def on_update_record_intervals(self, reader, record_intervals):
        """Update the intervals list with the newly selected pig.

        Args:
            reader (inspigtor.readers.picco2_reader.PiCCO2FileReader): the reader corresponding to the selected pig
            record_intervals (list of tuples): the record intervals
        """

        # Update the record intervals list view
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        for i, interval in enumerate(record_intervals):
            item = QtGui.QStandardItem('interval {}'.format(i+1))
            item.setData(interval)
            model.appendRow(item)

        self.update_properties.emit(list(reader.data.columns))

        coverages = reader.get_coverages(self._pigs_model.selected_property)

        self._coverages_widget.update_coverage_plot(coverages)
