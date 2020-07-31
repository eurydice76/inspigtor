import logging

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from inspigtor.gui.dialogs.dunn_matrix_dialog import DunnMatrixDialog
from inspigtor.gui.models.pvalues_data_model import PValuesDataModel
from inspigtor.gui.widgets.copy_pastable_tableview import CopyPastableTableView


class PreMortemStatisticsWidget(QtWidgets.QWidget):
    """This class implements the widget that will store the time-effect premortem statistics.
    """

    def __init__(self, groups_model, parent=None):
        super(PreMortemStatisticsWidget, self).__init__(parent)

        self._groups_model = groups_model

        self.init_ui()

    def build_events(self):
        """Build signal/slots
        """

        self._compute_premortem_statistics_button.clicked.connect(self.on_compute_premortem_statistics)
        self._dunn_table.customContextMenuRequested.connect(self.on_show_dunn_table_menu)
        self._selected_group_combo.currentIndexChanged.connect(self.on_select_group)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()

        hlayout.addWidget(self._n_last_intervals_label)
        hlayout.addWidget(self._n_last_intervals_spinbox)

        main_layout.addLayout(hlayout)

        main_layout.addWidget(self._compute_premortem_statistics_button)

        main_layout.addWidget(self._friedman_canvas, stretch=1)
        main_layout.addWidget(self._friedman_toolbar, stretch=0)

        dunn_layout = QtWidgets.QVBoxLayout()

        dunn_groupbox_layout = QtWidgets.QVBoxLayout()
        selected_group_layout = QtWidgets.QHBoxLayout()
        selected_group_layout.addWidget(self._selected_group_label)
        selected_group_layout.addWidget(self._selected_group_combo)
        dunn_groupbox_layout.addLayout(selected_group_layout)
        dunn_groupbox_layout.addWidget(self._dunn_table, stretch=2)
        self._dunn_groupbox.setLayout(dunn_groupbox_layout)

        dunn_layout.addWidget(self._dunn_groupbox)

        main_layout.addLayout(dunn_layout, stretch=2)

        self.setGeometry(0, 0, 600, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
        """

        self._n_last_intervals_label = QtWidgets.QLabel('Number of (last) intervals')

        self._n_last_intervals_spinbox = QtWidgets.QSpinBox()
        self._n_last_intervals_spinbox.setMinimum(1)
        self._n_last_intervals_spinbox.setMaximum(10)
        self._n_last_intervals_spinbox.setValue(6)

        self._compute_premortem_statistics_button = QtWidgets.QPushButton('Run')

        self._friedman_figure = Figure()
        self._friedman_axes = self._friedman_figure.add_subplot(111)
        self._friedman_canvas = FigureCanvasQTAgg(self._friedman_figure)
        self._friedman_toolbar = NavigationToolbar2QT(self._friedman_canvas, self)

        self._dunn_groupbox = QtWidgets.QGroupBox('Dunn pairwise statistics')

        self._selected_group_label = QtWidgets.QLabel('Selected group')

        self._selected_group_combo = QtWidgets.QComboBox()

        selected_groups = [self._groups_model.item(i).data(QtCore.Qt.DisplayRole) for i in range(self._groups_model.rowCount())]

        self._selected_group_combo.addItems(selected_groups)

        self._dunn_table = CopyPastableTableView()
        self._dunn_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._dunn_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._dunn_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def on_compute_premortem_statistics(self):
        """Event fired when the user click on the 'Run' button.

        It will compute the premortem statistics and update the friedman and dunn widgets accordingly.
        """

        n_last_intervals = self._n_last_intervals_spinbox.value()

        friedman, dunn = self._groups_model.premortem_statistics(n_last_intervals)

        print(friedman)

        print(dunn)

    def display_time_effect(self):
        """Display the global time effect and the pairwise time effect.
        """

        p_values = self._groups_model.evaluate_global_time_effect()
        if not p_values:
            return

        self._friedman_axes.clear()
        self._friedman_axes.set_xlabel('groups')
        self._friedman_axes.set_ylabel('Friedman p values')

        self._friedman_axes.bar(list(p_values.keys()), list(p_values.values()))

        self._friedman_canvas.draw()

        self._pairwise_p_values = self._groups_model.evaluate_pairwise_time_effect()

        self.on_select_group(0)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

        # self.display_time_effect()

    def on_export_dunn_table(self):
        """Export the current Dunn table to a csv file.
        """

        model = self._dunn_table.model()
        if model is None:
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export table as ...')
        if not filename:
            return

        try:
            with open(filename, 'w') as fout:
                for i in range(model.rowCount()):
                    line = []
                    for j in range(model.columnCount()):
                        index = model.index(i, j)
                        data = model.data(index, QtCore.Qt.DisplayRole)
                        line.append(data)
                    line = ';'.join(line)
                    fout.write(line)
                    fout.write('\n')
        except PermissionError:
            logging.error('Can not open file {} for writing.'.format(filename))

    def on_select_group(self, selected_group):
        """Event fired when the user change of group for showing the corresponding Dunn matrix.

        Args:
            selected_group (int): the selected group
        """

        if not self._pairwise_p_values:
            return

        selected_group = self._selected_group_combo.itemText(selected_group)
        if selected_group not in self._pairwise_p_values:
            return

        p_values = self._pairwise_p_values[selected_group]

        # p_values is a squared data frame
        n_rows, n_cols = p_values.shape
        p_values.index = range(1, n_rows+1)
        p_values.columns = range(1, n_cols+1)

        model = PValuesDataModel(p_values)

        self._dunn_table.setModel(model)

    def on_show_dunn_matrix(self):
        """Show the current Dunn matrix.
        """

        model = self._dunn_table.model()
        if model is None:
            return

        dialog = DunnMatrixDialog(model, self)
        dialog.show()

    def on_show_dunn_table_menu(self, point):
        """Pops up the contextual menu of the Dunn table

        Args:
            point(PyQt5.QtCore.QPoint) : the position of the contextual menu
        """

        menu = QtWidgets.QMenu()

        export_action = menu.addAction('Export')
        show_matrix_action = menu.addAction('Show matrix')

        export_action.triggered.connect(self.on_export_dunn_table)
        show_matrix_action.triggered.connect(self.on_show_dunn_matrix)

        menu.exec_(QtGui.QCursor.pos())
