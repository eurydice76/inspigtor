import numpy as np

from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class StatsResultsDialog(QtWidgets.QDialog):

    def __init__(self, main_window):

        super(StatsResultsDialog, self).__init__()

        self.setWindowTitle('Statistics')

        self._main_window = main_window

        self.init_ui()

    def build_events(self):
        """Set the signal:slots of the main window
        """

        self._selected_pig_combo.currentIndexChanged.connect(self.on_select_pig)

    def build_layout(self):

        self._main_layout = QtWidgets.QVBoxLayout()

        self._main_layout.addWidget(self._canvas)
        self._main_layout.addWidget(self._toolbar)

        self._main_layout.addWidget(self._selected_pig_combo)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(self._main_layout)

    def build_widgets(self):

        # Build the matplotlib imsho widget
        self._figure = Figure()
        # self._axes.set_xticks(range(self._reader.n_frames))
        # self._axes.set_yticks(range(0, 2))
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        # Fetch the model behind pigs list view
        pigs_list = self._main_window._pigs_list
        model = pigs_list.model()

        pig_names = []
        for row in range(model.rowCount()):
            current_item = model.item(row, 0)
            pig_names.append(current_item.data(0))

        self._selected_pig_combo = QtWidgets.QComboBox()
        self._selected_pig_combo.addItems(pig_names)

    def init_ui(self):
        """
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def on_select_pig(self, row):

        # Fetch the model behind pigs list view
        pigs_list = self._main_window._pigs_list
        model = pigs_list.model()

        selected_pig_item = model.item(row, 0)
        stats = selected_pig_item.data(259)

        averages = np.array([v[0] for v in stats['stats']])
        stds = np.array([v[1] for v in stats['stats']])

        x_values = range(len(averages))

        if hasattr(self, '_axes'):
            self._axes.remove()

        self._axes = self._figure.add_subplot(111)
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel(stats['selected_property'])
        self._axes.set_xlim([-1, len(averages)])

        self._plot = self._axes.errorbar(x_values, averages, yerr=stds, fmt='ro')

        self._canvas.draw()
