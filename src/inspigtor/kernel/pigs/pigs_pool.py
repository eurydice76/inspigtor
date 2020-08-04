import collections
import logging
import os

import numpy as np

import scipy.stats as stats
import scikit_posthocs as sk

from inspigtor.kernel.readers.picco2_reader import PiCCO2FileReader, PiCCO2FileReaderError


class PigsPoolError(Exception):
    pass


class PigsPool:
    """This class implements a pool of pigs. Each pigs in the pool is identified by its corresponding csv filename.
    """

    def __init__(self):
        """Constructor
        """

        self._pigs = collections.OrderedDict()

    def __len__(self):

        return len(self._pigs)

    def add_reader(self, reader):
        """Add a reader to the pool.

        Args:
            reader (inspigtor.kernel.readers.picco2_reader.PiCCO2FileReader): the reader
        """

        if reader.filename in self._pigs:
            logging.warning('The reader has already been registered')
            return

        self._pigs[reader.filename] = reader

    def remove_reader(self, filename):

        if filename in self._pigs:
            del self._pigs[filename]

    def get_reader(self, filename):

        return self._pigs.get(filename, None)

    def evaluate_global_time_effect(self, selected_property='APs', interval_indexes=None):
        """Performs a Friedman statistical test to check whether the averages defined for each pig over record intervals 
        belongs to the same distribution.

        Args:
            selected_property (str): the selected property
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.

        Returns:
            float: the p value from the Friedman test
        """

        try:
            averages = self.get_statistics(selected_property, selected_statistics='averages', interval_indexes=interval_indexes)
        except PiCCO2FileReaderError as error:
            raise PigsPoolError('Error when getting pool statistics for {} property'.format(selected_property)) from error

        p_value = stats.friedmanchisquare(*averages).pvalue

        return p_value

    def evaluate_pairwise_time_effect(self, selected_property='APs', interval_indexes=None):
        """Performs a Dunn statistical test to check whether the averages defined for each pig over record intervals belongs
        to the same distribution pairwisely.

        Args:
            selected_property (str): the selected property
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.

        Returns:
            pandas.DataFrame: the p values matrix resulting from Dunn test
        """

        try:
            averages = self.get_statistics(selected_property, selected_statistics='averages', interval_indexes=interval_indexes)
        except PiCCO2FileReaderError as error:
            raise PigsPoolError('Error when getting pool statistics for {} property'.format(selected_property)) from error

        df = sk.posthoc_dunn(averages)
        df = df.round(4)

        p_values = df

        return p_values

    def get_averages_per_interval(self, selected_property='APs', interval_indexes=None):
        """Get the averages and standard deviations of the pool for each interval.

        Args:
            selected_property (str): the selected property
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.
        """

        try:
            all_individual_averages = self.get_statistics(selected_property, selected_statistics='averages', interval_indexes=interval_indexes)
        except PiCCO2FileReaderError as error:
            raise PigsPoolError('Error when getting statistics for {} property'.format(selected_property)) from error

        all_individual_averages = np.array(all_individual_averages)

        averages = np.average(all_individual_averages, axis=1)
        stds = np.std(all_individual_averages, axis=1)

        return averages, stds

    def get_statistics(self, selected_property='APs', selected_statistics='averages', interval_indexes=None):
        """Returns the averages of a given property for each individual of the pool.

        Args:
            selected_property (str): the selected property
            statistics (str): the statistics to compute
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.
        """

        all_individual_averages = []
        previous_intervals = None
        for reader in self._pigs.values():

            try:
                individual_averages = reader.get_descriptive_statistics(selected_property, interval_indexes)
            except PiCCO2FileReaderError as error:
                raise PigsPoolError('Error when computing descriptive statistics for property {} of {} file'.format(
                    selected_property, reader.filename)) from error

            intervals = individual_averages['intervals']

            if selected_statistics not in individual_averages:
                raise PigsPoolError('The statistics {} is unknown'.format(selected_statistics))

            statistics = individual_averages[selected_statistics]

            all_individual_averages.append(statistics)
            if previous_intervals is not None and intervals != previous_intervals:
                raise PigsPoolError('Individuals do not have matching intervals.')

            previous_intervals = intervals

        # Transpose the nested list such as the number of rows is the number of intervals and the number of columns the number of pigs
        all_individual_averages = [list(x) for x in zip(*all_individual_averages)]

        return all_individual_averages

    @property
    def pigs(self):
        """Getter for self._pigs attribute.

        Returns:
            dict: the pigs registered in the pool
        """

        return self._pigs

    def premortem_statistics(self, n_last_intervals, selected_property='APs'):
        """Compute the premortem statistics to assess putative time effect between the last interval before 
        intoxication and the n last intervals.

        This is basically the same procedure than for the global and pairwise time effect analysis
        excepted that only the interval before Tinitial and the n last intervals are considered.
        This allows pigs with different intervals due to different time of death to be compared through
        a statistical test.

        Args:
            n_last_intervals (int): the number of last intervals to consider
            selected_property (str): the selected property

        Returns:
            2-tuple: the results of the Friedman test (float) and Dunn test (pandas.DataFrame)
        """

        friedman_statistics = {}
        dunn_statistics = {}

        averages = []

        for reader in self.pigs.values():

            t_initial_interval_index = reader.t_initial_interval_index
            t_final_interval_index = reader.t_final_interval_index

            # These are the intervals used for the analysis
            interval_indexes = [t_initial_interval_index - 1] + list(range(t_final_interval_index-n_last_intervals+1, t_final_interval_index+1))

            descriptive_statistics = reader.get_descriptive_statistics(selected_property, interval_indexes=interval_indexes)

            averages.append(descriptive_statistics['averages'])

        # Transpose the nested list such as the number rows is the number of intervals and the number of columns the number of individuals
        averages = [list(x) for x in zip(*averages)]

        friedman_statistics = stats.friedmanchisquare(*averages).pvalue
        data_frame = sk.posthoc_dunn(averages)
        data_frame = data_frame.round(4)
        dunn_statistics = data_frame

        return friedman_statistics, dunn_statistics

    def set_record_intervals(self, intervals):
        """Set the record intervals.

        Args:
            intervals (list of 4-tuples): the record time in seconds. List of 4-tuples of the form (start,end,record,offset).
        """

        for reader in self._pigs.values():

            reader.set_record_intervals(intervals)


if __name__ == '__main__':

    import sys
    pool = PigsPool()
    reader1 = PiCCO2FileReader(sys.argv[1])
    pool.add_reader(reader1)
    reader2 = PiCCO2FileReader(sys.argv[2])
    pool.add_reader(reader2)
    pool.set_record_intervals([('00:00:00', '01:00:00', 300, 30)])
    print(pool.get_statistics('APs'))
    print(pool.get_averages_per_interval('APs'))
    print(pool.evaluate_global_time_effect('APs'))
    print(pool.evaluate_pairwise_time_effect('APs'))
    print(pool.premortem_statistics(6, 'APs'))
