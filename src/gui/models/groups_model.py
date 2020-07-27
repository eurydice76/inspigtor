"""
"""

from PyQt5 import QtCore, QtGui
import collections
import logging

import scipy.stats as scistats
import scikit_posthocs as scikit


class GroupsModel(QtGui.QStandardItemModel):
    """This model describes a group of pigs.
    """

    def __init__(self, pigs_model):

        super(GroupsModel, self).__init__()

        self._pigs_model = pigs_model

    def _get_averages_per_interval(self):
        """Returns a nested dictionary where the key are the interval number and the value 
        a collections.OrderedDict whose key/values are respectively the group and the average of each individual 
        of the group for a given property.

        Returns:
            collections.OrderedDict: the averages per interval
        """

        averages_per_interval = collections.OrderedDict()

        for i in range(self.rowCount()):
            item = self.item(i)
            group = item.data(QtCore.Qt.DisplayRole)
            individuals_model = item.data(257)

            pigs = [individuals_model.item(i).data(QtCore.Qt.DisplayRole) for i in range(individuals_model.rowCount())]
            previous_intervals = None
            for pig in pigs:

                pig_item = self._pigs_model.findItems(pig, QtCore.Qt.MatchExactly)[0]
                reader = pig_item.data(257)
                individual_averages = reader.get_averages(self._pigs_model.selected_property)
                if not individual_averages:
                    logging.warning('No averages computed for file {}'.format(reader.filename))
                    return collections.OrderedDict()

                intervals = [interval for interval, _, _ in individual_averages]
                averages = [average for _, average, _ in individual_averages]

                if previous_intervals is not None and intervals != previous_intervals:
                    logging.warning('Individuals of the group do not have matching intervals')
                    return collections.OrderedDict()

                for interval, average in zip(intervals, averages):
                    averages_per_interval.setdefault(interval, collections.OrderedDict()).setdefault(group, []).append(average)

                previous_intervals = intervals

        return averages_per_interval

    def evaluate_global_group_effect(self):
        """Performs a statistical test to check whether the groups belongs to the same distribution.
        If there are only two groups, a Mann-Whitney test is performed otherwise a Kruskal-Wallis test 
        is performed.

        Returns:
            list: the p values resulting from Kruskal-Wallis or Mann-Whitney tests.
        """

        n_groups = self.rowCount()
        if n_groups < 2:
            logging.warning('There is less than two groups. Can not perform any global statistical test.')
            return []

        averages_per_interval = self._get_averages_per_interval()

        p_values = []
        for groups in averages_per_interval.values():

            if n_groups == 2:
                p_value = scistats.mannwhitneyu(*groups.values(), alternative='two-sided').pvalue
            else:
                p_value = scistats.kruskal(*groups.values()).pvalue

            p_values.append(p_value)

        return p_values

    def evaluate_pairwise_group_effect(self):
        """Performs a pairwise statistical test to check whether each pair of groups belongs to the same distribution.
        This should be evaluated only if the number of groups is >= 2.

        Returns:
            dict: the p values define for each pair of groups resulting from the Dunn test.
        """

        n_groups = self.rowCount()
        if n_groups < 2:
            logging.warning('There is less than two groups. Can not perform any global statistical test.')
            return []

        averages_per_interval = self._get_averages_per_interval()

        group_names = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        p_values_per_interval = []
        for groups in averages_per_interval.values():
            p_values_per_interval.append(scikit.posthoc_dunn(list(groups.values())))

        pairwise_p_values = collections.OrderedDict()
        for p_values in p_values_per_interval:
            for i in range(0, n_groups - 1):
                group_i = group_names[i]
                for j in range(i+1, n_groups):
                    group_j = group_names[j]
                    key = '{} vs {}'.format(group_i, group_j)
                    pairwise_p_values.setdefault(key, []).append(p_values.iloc[i, j])

        return pairwise_p_values

    def evaluate_global_time_effect(self):
        """Performs a Friedman statistical test to check whether the groups belongs to the same distribution.
        If there are only two groups, a Mann-Whitney test is performed otherwise a Kruskal-Wallis test 
        is performed.

        Returns:
            collections.OrderedDict: the p values for each group resulting from the Friedman test
        """

        averages_per_interval = self._get_averages_per_interval()

        averages_per_group = collections.OrderedDict()

        for groups in averages_per_interval.values():

            for group, averages in groups.items():

                averages_per_group.setdefault(group, []).append(averages)

        p_values = collections.OrderedDict()

        for group, averages in averages_per_group.items():
            p_values[group] = scistats.friedmanchisquare(*averages).pvalue

        return p_values

    def evaluate_pairwise_time_effect(self):
        """Performs a Dunn statistical test to check whether within each group the averages values defined over 
        intervals belongs to the same distribution.

        Returns:
            collections.OrderedDict: the p values matrix for each group resulting from the Dunn test
        """

        averages_per_interval = self._get_averages_per_interval()

        averages_per_group = collections.OrderedDict()

        for groups in averages_per_interval.values():

            for group, averages in groups.items():

                averages_per_group.setdefault(group, []).append(averages)

        p_values = collections.OrderedDict()

        for group, averages in averages_per_group.items():
            df = scikit.posthoc_dunn(averages)
            df = df.round(4)
            df.index = list(averages_per_interval.keys())
            df.columns = list(averages_per_interval.keys())
            p_values[group] = df

        return p_values
