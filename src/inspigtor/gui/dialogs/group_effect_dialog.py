import logging

from PyQt5 import QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.helper_functions import find_main_window, func_formatter
from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton
from inspigtor.kernel.pigs.pigs_groups import PigsGroupsError
from inspigtor.kernel.utils.helper_functions import build_timeline


class GroupEffectDialog(QtWidgets.QDialog):
    """This class implements the dialog that shows the group effect. It is made of three plots which plots respectively the
    number of groups used to perform the statistical test, the p value resulting from the kruskal-wallis or Mann-Whitney 
    statistical test and the group-pairwise p values resulting from the Dunn test.
    """

    def __init__(self, groups_model, parent=None):
        """
        """

        super(GroupEffectDialog, self).__init__(parent)

        self._groups_model = groups_model

        self.init_ui()

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._n_groups_canvas)
        main_layout.addWidget(self._n_groups_toolbar)

        main_layout.addWidget(self._kruskal_canvas)
        main_layout.addWidget(self._kruskal_toolbar)

        if self._groups_model.n_selected_groups >= 3:

            main_layout.addWidget(self._kruskal_dunn_canvas)
            main_layout.addWidget(self._kruskal_dunn_toolbar)

        self.setGeometry(0, 0, 600, 600)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self._n_groups_figure = Figure()
        self._n_groups_axes = self._n_groups_figure.add_subplot(111)
        self._n_groups_canvas = FigureCanvasQTAgg(self._n_groups_figure)
        self._n_groups_toolbar = NavigationToolbarWithExportButton(self._n_groups_canvas, self)

        self._kruskal_figure = Figure()
        self._kruskal_axes = self._kruskal_figure.add_subplot(111)
        self._kruskal_canvas = FigureCanvasQTAgg(self._kruskal_figure)
        self._kruskal_toolbar = NavigationToolbarWithExportButton(self._kruskal_canvas, self)

        if self._groups_model.n_selected_groups >= 3:

            self._kruskal_dunn_figure = Figure()
            self._kruskal_dunn_axes = self._kruskal_dunn_figure.add_subplot(111)
            self._kruskal_dunn_canvas = FigureCanvasQTAgg(self._kruskal_dunn_figure)
            self._kruskal_dunn_toolbar = NavigationToolbarWithExportButton(self._kruskal_dunn_canvas, self)

        main_window = find_main_window()
        self.setWindowTitle('Group effect statistics for {} property'.format(main_window.selected_property))

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()

        self.display_group_effect()

    def display_group_effect(self):
        """Display the global group effect and the pairwise group effect if the number of groups is > 2.
        """

        main_window = find_main_window()
        selected_property = main_window.selected_property

        selected_groups = self._groups_model.selected_groups

        try:
            intervals, p_values, n_groups = self._groups_model.evaluate_global_group_effect(
                selected_property=selected_property, selected_groups=selected_groups)
        except PigsGroupsError as error:
            logging.error(str(error))
            return

        interval_data = main_window.intervals_widget.interval_settings_label.data()
        tick_labels = range(1, len(intervals)+1) if interval_data is None else build_timeline(-10, int(interval_data[2]), intervals)

        self._n_groups_axes.clear()
        self._n_groups_axes.set_xlabel('interval')
        self._n_groups_axes.set_ylabel('n groups')
        self._n_groups_axes.plot(intervals, n_groups, 'b.')
        self._n_groups_axes.xaxis.set_major_locator(ticker.IndexLocator(base=10.0, offset=0.0))
        self._n_groups_axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))
        self._n_groups_canvas.draw()

        self._kruskal_axes.clear()
        self._kruskal_axes.set_xlabel('interval')
        y_label = 'Kruskal-Wallis' if self._groups_model.n_selected_groups >= 3 else 'Mann-Whitney'
        y_label += ' p values'
        self._kruskal_axes.set_ylabel(y_label)
        self._kruskal_axes.plot(intervals, p_values, 'bo')
        self._kruskal_axes.axhline(y=0.05, color='r')
        self._kruskal_axes.set_ylim([0, 1])
        self._kruskal_axes.xaxis.set_major_locator(ticker.IndexLocator(base=10.0, offset=0.0))
        self._kruskal_axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))
        self._kruskal_canvas.draw()

        if self._groups_model.n_selected_groups >= 3:
            p_values = self._groups_model.evaluate_pairwise_group_effect(selected_property=selected_property, selected_groups=selected_groups)
            self._kruskal_dunn_axes.clear()
            self._kruskal_dunn_axes.set_xlabel('interval')
            self._kruskal_dunn_axes.set_ylabel('Dunn p values')
            for p_values_dict in p_values.values():
                self._kruskal_dunn_axes.plot(p_values_dict['intervals'], p_values_dict['values'])
            self._kruskal_dunn_axes.axhline(y=0.05, color='r')
            self._kruskal_dunn_axes.legend(p_values.keys())
            self._kruskal_dunn_axes.xaxis.set_minor_locator(ticker.AutoLocator())
            self._kruskal_dunn_axes.xaxis.set_minor_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))
            self._kruskal_dunn_axes.xaxis.set_major_locator(ticker.IndexLocator(base=10.0, offset=0.0))
            self._kruskal_dunn_axes.xaxis.set_major_formatter(ticker.FuncFormatter(lambda tick_val, tick_pos: func_formatter(tick_val, tick_pos, tick_labels)))
            self._kruskal_dunn_canvas.draw()
