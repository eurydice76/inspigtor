import logging
import os

from PyQt5 import QtGui, QtWidgets

from inspigtor.gui.dialogs.group_averages_dialog import GroupAveragesDialog
from inspigtor.gui.dialogs.group_medians_dialog import GroupMediansDialog
from inspigtor.gui.dialogs.group_effect_dialog import GroupEffectDialog
from inspigtor.gui.dialogs.premortem_statistics_dialog import PreMortemStatisticsDialog
from inspigtor.gui.dialogs.time_effect_dialog import TimeEffectDialog
from inspigtor.gui.models.pigs_groups_model import PigsGroupsModel
from inspigtor.gui.models.pigs_pool_model import PigsPoolModel
from inspigtor.gui.views.pigs_pool_listview import PigsPoolListView
from inspigtor.kernel.pigs.pigs_groups import PigsGroupsError


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
        self._main_window.display_group_effect_statistics.connect(self.on_display_group_effect_statistics)
        self._main_window.display_time_effect_statistics.connect(self.on_display_time_effect_statistics)
        self._main_window.display_premortem_statistics.connect(self.on_display_premortem_statistics)
        self._main_window.export_group_statistics.connect(self.on_export_group_statistics)
        self._main_window.display_group_medians.connect(self.on_display_group_medians)
        self._main_window.import_groups_from_directories.connect(self.on_import_groups)

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
        groups_model = PigsGroupsModel(self)
        self._groups_list.setModel(groups_model)

        self._individuals_list = PigsPoolListView(self._pigs_model, self)
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
        groups_model.add_group(group)
        last_index = groups_model.index(groups_model.rowCount()-1, 0)
        self._groups_list.setCurrentIndex(last_index)

    def on_display_group_averages(self):
        """Display the group averages.
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

        if not groups_model.has_defined_intervals():
            logging.error('No intervals defined yet for selected groups')
            return

        dialog = GroupAveragesDialog(self._main_window.selected_property, self._groups_list.model(), self)
        dialog.show()

    def on_display_group_medians(self):
        """Display the group medians.
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

        if not groups_model.has_defined_intervals():
            logging.error('No intervals defined yet for selected groups')
            return

        dialog = GroupMediansDialog(self._main_window.selected_property, self._groups_list.model(), self)
        dialog.show()

    def on_display_group_effect_statistics(self):
        """Display the group effect statistics.
        """

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            logging.warning('No pigs loaded yet')
            return

        groups_model = self._groups_list.model()
        if groups_model.rowCount() == 0:
            logging.warning('No groups defined yet')
            return

        selected_property = self._main_window.selected_property

        global_effect = groups_model.evaluate_global_group_effect(selected_property=selected_property, selected_groups=groups_model.selected_groups)
        if global_effect.empty:
            return

        pairwise_effect = groups_model.evaluate_pairwise_group_effect(selected_property=selected_property, selected_groups=groups_model.selected_groups)
        if not pairwise_effect:
            return

        dialog = GroupEffectDialog(selected_property, global_effect, pairwise_effect, self)
        dialog.show()

    def on_display_time_effect_statistics(self):
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

        selected_property = self._main_window.selected_property

        global_effect = groups_model.evaluate_global_time_effect(selected_property=selected_property, selected_groups=groups_model.selected_groups)
        if global_effect.empty:
            return

        pairwise_effect = groups_model.evaluate_pairwise_time_effect(selected_property=selected_property, selected_groups=groups_model.selected_groups)
        if not pairwise_effect:
            return

        dialog = TimeEffectDialog(selected_property, global_effect, pairwise_effect, self)
        dialog.show()

    def on_display_premortem_statistics(self):
        """Display the premortem statistics.
        """

        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            logging.warning('No pigs loaded yet')
            return

        groups_model = self._groups_list.model()
        if groups_model.rowCount() == 0:
            logging.warning('No groups defined yet')
            return

        selected_property = self._main_window.selected_property

        dialog = PreMortemStatisticsDialog(selected_property, self._groups_list.model(), self)
        dialog.show()

    def on_export_group_statistics(self):
        """Event fired when the user clicks on the 'Export statistics' menu button.
        """

        # No pig loaded, return
        n_pigs = self._pigs_model.rowCount()
        if n_pigs == 0:
            logging.warning('No pigs loaded yet')
            return

        # No group defined, return
        pigs_groups_model = self._groups_list.model()
        if pigs_groups_model.rowCount() == 0:
            logging.warning('No group defined yet')
            return

        if not pigs_groups_model.has_defined_intervals():
            logging.error('No intervals defined yet for selected groups')
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Export statistics as ...', filter="Excel files (*.xls *.xlsx)")
        if not filename:
            return

        filename_noext, ext = os.path.splitext(filename)
        if ext not in ['.xls', '.xlsx']:
            logging.warning('Bad file extension for output excel file {}. It will be replaced by ".xlsx"'.format(filename))
            filename = filename_noext + '.xlsx'

        try:
            pigs_groups_model.pigs_groups.export_statistics(filename, selected_property=self._main_window.selected_property)
        except PigsGroupsError as error:
            logging.error(str(error))
            return

    def on_import_groups(self, groups):
        """Event fired when the user click on Groups -> Import from directories menu button.
        """

        for group, files in groups.items():
            self.on_add_group(group)
            for filename in files:
                pigs_pool = self._groups_list.model().get_group(group)
                pigs_pool.add_reader(self._pigs_model.get_reader(filename))

    def on_select_group(self, index):
        """Updates the individuals list view.

        Args:
            index (PyQt5.QtCore.QModelIndex): the group index
        """

        groups_model = self._groups_list.model()

        current_pig_pool = groups_model.data(index, groups_model.PigsPool)

        pigs_pool_model = PigsPoolModel(self, current_pig_pool)

        self._individuals_list.setModel(pigs_pool_model)

    def on_remove_reader(self, filename):
        """Delete the selected reader filename from the pig pools which store it.
        """

        groups_model = self._groups_list.model()

        groups_model.remove_reader(filename)

        pigs_pool_model = self._individuals_list.model()
        if pigs_pool_model is not None:
            pigs_pool_model.layoutChanged.emit()
