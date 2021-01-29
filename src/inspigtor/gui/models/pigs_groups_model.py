import logging

import pandas as pd

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

        self._selected_groups = []

    def has_defined_intervals(self):
        """Check whether this group has defined intervals
        """

        return self._pigs_groups.has_defined_intervals()

    @property
    def pigs_groups(self):
        """
        """

        return self._pigs_groups

    def premortem_statistics(self, n_last_intervals, selected_property='APs', selected_groups=None):
        """
        """

        p_values = self._pigs_groups.premortem_statistics(n_last_intervals, selected_property=selected_property, selected_groups=selected_groups)

        return p_values

    def evaluate_global_group_effect(self, selected_property='APs', selected_groups=None):
        """
        """

        p_values = self._pigs_groups.evaluate_global_group_effect(selected_property=selected_property, selected_groups=selected_groups)
        return p_values

    def evaluate_pairwise_group_effect(self, selected_property='APs', selected_groups=None):
        """
        """

        p_values = self._pigs_groups.evaluate_pairwise_group_effect(selected_property=selected_property, selected_groups=selected_groups)
        return p_values

    def evaluate_global_time_effect(self, selected_property='APs', selected_groups=None):
        """
        """

        p_values = self._pigs_groups.evaluate_global_time_effect(selected_property=selected_property, selected_groups=selected_groups)
        return p_values

    def evaluate_pairwise_time_effect(self, selected_property='APs', selected_groups=None):
        """
        """

        p_values = self._pigs_groups.evaluate_pairwise_time_effect(selected_property=selected_property, selected_groups=selected_groups)
        return p_values

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
            self._selected_groups.append(True)
        except PigsGroupsError as error:
            logging.error(str(error))

        self.endInsertRows()

    def get_group(self, group):

        return self._pigs_groups.get_group(group)

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
        elif role == QtCore.Qt.CheckStateRole:
            return QtCore.Qt.Checked if self._selected_groups[index.row()] else QtCore.Qt.Unchecked
        elif role == PigsGroupsModel.PigsPool:
            return groups[selected_group]
        else:
            return QtCore.QVariant()

    def flags(self, index):
        """
        """

        default_flags = super(PigsGroupsModel, self).flags(index)

        return QtCore.Qt.ItemIsUserCheckable | default_flags

    def setData(self, index, value, role):
        """
        """

        if not index.isValid():
            return QtCore.QVariant()

        if role == QtCore.Qt.CheckStateRole:
            self._selected_groups[index.row()] = True if value == QtCore.Qt.Checked else False
            return True

        return super(PigsGroupsModel, self).setData(index, value, role)

    def rowCount(self, parent=None):
        """
        """

        return len(self._pigs_groups)

    @property
    def selected_groups(self):
        """
        """

        return [group_name for i, group_name in enumerate(self._pigs_groups.groups.keys()) if self._selected_groups[i]]

    @ property
    def n_selected_groups(self):
        """
        """

        return len(self.selected_groups)

    def remove_reader(self, filename):
        """
        """

        self._pigs_groups.remove_reader(filename)

        self.layoutChanged.emit()
