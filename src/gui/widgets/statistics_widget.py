import logging

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets

from inspigtor.gui.dialogs.group_averages_dialog import GroupAveragesDialog
from inspigtor.gui.dialogs.group_statistics_dialog import GroupStatisticsDialog
from inspigtor.gui.dialogs.individual_averages_dialog import IndividualAveragesDialog
from inspigtor.gui.models.groups_model import GroupsModel
from inspigtor.gui.models.individuals_model import IndividualsModel
from inspigtor.gui.widgets.droppable_list_view import DroppableListView


class StatisticsWidget(QtWidgets.QWidget):

    def __init__(self, pigs_model, main_window):
        super(StatisticsWidget, self).__init__(main_window)

        self._pigs_model = pigs_model

        self.init_ui()

    def build_events(self):

        self._show_individual_averages_button.clicked.connect(self.on_show_individual_averages)
        self._show_group_averages_button.clicked.connect(self.on_show_group_averages)
        self._show_statistics_button.clicked.connect(self.on_show_statistics)
        self._add_group_button.clicked.connect(self.on_add_group)
        self._groups_list.selectionModel().currentChanged.connect(self.on_select_group)

    def build_layout(self):
        """Setup the layout of the widget
        """

        main_layout = QtWidgets.QVBoxLayout()

        pigs_layout = QtWidgets.QHBoxLayout()

        populations_layout = QtWidgets.QHBoxLayout()

        groups_layout = QtWidgets.QVBoxLayout()
        groups_layout.addWidget(self._groups_list)
        groups_layout.addWidget(self._add_group_button)
        populations_layout.addLayout(groups_layout)
        populations_layout.addWidget(self._individuals_list)
        self._groups_groupbox.setLayout(populations_layout)

        pigs_layout.addWidget(self._groups_groupbox)

        main_layout.addLayout(pigs_layout)

        show_averages_layout = QtWidgets.QHBoxLayout()
        show_averages_layout.addWidget(self._show_group_averages_button)
        show_averages_layout.addWidget(self._show_individual_averages_button)
        main_layout.addLayout(show_averages_layout)

        main_layout.addWidget(self._show_statistics_button)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Setup and initialize the widgets
        """

        self._groups_list = QtWidgets.QListView(self)
        self._groups_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._groups_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        groups_model = GroupsModel(self._pigs_model)
        self._groups_list.setModel(groups_model)

        self._individuals_list = DroppableListView(self)
        self._individuals_list.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._individuals_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._groups_groupbox = QtWidgets.QGroupBox('Groups')

        self._add_group_button = QtWidgets.QPushButton('Add group')

        self._show_group_averages_button = QtWidgets.QPushButton('Show group averages')

        self._show_individual_averages_button = QtWidgets.QPushButton('Show individual averages')

        self._show_statistics_button = QtWidgets.QPushButton('Show group statistics')

    def init_ui(self):
        """Initializes the ui
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def on_add_group(self):

        group, ok = QtWidgets.QInputDialog.getText(self, 'Enter group name', 'Group name', QtWidgets.QLineEdit.Normal, 'group')

        if ok and group:
            groups_model = self._groups_list.model()
            if groups_model.findItems(group):
                logging.warning('A group with the same name ({}) already exists.'.format(group))
            else:
                item = QtGui.QStandardItem(group)
                individuals_model = IndividualsModel(self._pigs_model, groups_model)
                item.setData(individuals_model, 257)
                groups_model.appendRow(item)
                last_index = groups_model.index(groups_model.rowCount()-1, 0)
                self._groups_list.setCurrentIndex(last_index)

    def on_select_group(self, index):
        """Updates the individuals list view.
        """

        groups_model = self._groups_list.model()

        individual_model = groups_model.data(index, 257)

        self._individuals_list.setModel(individual_model)

    def on_show_group_averages(self):

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            return

        dialog = GroupAveragesDialog(self._pigs_model, self._groups_list.model(), self)
        dialog.show()

    def on_show_individual_averages(self):
        """Computes the average of a given property
        """

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            return

        dialog = IndividualAveragesDialog(self._pigs_model, self)
        dialog.show()

    def on_show_statistics(self):
        """Open the statistics dialog.
        """

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            logging.warning('No pigs loaded yet')
            return

        groups_model = self._groups_list.model()
        if groups_model.rowCount() == 0:
            logging.warning('No groups defined yet')
            return

        dialog = GroupStatisticsDialog(self._pigs_model, self._groups_list.model(), self)
        dialog.show()
