from PyQt5 import QtCore, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT

from inspigtor.gui.models.pandas_data_model import PandasDataModel
from inspigtor.gui.widgets.copy_pastable_tableview import CopyPastableTableView


class TimeEffectWidget(QtWidgets.QWidget):
    """This class implements the widget that will store the time-effect statistics.
    """

    def __init__(self, groups_model, parent=None):
        super(TimeEffectWidget, self).__init__(parent)

        self._groups_model = groups_model

        self.init_ui()

    def build_events(self):
        """Build signal/slots
        """

        self._selected_group_combo.currentIndexChanged.connect(self.on_select_group)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._friedman_canvas)
        main_layout.addWidget(self._friedman_toolbar)

        dunn_layout = QtWidgets.QVBoxLayout()

        dunn_groupbox_layout = QtWidgets.QVBoxLayout()
        selected_group_layout = QtWidgets.QHBoxLayout()
        selected_group_layout.addWidget(self._selected_group_label)
        selected_group_layout.addWidget(self._selected_group_combo)
        dunn_groupbox_layout.addLayout(selected_group_layout)
        dunn_groupbox_layout.addWidget(self._dunn_table)
        self._dunn_groupbox.setLayout(dunn_groupbox_layout)

        dunn_layout.addWidget(self._dunn_groupbox)

        main_layout.addLayout(dunn_layout)

        self.setGeometry(0, 0, 600, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
        """

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

    def display_time_effect(self):
        """Display the global time effect and the pairwise time effect.
        """

        p_values = self._groups_model.evaluate_global_time_effect()

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

        self.display_time_effect()

    def on_select_group(self, selected_group):
        """Event fired when the user change of group for showing the corresponding Dunn matrix.

        Args:
            selected_group (int): the selected group
        """

        selected_group = self._selected_group_combo.itemText(selected_group)

        p_values = self._pairwise_p_values[selected_group]

        self._dunn_table.setModel(PandasDataModel(p_values))
