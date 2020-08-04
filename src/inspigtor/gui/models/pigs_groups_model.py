import logging

from PyQt5 import QtCore

from inspigtor.kernel.pigs.pigs_groups import PigsGroups, PigsGroupsError
from inspigtor.kernel.pigs.pigs_pool import PigsPool, PigsPoolError


class PigsGroupsModel(QtCore.QAbstractListModel):
    """This model describes groups of pigs.
    """

    PigsPool = QtCore.Qt.UserRole + 1

    def __init__(self, parent):
        """Constructor.

        Args:
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(PigsGroupsModel, self).__init__(parent)

        self._pigs_groups = PigsGroups()

    @property
    def pigs_groups(self):
        """
        """

        return self._pigs_groups

    def premortem_statistics(self, n_last_intervals, selected_property='APs'):
        """
        """

        n_groups = self.rowCount()

        p_values = [self.data(self.index(row), PigsGroupsModel.PigsPool).premortem_statistics(
            n_last_intervals, selected_property=selected_property) for row in range(n_groups)]

        return p_values

    def evaluate_global_group_effect(self, selected_property='APs'):
        """
        """

        p_values = self._pigs_groups.evaluate_global_group_effect(selected_property=selected_property)

        return p_values

    def evaluate_pairwise_group_effect(self, selected_property='APs'):
        """
        """

        p_values = self._pigs_groups.evaluate_pairwise_group_effect(selected_property=selected_property)

        return p_values

    def evaluate_global_time_effect(self, selected_property='APs'):
        """
        """

        n_groups = self.rowCount()

        group_names = [self.data(self.index(row), QtCore.Qt.DisplayRole) for row in range(n_groups)]

        try:
            p_values = [self.data(self.index(row), PigsGroupsModel.PigsPool).evaluate_global_time_effect(
                selected_property=selected_property) for row in range(n_groups)]
        except PigsPoolError as error:
            logging.error(str(error))
            return

        return dict(zip(group_names, p_values))

    def evaluate_pairwise_time_effect(self, selected_property='APs'):
        """
        """

        n_groups = self.rowCount()

        group_names = [self.data(self.index(row), QtCore.Qt.DisplayRole) for row in range(n_groups)]

        p_values = [self.data(self.index(row), PigsGroupsModel.PigsPool).evaluate_pairwise_time_effect(
            selected_property=selected_property) for row in range(n_groups)]

        return dict(zip(group_names, p_values))

    def add_group(self, group):
        """Add a group to the model.

        Args:
            group (str): the group name
        """

        if group in self._pigs_groups:
            logging.warning('A group with the name ({}) already exists.'.format(group))
            return

        self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())

        try:
            self._pigs_groups.add_group(group, PigsPool())
        except PigsGroupsError as error:
            logging.error(str(error))

        self.endInsertRows()

    def data(self, index, role):
        """
        """

        if not index.isValid():
            return QtCore.QVariant()

        groups = self._pigs_groups.groups

        group_names = list(groups.keys())

        selected_group = group_names[index.row()]

        if role == QtCore.Qt.DisplayRole:
            return selected_group
        elif role == PigsGroupsModel.PigsPool:
            return groups[selected_group]
        else:
            return QtCore.QVariant()

    def rowCount(self, parent=None):

        return len(self._pigs_groups)
