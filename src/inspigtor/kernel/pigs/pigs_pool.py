import collections
import logging

import numpy as np

import scipy.stats as stats
import scikit_posthocs as sk

from inspigtor.kernel.readers.picco2_reader import PiCCO2FileReader, PiCCO2FileReaderError
from inspigtor.kernel.utils.stats import statistical_functions


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
            averages_per_interval = self.get_statistics(selected_property, selected_statistics='mean', interval_indexes=interval_indexes)
        except PiCCO2FileReaderError as error:
            raise PigsPoolError('Error when getting pool statistics for {} property'.format(selected_property)) from error

        valid_intervals = []
        valid_averages_per_interval = []
        for i, averages in enumerate(averages_per_interval):
            if np.isnan(averages).any():
                continue
            valid_intervals.append(i)
            valid_averages_per_interval.append(averages)

        p_value = stats.friedmanchisquare(*valid_averages_per_interval).pvalue

        return valid_intervals, p_value

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
            averages_per_interval = self.get_statistics(selected_property, selected_statistics='mean', interval_indexes=interval_indexes)
        except PiCCO2FileReaderError as error:
            raise PigsPoolError('Error when getting pool statistics for {} property'.format(selected_property)) from error

        valid_intervals = []
        valid_averages_per_interval = []
        for i, averages in enumerate(averages_per_interval):
            if np.isnan(averages).any():
                continue
            valid_intervals.append(i)
            valid_averages_per_interval.append(averages)

        df = sk.posthoc_dunn(valid_averages_per_interval)
        df = df.round(4)

        p_values = df

        return valid_intervals, p_values

    def get_statistics(self, selected_property='APs', selected_statistics='mean', interval_indexes=None):
        """Returns a given statistics for a given property for each individual of the pool.

        Args:
            selected_property (str): the selected property
            statistics (str): the statistics to compute
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.
            reduce (list of str): the list statistical functions used to reduce the output over axis=1

        Returns:
            numpy.array: array which contain the sttaistics for each interval for each pig (row = number of intervals and columns = number of pigs)

        Raises:
            PigsPoolError: if the selected statistics is not valid.
        """

        n_pigs = len(self._pigs)
        max_n_intervals = 0
        all_statistics = []
        for reader in self._pigs.values():

            try:
                descriptive_statistics = reader.get_descriptive_statistics(selected_property, selected_statistics=[
                                                                           selected_statistics], interval_indexes=interval_indexes)
            except PiCCO2FileReaderError as error:
                logging.error(str(error))
                continue

            if selected_statistics not in descriptive_statistics:
                raise PigsPoolError('The statistics {} is unknown'.format(selected_statistics))

            # The selected statistics over record intervals for the current individual
            individual_statistics = descriptive_statistics[selected_statistics]

            all_statistics.append(individual_statistics)

            max_n_intervals = max(max_n_intervals, len(individual_statistics))

        if not all_statistics:
            raise PigsPoolError('No statistics computed for pool')

        output = np.full((max_n_intervals, n_pigs), np.nan, dtype=float)

        for i, s in enumerate(all_statistics):
            output[0:len(s), i] = s

        return output

    def reduced_statistics(self, selected_property='APs', selected_statistics='mean', interval_indexes=None, output_statistics=None):
        """Compute a set of statistics over the individuals.

        Args:
            selected_property (str): the selected property
            statistics (str): the statistics to compute
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.
            reduce (list of str): the list statistical functions used to reduce the output over axis=1

        Returns:
            numpy.array: array which contain the sttaistics for each interval for each pig (row = number of intervals and columns = number of pigs)

        Raises:
            PigsPoolError: if the selected statistics is not valid.
        """

        statistics = self.get_statistics(selected_property, selected_statistics, interval_indexes)

        available_statistics_functions = set(statistical_functions.keys())
        output_statistics = list(available_statistics_functions.intersection(output_statistics))

        if not output_statistics:
            raise PigsPoolError('No valid output statistics')

        reduced_statistics = {}
        for func in output_statistics:
            reduced_statistics[func] = statistical_functions[func](statistics, axis=1)

        if not reduced_statistics:
            raise PigsPoolError('Unknown reduce statistics')

        return reduced_statistics

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

            try:
                descriptive_statistics = reader.get_descriptive_statistics(selected_property, selected_statistics=['mean'], interval_indexes=interval_indexes)
            except PiCCO2FileReaderError as error:
                logging.error(str(error))
                continue

            averages.append(descriptive_statistics['mean'])

        # Transpose the nested list such as the number rows is the number of intervals and the number of columns the number of individuals
        averages = [list(x) for x in zip(*averages)]

        friedman_statistics = stats.friedmanchisquare(*averages).pvalue
        data_frame = sk.posthoc_dunn(averages)
        data_frame = data_frame.round(4)
        dunn_statistics = data_frame

        return interval_indexes, friedman_statistics, dunn_statistics

    def set_record_interval(self, interval):
        """Set the record interval.

        Args:
            interval (4-tuple): the record interval. 4-tuple of the form (start,end,record,offset).
        """

        for reader in self._pigs.values():

            reader.set_record_interval(interval)


if __name__ == '__main__':

    import sys
    pool = PigsPool()
    reader1 = PiCCO2FileReader(sys.argv[1])
    pool.add_reader(reader1)
    reader2 = PiCCO2FileReader(sys.argv[2])
    pool.add_reader(reader2)
    pool.set_record_interval(('00:00:00', '01:00:00', 300, 30))
    print(pool.get_statistics('APs'))
    print(pool.evaluate_global_time_effect('APs'))
    print(pool.evaluate_pairwise_time_effect('APs'))
    print(pool.premortem_statistics(6, 'APs'))
