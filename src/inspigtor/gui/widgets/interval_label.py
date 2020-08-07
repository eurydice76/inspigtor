from PyQt5 import QtWidgets


class IntervalLabel(QtWidgets.QLabel):
    """This class implements a QLabel for with settable data.
    """

    def __init__(self, pigs_model, parent=None):
        """Constructor

        Args:
            pigs_model (inspigtor.gui.models.pigs_data_model.PigsDataModel): the underlying model for the registered pigs
            parent (PyQt5.QtWidgets.QWidget): the parent widget
        """

        super(IntervalLabel, self).__init__(parent)

        self._data = None

    def data(self):
        """Return the data stored in the widget.
        """

        return self._data

    def setData(self, data):
        """Sets the data.
        """

        self._data = data
