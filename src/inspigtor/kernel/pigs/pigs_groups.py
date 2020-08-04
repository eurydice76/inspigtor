import collections
import logging

import xlsxwriter

import numpy as np

import scipy.stats as stats

import scikit_posthocs as sk

from inspigtor.kernel.pigs.pigs_pool import PigsPoolError
from inspigtor.kernel.readers.picco2_reader import PiCCO2FileReaderError


class PigsGroupsError(Exception):
    """
    """


class PigsGroups:
    """This class implements the groups of pigs. Each member of the groups is a PigsPool object.
    """

    def __init__(self):
        """Constructor
        """

        self._groups = collections.OrderedDict()

    def __contains__(self, group):

        return group in self._groups

    def __len__(self):

        return len(self._groups)

    def _get_averages_per_interval(self, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Returns a nested dictionary where the key are the interval number and the value
        a collections.OrderedDict whose key/values are respectively the group and the average of each individual
        of the group for a given property.

        Args:
            selected_property (str): the selected property
            selected_groups (list of str): the selected groups
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the
            record intervals will be used.

        Returns:
            collections.OrderedDict: the averages per interval
        """

        if selected_groups is None:
            selected_groups = self._groups.keys()
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        averages_per_interval = collections.OrderedDict()

        for group in selected_groups:
            pigs_pool = self._groups[group]

            previous_intervals = None

            for reader in pigs_pool.pigs.values():

                try:
                    descriptive_statistics = reader.get_descriptive_statistics(selected_property, interval_indexes=interval_indexes)
                except PiCCO2FileReaderError as error:
                    raise PigsGroupsError('Can not compute statistics for pigs {}'.format(reader.filename)) from error

                intervals = descriptive_statistics['intervals']

                if previous_intervals is not None and intervals != previous_intervals:
                    raise PigsGroupsError('Individuals of the group {} do not have matching intervals'.format(group))

                averages = descriptive_statistics['averages']
                for interval, average in zip(intervals, averages):
                    averages_per_interval.setdefault(interval, {}).setdefault(group, []).append(average)

                previous_intervals = intervals

        return averages_per_interval

    def add_group(self, group, pigs_pool):
        """Add a new group.

        Args:
            group (str): the name of the group
            pigs_pool (inspigtor.kernel.pigs.pigs_pool.PigsPool): the pigs pool
        """

        if group in self._groups:
            logging.warning('The group {} has already been registered'.format(group))
            return

        self._groups[group] = pigs_pool

    def evaluate_global_group_effect(self, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Performs a statistical test to check whether the selected groups belongs to the same distribution.
        If there are only two groups, a Mann-Whitney test is performed otherwise a Kruskal-Wallis test
        is performed.

        Args:
            selected_property (str): the selected property
            selected_groups (list of str): the selected group. if None all the groups of the model will be used.
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the
            record intervals will be used.

        Returns:
            list: the p values resulting from Kruskal-Wallis or Mann-Whitney tests.
        """

        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        n_groups = len(selected_groups)
        if n_groups < 2:
            raise PigsGroupsError('There is less than two groups. Can not perform any global statistical test.')

        averages_per_interval = self._get_averages_per_interval(selected_property, selected_groups=selected_groups, interval_indexes=interval_indexes)

        # Loop over the intervals
        p_values = []
        for selected_groups in averages_per_interval.values():

            if n_groups == 2:
                p_value = stats.mannwhitneyu(*selected_groups.values(), alternative='two-sided').pvalue
            else:
                p_value = stats.kruskal(*selected_groups.values()).pvalue

            p_values.append(p_value)

        return p_values

    def evaluate_pairwise_group_effect(self, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Performs a pairwise statistical test to check whether each pair of groups belongs to the same distribution.
        This should be evaluated only if the number of groups is >= 2.

        Args:
            selected_property (str): the selected property
            selected_groups (list of str): the selected group. if None all the groups of the model will be used.
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the
            record intervals will be used.

        Returns:
            dict: the p values defined for each pair of groups resulting from the Dunn test.
        """

        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        n_groups = len(selected_groups)
        if n_groups < 2:
            raise PigsGroupsError('There is less than two groups. Can not perform any global statistical test.')

        averages_per_interval = self._get_averages_per_interval(selected_property, selected_groups=selected_groups, interval_indexes=interval_indexes)

        p_values_per_interval = []
        for averages_per_group in averages_per_interval.values():
            p_values_per_interval.append(sk.posthoc_dunn(list(averages_per_group.values())))

        pairwise_p_values = collections.OrderedDict()
        for p_values in p_values_per_interval:
            for i in range(0, n_groups - 1):
                group_i = selected_groups[i]
                for j in range(i+1, n_groups):
                    group_j = selected_groups[j]
                    key = '{} vs {}'.format(group_i, group_j)
                    pairwise_p_values.setdefault(key, []).append(p_values.iloc[i, j])

        return pairwise_p_values

    def export_statistics(self, filename, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Export basic statistics (average, median, std, quartile ...) for each group and interval to an excel file.

        Args:
            filename (str): the output excel filename
            selected_property (str): the selected property
            selected_groups (list of str): the selected group. if None all the groups of the model will be used.
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the
            record intervals will be used.
        """

        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        averages_per_interval = self._get_averages_per_interval(selected_property, selected_groups=selected_groups, interval_indexes=interval_indexes)

        workbook = xlsxwriter.Workbook(filename)
        for group in selected_groups:
            worksheet = workbook.add_worksheet(group)
            worksheet.write('K1', 'Selected property')
            worksheet.write('K2', selected_property)
            worksheet.write('M1', 'Pigs')
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

                pigs = self._groups[group_name].pigs.keys()
                for j, pig in enumerate(pigs):
                    worksheet.write('M{}'.format(j+2), pig)

        workbook.close()

    @ property
    def groups(self):
        """Getter for self._groups attribute. Returns the registered groups.

        Returns:
            dict: the registered groups
        """

        return self._groups

    def set_record_intervals(self, intervals):
        """Set the record intervals.

        Args:
            intervals (list of 4-tuples): the record time in seconds. List of 4-tuples of the form (start,end,record,offset).
        """

        for pool in self._groups.values():

            pool.set_record_intervals(intervals)


if __name__ == '__main__':

    import sys
    from inspigtor.kernel.pigs.pigs_pool import PigsPool

    pool1 = PigsPool()
    pool1.add_reader(sys.argv[1])
    pool1.add_reader(sys.argv[2])

    pool2 = PigsPool()
    pool2.add_reader(sys.argv[1])
    pool2.add_reader(sys.argv[2])

    groups = PigsGroups()
    groups.add_group('group1', pool1)
    groups.add_group('group2', pool2)
    groups.set_record_intervals([('00:00:00', '01:00:00', 300, 30)])
    print(groups.evaluate_global_group_effect('APs'))
    print(groups.evaluate_pairwise_group_effect('APs'))
    groups.export_statistics('test.xlsx', selected_property='APs')
