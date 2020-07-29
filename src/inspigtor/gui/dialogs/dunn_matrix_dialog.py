import numpy as np

from PyQt5 import QtCore, QtWidgets

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT


class DunnMatrixDialog(QtWidgets.QDialog):
    """This class implements a dialog that will show the averages of a given property for the different pigs.
    """

    def __init__(self, dunn_model, parent):

        super(DunnMatrixDialog, self).__init__(parent)

        self._dunn_model = dunn_model

        self.init_ui()

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        main_layout.addWidget(self._canvas)
        main_layout.addWidget(self._toolbar)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Dunn matrix')

        # Build the matplotlib imshoxw widget
        self._figure = Figure()
        self._axes = self._figure.add_subplot(111)
        self._canvas = FigureCanvasQTAgg(self._figure)
        self._toolbar = NavigationToolbar2QT(self._canvas, self)

        n_rows = self._dunn_model.rowCount()
        n_cols = self._dunn_model.columnCount()

        matrix = np.empty((n_rows, n_cols), dtype=np.float)

        for r in range(n_rows):
            for c in range(n_cols):
                index = self._dunn_model.index(r, c)
                matrix[r, c] = self._dunn_model.data(index, QtCore.Qt.DisplayRole)

        self._axes.clear()
        plot = self._axes.imshow(matrix, aspect='equal', origin='lower', interpolation='nearest')
        self._axes.set_xlabel('interval')
        self._axes.set_ylabel('interval')
        self._axes.set_xticks(range(0, n_rows))
        self._axes.set_yticks(range(0, n_cols))
        self._axes.set_xticklabels(range(1, n_rows+1))
        self._axes.set_yticklabels(range(1, n_cols+1))
        self._figure.colorbar(plot)

        self._canvas.draw()

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()
