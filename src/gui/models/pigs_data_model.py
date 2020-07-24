from PyQt5 import QtGui


class PigsDataModel(QtGui.QStandardItemModel):
    """This model describes the pigs.
    """

    def __init__(self):

        super(PigsDataModel, self).__init__()

        self._selected_property = 'APs'

    @property
    def selected_property(self):

        return self._selected_property

    @selected_property.setter
    def selected_property(self, selected_property):

        self._selected_property = selected_property
