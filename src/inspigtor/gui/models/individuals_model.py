import logging

import numpy as np

from PyQt5 import QtCore, QtGui


class IndividualsModel(QtGui.QStandardItemModel):
    """This model describes a group of pigs.

    It is the model used in the individuals list view showing the set of pigs that belongs to a given group.
    """

    def __init__(self, pigs_model, parent):
        """Constructor.

        Args:
            pigs_model (inspigtor.gui.models.pigs_data_model.PigsDataModel): the underlying model for the registered pigs
            parent (PyQt5.QtWidgets.QObject): the parent object
        """

        super(IndividualsModel, self).__init__(parent)

        self._pigs_model = pigs_model

    def get_averages(self):
        """Returns the averages of each individual of this set.
        """

        pigs = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        all_individual_averages = []
        previous_intervals = None
        for pig in pigs:

            pig_item = self._pigs_model.findItems(pig, QtCore.Qt.MatchExactly)[0]
            reader = pig_item.data(257)
            individual_averages = reader.get_descriptive_statistics(self._pigs_model.selected_property)
            if not individual_averages:
                return None

            intervals = individual_averages['intervals']
            averages = individual_averages['averages']

            all_individual_averages.append(averages)
            if previous_intervals is not None and intervals != previous_intervals:
                logging.error('Individuals do not have matching intervals.')
                return None

            previous_intervals = intervals

        # Transpose the nested list
        all_individual_averages = [list(x) for x in zip(*all_individual_averages)]

        return all_individual_averages

    def get_group_averages(self):
        """Compute the average and standard deviation for this set of individuals.

        Returns:
            2-tuple: the average and standard deviation for each interval for this set of individuals
        """

        all_individual_averages = self.get_averages()
        if not all_individual_averages:
            return None

        all_individual_averages = np.array(all_individual_averages)

        averages = np.average(all_individual_averages, axis=1)
        stds = np.std(all_individual_averages, axis=1)

        return averages, stds
