from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.widgets.droppable_list_view import DroppableListView


class StatisticsWidget(QtWidgets.QWidget):

    def __init__(self, main_window=None):
        super(StatisticsWidget, self).__init__(main_window)

        self._main_window = main_window

        self.init_ui()

    def build_layout(self):
        """Setup the layout of the widget
        """

        main_layout = QtWidgets.QVBoxLayout()

        pigs_layout = QtWidgets.QHBoxLayout()

        populations_layout = QtWidgets.QHBoxLayout()
        populations_layout.addWidget(self._population1_list)
        populations_layout.addWidget(self._population2_list)
        self._populations_groupbox.setLayout(populations_layout)

        pigs_layout.addWidget(self._populations_groupbox)

        main_layout.addLayout(pigs_layout)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Setup and initialize the widgets
        """

        self._population1_list = DroppableListView(self)
        self._population1_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        population1_model = QtGui.QStandardItemModel()
        self._population1_list.setModel(population1_model)

        self._population2_list = DroppableListView(self)
        self._population2_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        population2_model = QtGui.QStandardItemModel()
        self._population2_list.setModel(population2_model)

        self._populations_groupbox = QtWidgets.QGroupBox('Populations')

    def init_ui(self):
        """Initializes the ui
        """

        self.build_widgets()

        self.build_layout()
