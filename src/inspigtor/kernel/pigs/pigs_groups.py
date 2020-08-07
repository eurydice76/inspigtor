import collections
import copy
import logging
import string

import xlsxwriter

import numpy as np

import scipy.stats as stats

import scikit_posthocs as sk

from inspigtor.kernel.pigs.pigs_pool import PigsPoolError
from inspigtor.kernel.readers.picco2_reader import PiCCO2FileReaderError
from inspigtor.kernel.utils.stats import statistical_functions
from inspigtor.kernel.utils.progress_bar import progress_bar


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
            list of int: the valid intervals for which the Kruskal-Wallis or Mann-Whitney tests could be performed.
            list of float: the p values resulting from Kruskal-Wallis or Mann-Whitney tests.

        Raises:
            PigsGroupsError: if the number of groups is less than two.
        """

        # If selected groups is not provided by the user take all the groups
        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        if len(selected_groups) < 2:
            raise PigsGroupsError('There is less than two groups. Can not perform any global statistical test.')

        progress_bar.reset(len(selected_groups))
        averages_per_group = {}
        for i, group in enumerate(selected_groups):
            try:
                averages_per_group[group] = self._groups[group].get_statistics(selected_property, selected_statistics='mean', interval_indexes=interval_indexes)
            except PigsPoolError as error:
                logging.error(str(error))
                continue
            finally:
                progress_bar.update(i+1)

        if not averages_per_group:
            raise PigsGroupsError('There is less than two groups. Can not perform any global statistical test.')

        max_n_intervals = max([v.shape[0] for v in averages_per_group.values()])

        progress_bar.reset(max_n_intervals)

        valid_intervals = []
        p_values = []
        n_groups = []
        # Loop over the intervals
        for interv in range(max_n_intervals):
            groups = []
            for averages in averages_per_group.values():
                # This interval is ont defined for this group, skip the group
                if interv >= averages.shape[0]:
                    continue
                values = [v for v in averages[interv, :] if not np.isnan(v)]
                if not values:
                    continue
                groups.append(values)

            valid_intervals.append(interv)
            if len(groups) < 2:
                n_groups.append(np.nan)
                p_values.append(np.nan)
            else:
                n_groups.append(len(groups))
                if n_groups[-1] == 2:
                    p_value = stats.mannwhitneyu(*groups, alternative='two-sided').pvalue
                else:
                    p_value = stats.kruskal(*groups).pvalue

                p_values.append(p_value)

            progress_bar.update(interv+1)

        return valid_intervals, p_values, n_groups

    def evaluate_global_time_effect(self, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Performs a Friedman statistical test to check whether the averages defined for each pig over record intervals
        belongs to the same distribution.

        Args:
            selected_property (str): the selected property
            selected_groups (list of str): the selected group. if None all the groups will be used.
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.

        Returns:
            list of str: the valid groups for which the Friedman test could be performed.
            list of float: the Friedman p values
        """

        # If selected groups is not provided by the user take all the groups
        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        progress_bar.reset(len(selected_groups))
        valid_groups = []
        p_values = []
        for i, group in enumerate(selected_groups):
            try:
                _, p_value = self._groups[group].evaluate_global_time_effect(selected_property=selected_property, interval_indexes=interval_indexes)
            except PigsPoolError:
                logging.error('Can not evaluate global time effect for group {}'.format(group))
                continue
            else:
                valid_groups.append(group)
                p_values.append(p_value)
            finally:
                progress_bar.update(i+1)

        return valid_groups, p_values

    def evaluate_pairwise_group_effect(self, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Performs a pairwise statistical test to check whether each pair of groups belongs to the same distribution.
        This should be evaluated only if the number of groups is >= 2.

        Args:
            selected_property (str): the selected property.
            selected_groups (list of str): the selected group. if None all the groups of the model will be used.
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the
            record intervals will be used.

        Returns:
            list of int: the list of valid intervals for which the Dunn test could be performed
            dict: the p values defined for each pair of groups resulting from the Dunn test.

        Raises:
            PigsGroupsError: if the number of groups is less than two.
        """

        # If selected groups is not provided by the user take all the groups
        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        if len(selected_groups) < 2:
            raise PigsGroupsError('There is less than two groups. Can not perform any global statistical test.')

        averages_per_group = {}
        for group in selected_groups:
            try:
                averages_per_group[group] = self._groups[group].get_statistics(selected_property, selected_statistics='mean', interval_indexes=interval_indexes)
            except PigsPoolError as error:
                logging.error(str(error))
                continue

        if not averages_per_group:
            raise PigsGroupsError('There is less than two groups. Can not perform any global statistical test.')

        max_n_intervals = max([v.shape[0] for v in averages_per_group.values()])

        progress_bar.reset(max_n_intervals)
        valid_intervals = []
        p_values = collections.OrderedDict()
        # Loop over the intervals
        for interv in range(max_n_intervals):
            groups = []
            group_names = []
            for group_name, averages in averages_per_group.items():
                # This interval is ont defined for this group, skip the group
                if interv >= averages.shape[0]:
                    continue
                values = [v for v in averages[interv, :] if not np.isnan(v)]
                if not values:
                    continue
                group_names.append(group_name)
                groups.append(values)

            n_groups = len(groups)
            if n_groups >= 2:
                valid_intervals.append(interv)
                data_frame = sk.posthoc_dunn(groups)
                for i in range(0, n_groups - 1):
                    group_i = selected_groups[i]
                    for j in range(i+1, n_groups):
                        group_j = selected_groups[j]
                        key = '{} vs {}'.format(group_i, group_j)
                        if key not in p_values:
                            p_values[key] = {'intervals': [], 'values': []}
                        p_values[key]['intervals'].append(interv)
                        p_values[key]['values'].append(data_frame.iloc[i, j])
            progress_bar.update(interv+1)

        return p_values

    def evaluate_pairwise_time_effect(self, selected_property='APs', selected_groups=None, interval_indexes=None):
        """Performs a Dunn statistical test to check whether the averages defined for each pig over record intervals belongs
        to the same distribution pairwisely.

        Args:
            selected_property (str): the selected property
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.

        Returns:
            list of str: the valid groups for which the Dunn test could be performed.
            list of pandas.DataFrame: the p values matrix resulting from Dunn test
        """

        # If selected groups is not provided by the user take all the groups
        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        progress_bar.reset(len(selected_groups))
        valid_groups = []
        valid_intervals = []
        p_values = []
        for i, group in enumerate(selected_groups):
            try:
                intervals, p_values_df = self._groups[group].evaluate_pairwise_time_effect(
                    selected_property=selected_property, interval_indexes=interval_indexes)
            except PigsPoolError:
                logging.error('Can not evaluate pairwise time effect for group {}'.format(group))
            else:
                valid_groups.append(group)
                valid_intervals.append(intervals)
                p_values.append(p_values_df)
            finally:
                progress_bar.update(i+1)

        return valid_groups, valid_intervals, p_values

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

        alphabet = list(string.ascii_uppercase)

        workbook = xlsxwriter.Workbook(filename)
        for group in selected_groups:

            try:
                reduced_averages = self._groups[group].reduced_statistics(selected_property, selected_statistics='mean',
                                                                          interval_indexes=interval_indexes, output_statistics=statistical_functions.keys())
            except PigsPoolError as error:
                logging.error(str(error))
                return

            # Create the excel worksheet
            worksheet = workbook.add_worksheet(group)

            worksheet.write('A1', 'interval')
            worksheet.write('L1', 'selected property')
            worksheet.write('L2', selected_property)
            worksheet.write('N1', 'pigs')

            # Add titles
            for col, func in enumerate(statistical_functions.keys()):
                worksheet.write('{}1'.format(alphabet[col+1]), func)

                for row, value in enumerate(reduced_averages[func]):

                    worksheet.write('A{}'.format(row+2), row+1)
                    worksheet.write('{}{}'.format(alphabet[col+1], row+2), value)

            pigs = self._groups[group].pigs.keys()
            for row, pig in enumerate(pigs):
                worksheet.write('N{}'.format(row+2), pig)

        workbook.close()

        logging.info('Exported successfully groups statistics in {} file'.format(filename))

    def get_group(self, group):

        return self._groups.get(group, None)

    @ property
    def groups(self):
        """Getter for self._groups attribute. Returns the registered groups.

        Returns:
            dict: the registered groups
        """

        return self._groups

    def premortem_statistics(self, n_last_intervals, selected_property='APs', selected_groups=None):
        """
        """

        if selected_groups is None:
            selected_groups = list(self._groups.keys())
        else:
            all_groups = set(self._groups.keys())
            selected_groups = list(all_groups.intersection(selected_groups))

        progress_bar.reset(len(selected_groups))
        p_values = []
        for i, group in enumerate(selected_groups):
            p_value = self._groups[group].premortem_statistics(n_last_intervals, selected_property=selected_property)
            p_values.append(p_value)
            progress_bar.update(i+1)

        return dict(zip(selected_groups, p_values))

    def set_record_interval(self, interval):
        """Set the record interval.

        Args:
            interval (4-tuple): the record interval. 4-tuple of the form (start,end,record,offset).
        """

        for pool in self._groups.values():

            pool.set_record_interval(interval)


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
    groups.set_record_interval(('00:00:00', '01:00:00', 300, 30))
    print(groups.evaluate_global_group_effect('APs'))
    print(groups.evaluate_pairwise_group_effect('APs'))
    groups.export_statistics('test.xlsx', selected_property='APs')
