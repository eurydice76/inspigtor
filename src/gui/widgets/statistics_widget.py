import logging

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.widgets.droppable_list_view import DroppableListView
from inspigtor.gui.utils.helper_functions import find_main_window


class StatisticsWidget(QtWidgets.QWidget):

    def __init__(self, main_window, *args, **kwargs):
        super(StatisticsWidget, self).__init__(*args, **kwargs)

        self.init_ui()

    def build_events(self):

        self._show_statistics_button.clicked.connect(self.on_show_statistics)

    def build_layout(self):
        """Setup the layout of the widget
        """

        main_layout = QtWidgets.QVBoxLayout()

        pigs_layout = QtWidgets.QHBoxLayout()

        populations_layout = QtWidgets.QHBoxLayout()
        populations_layout.addWidget(self._population1_list)
        populations_layout.addWidget(self._population2_list)
        self._populations_groupbox.setLayout(populations_layout)

        pigs_layout.addWidget(self._populations_groupbox)

        main_layout.addLayout(pigs_layout)

        main_layout.addWidget(self._show_statistics_button)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Setup and initialize the widgets
        """

        self._population1_list = DroppableListView(self)
        self._population1_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        population1_model = QtGui.QStandardItemModel()
        self._population1_list.setModel(population1_model)

        self._population2_list = DroppableListView(self)
        self._population2_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        population2_model = QtGui.QStandardItemModel()
        self._population2_list.setModel(population2_model)

        self._populations_groupbox = QtWidgets.QGroupBox('Populations')

        self._show_statistics_button = QtWidgets.QPushButton('Show statistics')

    def init_ui(self):
        """Initializes the ui
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def _get_population_statistics(self, population_model):

        main_window = find_main_window()
        if main_window is None:
            return

        pigs_model = main_window.pigs_list.model()

        n_pigs = population_model.rowCount()

        min_n_intervals = np.inf
        averages = []
        coverages = []
        for row in range(n_pigs):
            index = population_model.index(row, 0)
            item = population_model.item(index.row(), index.column())
            filename = item.text()

            items = pigs_model.findItems(filename, QtCore.Qt.MatchExactly)
            reader = items[0].data(257)
            stats = items[0].data(259)
            if not stats:
                raise ValueError('No statistics computed for file {}. Can not continue.'.format(reader.filename))

            try:
                idx = stats['averages'].index(None)
            except ValueError:
                pass
            else:
                raise ValueError('(At least) interval {:d} has no statistics for file {}. Can not continue.'.format(idx+1, reader.filename))

            min_n_intervals = min(min_n_intervals, len(stats['averages']))
            coverages.append(stats['coverages'])
            averages.append(stats['averages'])

        temp_coverages = np.empty((n_pigs, min_n_intervals))
        temp_averages = np.empty((n_pigs, min_n_intervals))
        for i, avg in enumerate(averages):
            coverage = coverages[i]
            temp_averages[i, :] = avg[:min_n_intervals]
            temp_coverages[i, :] = coverage[:min_n_intervals]

        averages = np.average(temp_averages, axis=0)
        stds = np.std(temp_averages, axis=0)

        average_coverages = np.average(temp_coverages, axis=0)
        std_coverages = np.std(temp_coverages, axis=0)

        return (averages, stds, average_coverages, std_coverages)

    def on_show_statistics(self):

        population1_model = self._population1_list.model()
        population2_model = self._population2_list.model()

        if population1_model.rowCount() == 0 or population2_model.rowCount() == 0:
            return

        try:
            stats1 = self._get_population_statistics(population1_model)
        except ValueError as err:
            logging.error(str(err))
            return

        try:
            stats2 = self._get_population_statistics(population2_model)
        except ValueError as err:
            logging.error(str(err))
            return

        print(stats1)
        print(stats2)
