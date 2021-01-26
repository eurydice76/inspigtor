import re

from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.dialogs.interval_settings_dialog import IntervalSettingsDialog
from inspigtor.gui.utils.helper_functions import find_main_window
from inspigtor.gui.widgets.coverages_widget import CoveragesWidget
from inspigtor.gui.widgets.interval_label import IntervalLabel
from inspigtor.kernel.utils.progress_bar import progress_bar


class IntervalsWidget(QtWidgets.QWidget):
    """This class implements the widget that store intervals settings.
    """

    record_interval_selected = QtCore.pyqtSignal(int, int)

    update_properties = QtCore.pyqtSignal(list)

    def __init__(self, pigs_model, parent=None):
        """Constructor

        Args:
            pigs_model (inspigtor.gui.models.pigs_data_model.PigsDataModel): the underlying model for the registered pigs
            parent (PyQt5.QtWidgets.QWidget): the parent widget
        """

        super(IntervalsWidget, self).__init__(parent)

        self._pigs_model = pigs_model

        self.init_ui()

    def build_events(self):
        """Build the signal/slots.
        """

        self._clear_intervals_settings_button.clicked.connect(self.on_clear_interval_settings)
        self._add_intervals_settings_button.clicked.connect(self.on_add_interval_settings)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hl1 = QtWidgets.QHBoxLayout()

        hl11 = QtWidgets.QHBoxLayout()

        hl11.addWidget(self._times_groupbox)
        hl111 = QtWidgets.QHBoxLayout()
        hl111.addWidget(self._intervals_settings_label)
        hl111.addWidget(self._clear_intervals_settings_button)
        hl111.addWidget(self._add_intervals_settings_button)
        self._times_groupbox.setLayout(hl111)

        vl11 = QtWidgets.QVBoxLayout()
        vl11.addLayout(hl11)
        vl11.addWidget(self._coverages_widget)
        vl11.addStretch()

        hl1.addLayout(vl11, stretch=0)
        hl1.addWidget(self._intervals_list)

        main_layout.addLayout(hl1)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
        """

        self._times_groupbox = QtWidgets.QGroupBox('Record intervals')

        self._intervals_settings_label = IntervalLabel('interval not set')
        self._intervals_settings_label.setFixedWidth(250)

        self._clear_intervals_settings_button = QtWidgets.QPushButton('Reset interval')

        self._add_intervals_settings_button = QtWidgets.QPushButton('Set interval')

        self._intervals_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self._coverages_widget = CoveragesWidget(self)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    @property
    def interval_settings_label(self):

        return self._intervals_settings_label

    def on_add_interval_settings(self):
        """Event fired when the user add a new interval.
        """

        dialog = IntervalSettingsDialog(self)

        if dialog.exec_():
            interval_settings = dialog.value()
            self._intervals_settings_label.setData(interval_settings)
            interval = 'start: {} end: {} step: {}'.format(*interval_settings)

            self.search_record_intervals(interval)

            self._intervals_settings_label.setText(interval)

    def on_clear_interval_settings(self):
        """Event fired when the user clears the intervals defined so far.
        """

        self._intervals_settings_label.setText('interval not set')

    def search_record_intervals(self, interval):
        """Event handler called when the search record intervals button is clicked.

        Compute the record intervals for the selected pig.
        """

        match = re.findall(r'start: (\S+) end: (\S+) step: (\d+)', interval)
        if not match:
            return

        interval_settings = match[0]

        main_window = find_main_window()
        if main_window is None:
            return

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            return

        progress_bar.reset(n_pigs)

        for row in range(n_pigs):
            index = self._pigs_model.index(row, 0)
            reader = self._pigs_model.data(index, self._pigs_model.Reader)
            reader.set_record_interval(interval_settings)
            progress_bar.update(row+1)

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

        record_times = reader.record_times
        timeline = reader.timeline
        for i, interval in enumerate(record_intervals):
            item = QtGui.QStandardItem(timeline[i])
            item.setData(interval)
            item.setData(" - ".join(record_times[i]), QtCore.Qt.ToolTipRole)
            model.appendRow(item)

        self.update_properties.emit(list(reader.data.columns))

        t_initial_interval_index = reader.t_initial_interval_index
        index = model.index(t_initial_interval_index, 0)
        model.setData(index, QtGui.QBrush(QtCore.Qt.red), QtCore.Qt.ForegroundRole)

        self._coverages_widget.update_coverage_plot(reader, self._pigs_model.selected_property)
