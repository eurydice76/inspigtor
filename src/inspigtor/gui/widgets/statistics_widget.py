import logging
import os

from PyQt5 import QtGui, QtWidgets

from inspigtor.gui.dialogs.group_averages_dialog import GroupAveragesDialog
from inspigtor.gui.dialogs.group_statistics_dialog import GroupStatisticsDialog
from inspigtor.gui.models.groups_model import GroupsModel
from inspigtor.gui.models.individuals_model import IndividualsModel
from inspigtor.gui.widgets.droppable_list_view import DroppableListView


class StatisticsWidget(QtWidgets.QWidget):
    """This class implements the widget that will store all the sttatistics related widgets.
    """

    def __init__(self, pigs_model, main_window):
        """Constructor.

        Args:
            pigs_model (inspigtor.gui.models.pigs_data_model.PigsDataModel): the underlying model for the registered pigs
            main_window (PyQt5.QtWidgets.QMainWindow): the main window
        """
        super(StatisticsWidget, self).__init__(main_window)

        self._main_window = main_window

        self._pigs_model = pigs_model

        self.init_ui()

    def build_events(self):
        """Build the signal/slots
        """

        self._groups_list.selectionModel().currentChanged.connect(self.on_select_group)
        self._main_window.add_new_group.connect(self.on_add_group)
        self._main_window.display_group_averages.connect(self.on_display_group_averages)
        self._main_window.display_group_time_effect_statistics.connect(self.on_display_group_time_effect_statistics)
        self._main_window.export_group_statistics.connect(self.on_export_group_statistics)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        pigs_layout = QtWidgets.QHBoxLayout()

        populations_layout = QtWidgets.QHBoxLayout()

        groups_layout = QtWidgets.QVBoxLayout()
        groups_layout.addWidget(self._groups_list)
        populations_layout.addLayout(groups_layout)
        populations_layout.addWidget(self._individuals_list)
        self._groups_groupbox.setLayout(populations_layout)

        pigs_layout.addWidget(self._groups_groupbox)

        main_layout.addLayout(pigs_layout)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build the widgets.
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

    def init_ui(self):
        """Initializes the ui
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

    def on_add_group(self, group):
        """Event fired when a new group is added to the group list.
        """

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

    def on_export_group_statistics(self):
        """Event fired when the user clicks on the 'Export statistics' menu button.
        """

        # No pig loaded, return
        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            logging.warning('No pigs loaded yet')
            return

        # No group defined, return
        groups_model = self._groups_list.model()
        if groups_model.rowCount() == 0:
            logging.warning('No group defined yet')
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Export statistics as ...', "Excel files (*.xls);;All Files (*)")
        if not filename:
            return

        filename_noext, ext = os.path.splitext(filename)
        if ext not in ['.xls', '.xlsx']:
            logging.warning('Bad file extension for output excel file {}. It will be replaced by ".xlsx"'.format(filename))
            filename = filename_noext + '.xlsx'

        groups_model.export_statistics(filename)

    def on_select_group(self, index):
        """Updates the individuals list view.

        Args:
            index (PyQt5.QtCore.QModelIndex): the group index
        """

        groups_model = self._groups_list.model()

        individual_model = groups_model.data(index, 257)

        self._individuals_list.setModel(individual_model)

    def on_display_group_averages(self):
        """Display the group averages plot.
        """

        # No pig loaded, return
        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            logging.warning('No pigs loaded yet')
            return

        # No group defined, return
        groups_model = self._groups_list.model()
        if groups_model.rowCount() == 0:
            logging.warning('No group defined yet')
            return

        dialog = GroupAveragesDialog(self._pigs_model, self._groups_list.model(), self)
        dialog.show()

    def on_display_group_time_effect_statistics(self):
        """Display the group/time effect statistics.
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
