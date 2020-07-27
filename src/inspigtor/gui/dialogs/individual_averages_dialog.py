import numpy as np

from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton


class IndividualAveragesDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the different pigs.
    """

    def __init__(self, pigs_model, parent):

        super(IndividualAveragesDialog, self).__init__(parent)

        self._pigs_model = pigs_model

        self._selected_property = self._pigs_model.selected_property

        self.init_ui()

    def build_events(self):
        """Set the signal/slots of the main window
        """

        self._selected_pig_combo.currentIndexChanged.connect(self.on_select_pig)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._canvas)
        main_layout.addWidget(self._toolbar)

        main_layout.addWidget(self._selected_pig_combo)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Individual averages for {} property'.format(self._selected_property))

        # Build the matplotlib imsho widget
        self._figure = Figure()
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbarWithExportButton(self._canvas, self)

        pig_names = []
        for row in range(self._pigs_model.rowCount()):
            current_item = self._pigs_model.item(row, 0)
            pig_names.append(current_item.data(0))

        self._selected_pig_combo = QtWidgets.QComboBox()
        self._selected_pig_combo.addItems(pig_names)

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

        self.on_select_pig(0)

    def on_select_pig(self, row):
        """Plot the averages and standard deviations over record intervals for a selected pig.

        Args:
            row (int): the selected pig
        """

        # Fetch the statistics (average and standard deviation) for the selected pig
        selected_pig_item = self._pigs_model.item(row, 0)
        reader = selected_pig_item.data(257)
        individual_averages = reader.get_averages(self._selected_property)

        if not individual_averages:
            return

        xs = []
        averages = []
        stds = []
        for interval, average, std in individual_averages:
            xs.append(interval+1)
            averages.append(average)
            stds.append(std)

        # If there is already a plot, remove it
        if hasattr(self, '_axes'):
            self._axes.remove()

        # Plot the averages and standard deviations
        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel(self._selected_property)

        self._plot = self._axes.errorbar(xs, averages, yerr=stds, fmt='ro')

        self._canvas.draw()
