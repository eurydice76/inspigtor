"""
"""

import numpy as np

from PyQt5 import QtCore, QtGui
import collections
import logging

import scipy.stats as stats
import scikit_posthocs as sk

import xlsxwriter


class GroupsModel(QtGui.QStandardItemModel):
    """This model describes a group of pigs.
    """

    def __init__(self, pigs_model):
        """Constructor

        Args:
            pigs_model ()
        """

        super(GroupsModel, self).__init__()

        self._pigs_model = pigs_model

    def _get_averages_per_interval(self, selected_groups):
        """Returns a nested dictionary where the key are the interval number and the value
        a collections.OrderedDict whose key/values are respectively the group and the average of each individual
        of the group for a given property.

        Args:
            groups (list of str): the selected groups

        Returns:
            collections.OrderedDict: the averages per interval
        """

        all_groups = set([self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())])
        groups = list(all_groups.intersection(selected_groups))
        if not groups:
            return None

        averages_per_interval = collections.OrderedDict()

        for group in groups:
            items = self.findItems(group, QtCore.Qt.MatchExactly)
            if not items:
                continue
            item = items[0]
            individuals_model = item.data(257)

            pigs = [individuals_model.item(i).data(QtCore.Qt.DisplayRole) for i in range(individuals_model.rowCount())]
            previous_intervals = None
            for pig in pigs:

                pig_item = self._pigs_model.findItems(pig, QtCore.Qt.MatchExactly)[0]
                reader = pig_item.data(257)
                individual_averages = reader.get_descriptive_statistics(self._pigs_model.selected_property)
                if not individual_averages:
                    logging.warning('No averages computed for file {}'.format(reader.filename))
                    return None

                intervals = individual_averages['intervals']

                if previous_intervals is not None and intervals != previous_intervals:
                    logging.warning('Individuals of the group {} do not have matching intervals'.format(group))
                    return None

                averages = individual_averages['averages']
                for interval, average in zip(intervals, averages):
                    averages_per_interval.setdefault(interval, collections.OrderedDict()).setdefault(group, []).append(average)

                previous_intervals = intervals

        return averages_per_interval

    def evaluate_global_group_effect(self, groups=None):
        """Performs a statistical test to check whether the groups belongs to the same distribution.
        If there are only two groups, a Mann-Whitney test is performed otherwise a Kruskal-Wallis test
        is performed.

        Args:
            groups (list of str): the selected group. if None all the groups of the model will be used.

        Returns:
            list: the p values resulting from Kruskal-Wallis or Mann-Whitney tests.
        """

        if groups is None:
            groups = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        n_groups = len(groups)
        if n_groups < 2:
            logging.warning('There is less than two groups. Can not perform any global statistical test.')
            return []

        averages_per_interval = self._get_averages_per_interval(groups)
        if not averages_per_interval:
            return None

        p_values = []
        for groups in averages_per_interval.values():

            if n_groups == 2:
                p_value = stats.mannwhitneyu(*groups.values(), alternative='two-sided').pvalue
            else:
                p_value = stats.kruskal(*groups.values()).pvalue

            p_values.append(p_value)

        return p_values

    def evaluate_pairwise_group_effect(self, groups=None):
        """Performs a pairwise statistical test to check whether each pair of groups belongs to the same distribution.
        This should be evaluated only if the number of groups is >= 2.

        Args:
            groups (list of str): the selected group. if None all the groups of the model will be used.

        Returns:
            dict: the p values define for each pair of groups resulting from the Dunn test.
        """

        if groups is None:
            groups = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        n_groups = len(groups)
        if n_groups < 2:
            logging.warning('There is less than two groups. Can not perform any global statistical test.')
            return []

        averages_per_interval = self._get_averages_per_interval(groups)
        if not averages_per_interval:
            return None

        group_names = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        p_values_per_interval = []
        for groups in averages_per_interval.values():
            p_values_per_interval.append(sk.posthoc_dunn(list(groups.values())))

        pairwise_p_values = collections.OrderedDict()
        for p_values in p_values_per_interval:
            for i in range(0, n_groups - 1):
                group_i = group_names[i]
                for j in range(i+1, n_groups):
                    group_j = group_names[j]
                    key = '{} vs {}'.format(group_i, group_j)
                    pairwise_p_values.setdefault(key, []).append(p_values.iloc[i, j])

        return pairwise_p_values

    def evaluate_global_time_effect(self, groups=None):
        """Performs a Friedman statistical test to check whether the groups belongs to the same distribution.
        If there are only two groups, a Mann-Whitney test is performed otherwise a Kruskal-Wallis test
        is performed.

        Args:
            groups (list of str): the selected group. if None all the groups of the model will be used.

        Returns:
            collections.OrderedDict: the p values for each group resulting from the Friedman test
        """

        if groups is None:
            groups = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        averages_per_interval = self._get_averages_per_interval(groups)
        if not averages_per_interval:
            return None

        averages_per_group = collections.OrderedDict()

        for groups_dict in averages_per_interval.values():

            for group, averages in groups_dict.items():

                averages_per_group.setdefault(group, []).append(averages)

        p_values = collections.OrderedDict()

        for group, averages in averages_per_group.items():
            p_values[group] = stats.friedmanchisquare(*averages).pvalue

        return p_values

    def evaluate_pairwise_time_effect(self, groups=None):
        """Performs a Dunn statistical test to check whether within each group the averages values defined over
        intervals belongs to the same distribution.

        Args:
            groups(list of str): the selected group. if None all the groups of the model will be used.

        Returns:
            collections.OrderedDict: the p values matrix for each group resulting from the Dunn test
        """

        if groups is None:
            groups = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        averages_per_interval = self._get_averages_per_interval(groups)

        averages_per_group = collections.OrderedDict()

        for groups in averages_per_interval.values():

            for group, averages in groups.items():

                averages_per_group.setdefault(group, []).append(averages)

        p_values = collections.OrderedDict()

        for group, averages in averages_per_group.items():
            df = sk.posthoc_dunn(averages)
            df = df.round(4)

            p_values[group] = df

        return p_values

    def export_statistics(self, filename, groups=None):
        """Export basic statistics (average, median, std, quartile ...) for each group and interval to an excel file.

        Args:
            filename (str): the output excel filename
            groups(list of str): the selected group. if None all the groups of the model will be used.
        """

        if groups is None:
            groups = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        averages_per_interval = self._get_averages_per_interval(groups)
        if not averages_per_interval:
            return None

        workbook = xlsxwriter.Workbook(filename)
        for i in range(self.rowCount()):
            item = self.item(i)
            group_name = item.data(QtCore.Qt.DisplayRole)
            worksheet = workbook.add_worksheet(group_name)
            worksheet.write('K1', 'Selected property')
            worksheet.write('K2', self._pigs_model.selected_property)
            worksheet.write('A1', 'Interval')
            worksheet.write('B1', 'Average')
            worksheet.write('C1', 'Std Dev')
            worksheet.write('D1', 'Median')
            worksheet.write('E1', '1st quartile')
            worksheet.write('F1', '3rd quartile')
            worksheet.write('G1', 'Skewness')
            worksheet.write('H1', 'kurtosis')

        for i, (interval, groups) in enumerate(averages_per_interval.items()):

            for group_name, averages in groups.items():

                worksheet = workbook.get_worksheet_by_name(group_name)
                worksheet.write('A{}'.format(i+2), interval)
                worksheet.write('B{}'.format(i+2), np.average(averages))
                worksheet.write('C{}'.format(i+2), np.std(averages))
                worksheet.write('D{}'.format(i+2), np.median(averages))
                worksheet.write('E{}'.format(i+2), np.quantile(averages, 0.25))
                worksheet.write('F{}'.format(i+2), np.quantile(averages, 0.75))
                worksheet.write('G{}'.format(i+2), stats.skew(averages))
                worksheet.write('H{}'.format(i+2), stats.kurtosis(averages))

        workbook.close()

    def premortem_statistics(self, n_last_intervals, groups=None):
        """Compute the premortem statisitcs to assess putative time effect.

        This is basically the same procedure than for the global and pairwise time effect analysis
        excepted that only the interval before Tinitial and the n last intervals are considered.
        This allows pigs with different intervals due to different time of death to be compared through
        a statistical test.

        Args:
            n_last_intervals (int): the number of last intervals to consider
            groups (list of str): the groups on which the analysis should be performed
        """

        if groups is None:
            groups = [self.item(i).data(QtCore.Qt.DisplayRole) for i in range(self.rowCount())]

        friedman_statistics = {}
        dunn_statistics = {}

        for group in groups:
            items = self.findItems(group, QtCore.Qt.MatchExactly)
            if not items:
                continue

            averages = []

            individuals_model = items[0].data(257)
            for i in range(individuals_model.rowCount()):
                pig_name = individuals_model.item(i).data(QtCore.Qt.DisplayRole)
                try:
                    pig_item = self._pigs_model.findItems(pig_name, QtCore.Qt.MatchExactly)[0]
                except IndexError:
                    return None
                reader = pig_item.data(257)

                t_initial_interval_index = reader.t_initial_interval_index
                t_final_interval_index = reader.t_final_interval_index

                # These are the intervals used for the analysis
                intervals = [t_initial_interval_index - 1] + list(range(t_final_interval_index-n_last_intervals+1, t_final_interval_index+1))

                descriptive_statistics = reader.get_descriptive_statistics(self._pigs_model.selected_property, interval_indexes=intervals)
                if not descriptive_statistics:
                    return None

                averages.append(descriptive_statistics['averages'])

            # Transpose the nested list such as the number rows is the number of intervals and the number of columns the number of individuals
            averages = [list(x) for x in zip(*averages)]

            friedman_statistics[group] = stats.friedmanchisquare(*averages).pvalue
            df = sk.posthoc_dunn(averages)
            df = df.round(4)
            dunn_statistics[group] = df

        return friedman_statistics, dunn_statistics
