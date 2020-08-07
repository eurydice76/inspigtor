import logging

from PyQt5 import QtCore, QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.helper_functions import find_main_window, func_formatter
from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton
from inspigtor.kernel.pigs.pigs_pool import PigsPoolError
from inspigtor.kernel.utils.helper_functions import build_timeline


class GroupAveragesDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the groups defined so far.
    """

    def __init__(self, selected_property, groups_model, parent):

        super(GroupAveragesDialog, self).__init__(parent)

        self._groups_model = groups_model

        self._selected_property = selected_property

        self.init_ui()

    def build_events(self):
        """Set the signal/slots of the main window
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

        self.setWindowTitle('Group averages for {} property'.format(self._selected_property))

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbarWithExportButton(self._canvas, self)

        self._selected_group_combo = QtWidgets.QComboBox()
        group_names = ['all']
        for i in range(self._groups_model.rowCount()):
            index = self._groups_model.index(i)
            group_names.append(self._groups_model.data(index, QtCore.Qt.DisplayRole))
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
        if group == 'all':
            selected_groups = range(self._groups_model.rowCount())
        else:
            selected_groups = [row-1]

        # If there is already a plot, remove it
        if hasattr(self, '_axes'):
            self._axes.remove()

        # Plot the averages and standard deviations
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel(self._selected_property)

        for group_id in selected_groups:

            pigs_pool = self._groups_model.data(self._groups_model.index(group_id, 0), self._groups_model.PigsPool)
            if len(pigs_pool) == 0:
                continue

            try:
                reduced_averages = pigs_pool.reduced_statistics(self._selected_property, selected_statistics='mean', output_statistics=['mean', 'std'])
            except PigsPoolError as error:
                logging.error(str(error))
                return

            x = range(0, len(reduced_averages['mean']))
            main_window = find_main_window()
            interval_data = main_window.intervals_widget.interval_settings_label.data()
            tick_labels = range(1, len(x)+1) if interval_data is None else build_timeline(-10, int(interval_data[2]), x)

            self._axes.errorbar(x, reduced_averages['mean'], yerr=reduced_averages['std'], fmt='o')
            self._axes.xaxis.set_major_locator(ticker.IndexLocator(base=10.0, offset=0.0))
            self._axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))

        group_names = self._groups_model.pigs_groups.groups.keys()

        self._axes.legend(group_names)

        self._canvas.draw()
