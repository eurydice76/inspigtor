import logging

import numpy as np

from PyQt5 import QtCore, QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from inspigtor.gui.utils.helper_functions import find_main_window, func_formatter
from inspigtor.kernel.utils.helper_functions import build_timeline


class GroupMediansDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the groups defined so far.
    """

    def __init__(self, selected_property, groups_model, parent):

        super(GroupMediansDialog, self).__init__(parent)

        self._groups_model = groups_model

        self._selected_property = selected_property

        self.init_ui()

    def build_events(self):
        """Set the signal/slots.
        """

        self._selected_group_combo.currentIndexChanged.connect(self.on_select_group)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._canvas)
        main_layout.addWidget(self._toolbar)

        main_layout.addWidget(self._selected_group_combo)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Group medians for {} property'.format(self._selected_property))

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        self._selected_group_combo = QtWidgets.QComboBox()
        group_names = [self._groups_model.data(self._groups_model.index(row), QtCore.Qt.DisplayRole) for row in range(self._groups_model.rowCount())]
        self._selected_group_combo.addItems(group_names)

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

        self.on_select_group(0)

    def on_select_group(self, row):
        """Plot the averages and standard deviations over record intervals for a selected group.

        Args:
            row (int): the selected group
        """

        selected_group_model = self._selected_group_combo.model()
        if selected_group_model.rowCount() == 0:
            return

        group = selected_group_model.item(row, 0).data(QtCore.Qt.DisplayRole)
        pigs_groups = self._groups_model.pigs_groups
        if group not in pigs_groups:
            logging.warning('Can not find group with name {}'.format(group))
            return

        pigs_pool = self._groups_model.data(self._groups_model.index(row, 0), self._groups_model.PigsPool)
        if len(pigs_pool) == 0:
            return

        _, individual_averages = pigs_pool.get_statistics(self._selected_property)
        individual_averages = [[v for v in row if not np.isnan(v)] for row in individual_averages]

        # If there is already a plot, remove it
        if hasattr(self, '_axes'):
            self._axes.remove()

        # Plot the averages and standard deviations
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel(self._selected_property)

        x = range(len(individual_averages))
        main_window = find_main_window()
        interval_data = main_window.intervals_widget.interval_settings_label.data()
        tick_labels = range(1, len(x)+1) if interval_data is None else build_timeline(-10, int(interval_data[2]), x)

        self._plot = self._axes.boxplot(individual_averages, showfliers=False)
        self._axes.xaxis.set_major_locator(ticker.IndexLocator(base=10.0, offset=0.0))
        self._axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))

        self._canvas.draw()
