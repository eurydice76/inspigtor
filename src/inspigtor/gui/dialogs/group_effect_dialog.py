import logging

from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.helper_functions import find_main_window
from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton
from inspigtor.kernel.pigs.pigs_groups import PigsGroupsError


class GroupEffectDialog(QtWidgets.QDialog):
    """
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

        main_layout.addWidget(self._kruskal_canvas)
        main_layout.addWidget(self._kruskal_toolbar)

        if self._groups_model.rowCount() >= 3:

            main_layout.addWidget(self._kruskal_dunn_canvas)
            main_layout.addWidget(self._kruskal_dunn_toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self._kruskal_figure = Figure()
        self._kruskal_axes = self._kruskal_figure.add_subplot(111)
        self._kruskal_canvas = FigureCanvasQTAgg(self._kruskal_figure)
        self._kruskal_toolbar = NavigationToolbarWithExportButton(self._kruskal_canvas, self)

        if self._groups_model.rowCount() >= 3:

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

        try:
            p_values = self._groups_model.evaluate_global_group_effect(selected_property=selected_property)
        except PigsGroupsError as error:
            logging.error(str(error))
            return

        self._kruskal_axes.clear()
        self._kruskal_axes.set_xlabel('interval')
        y_label = 'Kruskal-Wallis' if self._groups_model.rowCount() >= 3 else 'Mann-Whitney'
        y_label += ' p values'
        self._kruskal_axes.set_ylabel(y_label)

        self._kruskal_axes.plot(range(1, len(p_values)+1), p_values, 'ro')

        self._kruskal_canvas.draw()

        if self._groups_model.rowCount() >= 3:
            pairwise_p_values = self._groups_model.evaluate_pairwise_group_effect(selected_property=selected_property)

            self._kruskal_dunn_axes.clear()
            self._kruskal_dunn_axes.set_xlabel('interval')
            self._kruskal_dunn_axes.set_ylabel('Dunn p values')

            for p_values in pairwise_p_values.values():
                self._kruskal_dunn_axes.plot(range(1, len(p_values)+1), p_values)

            self._kruskal_dunn_axes.legend(pairwise_p_values.keys())

            self._kruskal_dunn_canvas.draw()
