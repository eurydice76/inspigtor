import logging
import os

from PyQt5 import QtCore, QtGui, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from inspigtor.gui.dialogs.dunn_matrix_dialog import DunnMatrixDialog
from inspigtor.gui.models.pvalues_data_model import PValuesDataModel
from inspigtor.gui.utils.helper_functions import find_main_window
from inspigtor.gui.views.copy_pastable_tableview import CopyPastableTableView


class TimeEffectDialog(QtWidgets.QDialog):
    """
    """

    def __init__(self, selected_property, global_effect, pairwise_effect, parent=None):
        """
        """

        super(TimeEffectDialog, self).__init__(parent)

        self._selected_property = selected_property

        self._global_effect = global_effect

        self._pairwise_effect = pairwise_effect

        self.init_ui()

    def build_events(self):
        """Build signal/slots
        """

        self._dunn_table.customContextMenuRequested.connect(self.on_show_dunn_table_menu)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        friedman_layout = QtWidgets.QVBoxLayout()
        friedman_groupbox_layout = QtWidgets.QVBoxLayout()
        friedman_groupbox_layout.addWidget(self._friedman_table, stretch=1)
        self._friedman_groupbox.setLayout(friedman_groupbox_layout)
        friedman_layout.addWidget(self._friedman_groupbox)

        dunn_layout = QtWidgets.QVBoxLayout()
        dunn_groupbox_layout = QtWidgets.QVBoxLayout()
        selected_group_layout = QtWidgets.QHBoxLayout()
        selected_group_layout.addWidget(self._selected_group_label)
        selected_group_layout.addWidget(self._selected_group_combo)
        dunn_groupbox_layout.addLayout(selected_group_layout)
        dunn_groupbox_layout.addWidget(self._dunn_table, stretch=2)
        self._dunn_groupbox.setLayout(dunn_groupbox_layout)
        dunn_layout.addWidget(self._dunn_groupbox)

        main_layout.addLayout(friedman_layout, stretch=2)
        main_layout.addLayout(dunn_layout, stretch=2)

        self.setGeometry(0, 0, 600, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
        """

        self.setWindowTitle('Time effect statistics for {} property'.format(self._selected_property))

        self._friedman_groupbox = QtWidgets.QGroupBox('Global effect (Friedman test)')

        self._friedman_table = CopyPastableTableView()

        self._dunn_groupbox = QtWidgets.QGroupBox('Pairwise effect (Dunn test)')
        self._selected_group_label = QtWidgets.QLabel('Selected group')
        self._selected_group_combo = QtWidgets.QComboBox()
        self._dunn_table = CopyPastableTableView()
        self._dunn_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self._dunn_table.setSelectionBehavior(QtWidgets.QTableView.SelectRows)
        self._dunn_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

    def display_time_effect(self):
        """Display the global time effect and the pairwise time effect.
        """

        model = PValuesDataModel(self._global_effect)
        self._friedman_table.setModel(model)
        for col in range(model.columnCount()):
            self._friedman_table.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)

        self._selected_group_combo.clear()
        self._selected_group_combo.addItems(self._pairwise_effect.keys())
        for i, p_values in enumerate(self._pairwise_effect.values()):
            self._selected_group_combo.setItemData(i, p_values)

        self._selected_group_combo.currentIndexChanged.connect(self.on_select_group)
        self.on_select_group(0)

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

        self.display_time_effect()

    def on_export_dunn_table(self):
        """Export the current Dunn table to a excel file.
        """

        model = self._dunn_table.model()
        if model is None:
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Export statistics as ...', filter="Excel files (*.xls *.xlsx)")
        if not filename:
            return

        try:
            model.matrix().to_excel(filename)
        except:
            logging.error('Can not open file {} for writing.'.format(filename))

    def on_select_group(self, selected_group):
        """Event fired when the user change of group for showing the corresponding Dunn matrix.

        Args:
            selected_group (int): the selected group
        """

        p_values = self._selected_group_combo.itemData(selected_group)

        model = PValuesDataModel(p_values)

        self._dunn_table.setModel(model)

    def on_show_dunn_matrix(self):
        """Show the current Dunn matrix.
        """

        model = self._dunn_table.model()
        if model is None:
            return

        dialog = DunnMatrixDialog(model.matrix(), self)
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
