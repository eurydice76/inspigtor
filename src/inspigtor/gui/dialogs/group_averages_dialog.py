import logging

from PyQt5 import QtCore, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton


class GroupAveragesDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the groups defined so far.
    """

    def __init__(self, pigs_model, groups_model, parent):

        super(GroupAveragesDialog, self).__init__(parent)

        self._pigs_model = pigs_model

        self._groups_model = groups_model

        self._selected_property = self._pigs_model.selected_property

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
        group_names = [self._groups_model.item(i).data(QtCore.Qt.DisplayRole) for i in range(self._groups_model.rowCount())]
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
        if not self._groups_model.findItems(group, QtCore.Qt.MatchExactly):
            return

        individuals_model = self._groups_model.get_group(group)
        if individuals_model is not None and individuals_model.rowCount() == 0:
            return

        temp = individuals_model.get_averages()
        if temp is None:
            return
        averages, stds = temp

        # If there is already a plot, remove it
        if hasattr(self, '_axes'):
            self._axes.remove()

        # Plot the averages and standard deviations
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel(self._selected_property)

        self._plot = self._axes.errorbar(range(1, len(averages)+1), averages, yerr=stds, fmt='ro')

        self._canvas.draw()
