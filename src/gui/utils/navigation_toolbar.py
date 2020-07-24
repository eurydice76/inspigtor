import logging
import os

from PyQt5 import QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

import inspigtor


class NavigationToolbarWithExportButton(NavigationToolbar2QT):
    """This class subclasses the standard matplotlib toolbar with an additional export button for 
    exporting the plots in a csv file.
    """

    def __init__(self, canvas, parent=None):
        super(NavigationToolbarWithExportButton, self).__init__(canvas, parent)

        self._parent = parent

        icon_path = os.path.join(inspigtor.__path__[0], 'icons', 'export.ico')

        export_action = QtWidgets.QAction(QtGui.QIcon(icon_path), "Export data", self)
        export_action.triggered.connect(self.on_export_plot)

        self.insertAction(self.actions()[10], export_action)

    def on_export_plot(self):
        """Export the plot as csv file.
        """

        axes = self.canvas.figure.get_axes()
        if not axes:
            return

        lines = axes[0].lines
        if not lines:
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self._parent, 'Export plot as ...')
        if not filename:
            return

        try:
            with open(filename, 'w') as fout:
                for line in lines:
                    fout.write(';'.join([str(v) for v in line.get_xdata()]))
                    fout.write('\n')
                    fout.write(';'.join([str(v) for v in line.get_ydata()]))
                    fout.write('\n')
        except PermissionError:
            logging.error('Can not open file {} for writing.'.format(filename))
