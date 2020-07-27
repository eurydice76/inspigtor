import logging

import numpy as np

from PyQt5 import QtCore, QtGui


class IndividualsModel(QtGui.QStandardItemModel):
    """This model describes a group of pigs.
    """

    def __init__(self, pigs_model, parent):

        super(IndividualsModel, self).__init__(parent)

        self._pigs_model = pigs_model

    def get_averages(self):
        """
        """

        pigs = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        all_individual_averages = []
        previous_intervals = None
        for pig in pigs:

            pig_item = self._pigs_model.findItems(pig, QtCore.Qt.MatchExactly)[0]
            reader = pig_item.data(257)
            individual_averages = reader.get_averages(self._pigs_model.selected_property)
            if not individual_averages:
                logging.warning('No averages computed for file {}'.format(reader.filename))
                continue

            intervals = [interval for interval, _, _ in individual_averages]
            averages = [average for _, average, _ in individual_averages]

            all_individual_averages.append(averages)
            if previous_intervals is not None and intervals != previous_intervals:
                logging.warning('Individuals of the group do not have matching intervals')
                return None

            previous_intervals = intervals

        all_individual_averages = np.array(all_individual_averages)

        averages = np.average(all_individual_averages, axis=0)
        stds = np.std(all_individual_averages, axis=0)

        return averages, stds
