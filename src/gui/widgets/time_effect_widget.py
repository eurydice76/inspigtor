from PyQt5 import QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class TimeEffectWidget(QtWidgets.QWidget):
    """This class implements the widget that will store the time-effect statistics.
    """

    def __init__(self, groups_model, parent=None):
        super(TimeEffectWidget, self).__init__(parent)

        self._groups_model = groups_model

        self.init_ui()

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._friedman_canvas)
        main_layout.addWidget(self._friedman_toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
        """

        self._friedman_figure = Figure()
        self._friedman_axes = self._friedman_figure.add_subplot(111)
        self._friedman_canvas = FigureCanvasQTAgg(self._friedman_figure)
        self._friedman_toolbar = NavigationToolbar2QT(self._friedman_canvas, self)

    def display_time_effect(self):
        """Display the global time effect and the pairwise time effect.
        """

        p_values = self._groups_model.evaluate_global_time_effect()

        self._friedman_axes.clear()
        self._friedman_axes.set_xlabel('groups')
        self._friedman_axes.set_ylabel('Friedman p values')

        self._friedman_axes.bar(list(p_values.keys()), list(p_values.values()))

        self._friedman_canvas.draw()

    def init_ui(self):
        """Initializes the ui.
        """

        self.build_widgets()

        self.build_layout()

        self.display_time_effect()
