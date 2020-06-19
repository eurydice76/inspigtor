import logging
import os

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.dialogs.interval_settings_dialog import IntervalSettingsDialog
from inspigtor.gui.dialogs.stats_results_dialog import StatsResultsDialog
from inspigtor.gui.utils.helper_functions import find_main_window


class IntervalsWidget(QtWidgets.QWidget):

    record_interval_selected = QtCore.pyqtSignal(int, int)

    def __init__(self, main_window=None):
        super(IntervalsWidget, self).__init__(main_window)

        self._main_window = main_window

        self.init_ui()

    def build_events(self):

        self._compute_button.clicked.connect(self.on_compute_averages)
        self._clear_intervals_settings_button.clicked.connect(self.on_clear_interval_settings)
        self._add_intervals_settings_button.clicked.connect(self.on_add_interval_settings)
        self._search_record_intervals_button.clicked.connect(self.on_search_record_intervals)
        self._main_window.pig_selected.connect(self.on_update_record_intervals)

    def build_layout(self):

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

        hl13 = QtWidgets.QHBoxLayout()
        hl13.addWidget(self._compute_property_combo)
        hl13.addWidget(self._compute_button)

        vl11 = QtWidgets.QVBoxLayout()
        vl11.addLayout(hl11)
        vl11.addLayout(hl12)
        vl11.addLayout(hl13)
        vl11.addStretch()

        hl1.addLayout(vl11, stretch=0)
        hl1.addWidget(self._intervals_list)

        main_layout.addLayout(hl1)

        self.setLayout(main_layout)

    def build_widgets(self):
        """
        """

        self._times_groupbox = QtWidgets.QGroupBox('Times (s)')

        self._intervals_settings_combo = QtWidgets.QComboBox()
        self._intervals_settings_combo.setFixedWidth(200)
        self._intervals_settings_combo.installEventFilter(self)

        self._clear_intervals_settings_button = QtWidgets.QPushButton('Clear')

        self._add_intervals_settings_button = QtWidgets.QPushButton('Add interval')

        self._search_record_intervals_button = QtWidgets.QPushButton('Search record intervals')

        self._compute_property_combo = QtWidgets.QComboBox()
        self._compute_button = QtWidgets.QPushButton('Compute averages')

        self._intervals_list = QtWidgets.QListView()
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

    def eventFilter(self, source, event):

        if event.type() == QtCore.QEvent.KeyPress:
            key = event.key()
            if key == QtCore.Qt.Key_Delete:
                if source == self._intervals_settings_combo:
                    self._intervals_settings_combo.removeItem(self._intervals_settings_combo.currentIndex())

        return super(IntervalsWidget, self).eventFilter(source, event)

    def init_ui(self):
        """Set the widgets of the main window
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def on_add_interval_settings(self):

        dialog = IntervalSettingsDialog(self)

        if dialog.exec_():
            interval_settings = interval_settings = dialog.value()
            item_text = '{} {} {:d} {:d}'.format(*interval_settings)

            self._intervals_settings_combo.addItem(item_text, userData=interval_settings)

    def on_clear_interval_settings(self):

        self._intervals_settings_combo.clear()

    def on_compute_averages(self):
        """Computes the average of a given property
        """

        main_window = find_main_window()
        if main_window is None:
            return

        model = main_window.pigs_list.model()

        n_pigs = model.rowCount()

        if n_pigs == 0:
            return

        selected_property = self._compute_property_combo.currentText()

        main_window.init_progress_bar(n_pigs)

        # Loop over the pigs
        for row in range(n_pigs):

            # Fetch the pig's reader
            model_index = model.index(row, 0)
            current_item = model.item(row, 0)
            reader = model.data(model_index, 257)
            data = reader.data

            results = {'selected_property': selected_property, 'stats': []}

            # Fetch the record interval
            record_intervals = model.data(model_index, 258)
            if record_intervals is None:
                record_intervals = []

            # Compute for each record interval the average and standard deviation of the selected property
            for i, interval in enumerate(record_intervals):
                first_index, last_index = interval
                values = []
                for j in range(first_index, last_index):
                    try:
                        values.append(float(data[selected_property].iloc[j]))
                    except ValueError:
                        continue
                if not values:
                    logging.warning('No values to compute statistics for interval {:d} of file {}'.format(i+1, reader.filename))
                    results['stats'].append(None)
                else:
                    avg = np.average(values)
                    std = np.std(values)
                    results['stats'].append((avg, std))

            current_item.setData(results, 259)
            main_window.update_progress_bar(row+1)

        dialog = StatsResultsDialog(main_window)
        dialog.show()

    def on_search_record_intervals(self):
        """Event handler called when the search record intervals buton is clicked.

        Compute for the selected pig the record intervals.
        """

        interval_settings = []
        for row in range(self._intervals_settings_combo.count()):
            interval = self._intervals_settings_combo.itemData(row)
            interval_settings.append(interval)

        main_window = find_main_window()
        if main_window is None:
            return

        pigs_model = main_window.pigs_list.model()

        n_pigs = pigs_model.rowCount()
        if n_pigs == 0:
            return

        main_window.init_progress_bar(n_pigs)

        for row in range(n_pigs):
            model_index = pigs_model.index(row, 0)
            reader = pigs_model.data(model_index, 257)
            record_intervals = reader.get_record_intervals(interval_settings)

            # Set the record intervals as new data (id 258)
            current_item = pigs_model.item(row, 0)
            current_item.setData(record_intervals, 258)
            current_item.setData({}, 259)

            main_window.update_progress_bar(row+1)

        main_window.on_select_pig(pigs_model.index(0, 0))

    def on_select_interval(self, index):
        """Event handler for interval selection.

        It will grey the data table for the corresponding interval
        """

        model = self._intervals_list.model()

        item = model.item(index.row(), index.column())

        row_min, row_max = item.data()

        self.record_interval_selected.emit(row_min, row_max)

    def on_update_record_intervals(self, reader, record_intervals):

        # Update the record intervals list view
        model = QtGui.QStandardItemModel()
        self._intervals_list.setModel(model)
        self._intervals_list.selectionModel().currentChanged.connect(self.on_select_interval)

        for i, interval in enumerate(record_intervals):
            item = QtGui.QStandardItem('interval {}'.format(i+1))
            item.setData(interval)
            model.appendRow(item)

        # Reset the property combobox
        self._compute_property_combo.clear()
        self._compute_property_combo.addItems(reader.data.columns)
        index = self._compute_property_combo.findText('APs', QtCore.Qt.MatchFixedString)
        if index >= 0:
            self._compute_property_combo.setCurrentIndex(index)

    @property
    def pigs_list(self):

        return self._pigs_list
