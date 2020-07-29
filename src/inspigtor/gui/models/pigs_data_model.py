from PyQt5 import QtGui


class PigsDataModel(QtGui.QStandardItemModel):
    """This model underlies the QListView used to display the pigs registered so far.
    """

    def __init__(self):
        """Constructor.
        """

        super(PigsDataModel, self).__init__()

        self._selected_property = 'APs'

    @property
    def selected_property(self):
        """Getter for the selected property.

        Returns:
            str: the selected property
        """

        return self._selected_property

    @selected_property.setter
    def selected_property(self, selected_property):
        """Setter for the selected property.

        Args:
            selected_property (str): the selected property
        """

        self._selected_property = selected_property
