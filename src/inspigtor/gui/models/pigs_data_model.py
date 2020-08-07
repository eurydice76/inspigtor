from PyQt5 import QtGui


class PigsDataModel(QtGui.QStandardItemModel):
    """This model underlies the QListView used to display the pigs registered so far.
    """

    def __init__(self):
        """Constructor.
        """

        super(PigsDataModel, self).__init__()
