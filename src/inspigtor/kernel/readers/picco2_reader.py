import collections
from datetime import datetime
import logging
import os
import sys

import numpy as np

import scipy.stats as stats

import xlsxwriter

import pandas as pd


class PiCCO2FileReaderError(Exception):
    """Exception for PiCCO2 file reader.
    """


class PiCCO2FileReader:
    """This class implements the PiCCO2 device reader.

    This is the base class of inspigtor application. It reads and parses a PiCCO2 file and computes statistics on
    the properties stored in the file (columns). To be read properly, the file must contain a cell with the starting
    time and ending time of the experiment. The Tinitial time will be used to define a Tinitial - 10 minutes time starting from
    which records intervals will be computed. Those record intervals are those interval on which the average and std
    of a given property are computed. The Tfinal time will be used to compute pre-mortem statistics.
    """

    def __init__(self, filename):
        """Constructor

        Args:
            filename (str): the PiCCO2 input file
        """

        if not os.path.exists(filename):
            raise PiCCO2FileReaderError('The picco file {} does not exist'.format(filename))

        self._filename = filename

        csv_file = open(self._filename, 'r')

        # Skip the first line, just comments about the device
        csv_file.readline()

        # Read the second line which contains the titles of the general parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        general_info_fields = [v.strip() for v in line.split(';') if v.strip()]

        # Read the third line which contains the values of the general parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        general_info = [v.strip() for v in line.split(';') if v.strip()]

        # Create a dict out of those parameters
        general_info_dict = collections.OrderedDict(zip(general_info_fields, general_info))

        if 'Tinitial' not in general_info_dict:
            raise PiCCO2FileReaderError('Missing Tinitial value in the general parameters section.')

        if 'Tfinal' not in general_info_dict:
            raise PiCCO2FileReaderError('Missing Tfinal value in the general parameters section.')

        # Read the fourth line which contains the titles of the pig id parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        pig_id_fields = [v.strip() for v in line.split(';') if v.strip()]

        # Read the fifth line which contains the values of the pig id parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        pig_id = [v.strip() for v in line.split(';') if v.strip()]

        # Create a dict outof those parameters
        pig_id_dict = collections.OrderedDict(zip(pig_id_fields, pig_id))

        # Concatenate the pig id parameters dict and the general parameters dict
        self._parameters = {**pig_id_dict, **general_info_dict}

        # Read the rest of the file as a csv file
        self._data = pd.read_csv(self._filename, sep=';', skiprows=7, skipfooter=1, engine='python')

        # For some files, times are not written in chronological order, so sort them before doing anything
        self._data = self._data.sort_values(by=['Time'])

        self._time_fmt = '%H:%M:%S'
        self._exp_start = datetime.strptime(self._data.iloc[0]['Time'], self._time_fmt)

        # The evaluation of intervals starts at t_zero - 10 minutes (as asked by experimentalists)
        t_minus_10_strptime = datetime.strptime(general_info_dict['Tinitial'], self._time_fmt) - datetime.strptime('00:10:00', self._time_fmt)

        # If the t_zero - 10 is earlier than the beginning of the experiment set t_minus_10_strptime to the starting time of the experiment
        if t_minus_10_strptime.days < 0 or t_minus_10_strptime.seconds < 600:
            logging.warning(
                'Tinitial - 10 minutes is earlier than the beginning of the experiment for file {}. Will use its starting time instead.'.format(self._filename))
            t_minus_10_strptime = self._exp_start
        else:
            t_minus_10_strptime = datetime.strptime(str(t_minus_10_strptime), self._time_fmt)

        self._t_minus_10_index = 0

        valid_t_minus_10 = False
        delta_ts = []
        first = True
        for i, time in enumerate(self._data['Time']):
            delta_t = datetime.strptime(time, self._time_fmt) - t_minus_10_strptime
            # If the difference between the current time and t_zero - 10 is positive for the first time, then record the corresponding
            # index as being the reference time
            if delta_t.days >= 0:
                delta_ts.append(str(delta_t))
                if first:
                    self._t_minus_10_index = i
                    valid_t_minus_10 = True
                    first = False
            else:
                delta_ts.append('-'+str(-delta_t))

        if not valid_t_minus_10:
            raise PiCCO2FileReaderError('Invalid value for Tinitial parameters')

        # Add a column to the original data which show the delta t regarding t_zero - 10 minutes
        self._data.insert(loc=2, column='delta_t', value=delta_ts)

        csv_file.close()

        self._record_intervals = []

        # This dictionary will cache the statistics computed for selected properties to save some time
        self.reset_statistics_cache()

    @ property
    def data(self):
        """Property for the data stored in the csv file

        Returns:
            pandas.DataFrame: the data stored in the csv file.
        """

        return self._data

    @ property
    def filename(self):
        """Property for the reader's filename.

        Returns:
            str: the reader's filename.
        """

        return self._filename

    def get_descriptive_statistics(self, selected_property='APs', interval_indexes=None):
        """Compute the statistics for a given property for the current record intervals.

        For each record interval, computes the average and the standard deviation of the selected property.

        Args:
            selected_property (str): the selected property
            interval_indexes (list of int): the indexes of the record intervals to select. If None, all the record intervals will be used.

        Returns:
            dict: a dictionary whose keys are the different statistics computed (e;g; average, median ...) and the values are the list of 
            the value of the statistics over record intervals
        """

        if selected_property not in list(self._data.columns):
            raise PiCCO2FileReaderError('Property {} is unknown'.format(selected_property))

            # If the selected property is cached, just return its current value
        if selected_property in self._statistics:
            return self._statistics[selected_property]

        # Some record intervals must have been set before
        if not self._record_intervals:
            raise PiCCO2FileReaderError('No record intervals defined yet')

        if interval_indexes is None:
            interval_indexes = range(len(self._record_intervals))

        self._statistics[selected_property] = {}

        # Compute for each record interval the average and standard deviation of the selected property
        for index in interval_indexes:
            interval = self._record_intervals[index]
            first_index, last_index = interval
            data = []
            for j in range(first_index, last_index):
                try:
                    data.append(float(self._data[selected_property].iloc[j]))
                except ValueError:
                    continue
            if not data:
                raise PiCCO2FileReaderError('The interval {:d} of file {} does not contain any number'.format(index+1, self._filename))
            else:
                self._statistics[selected_property].setdefault('intervals', []).append(index+1)
                self._statistics[selected_property].setdefault('data', []).append(data)
                self._statistics[selected_property].setdefault('averages', []).append(np.average(data))
                self._statistics[selected_property].setdefault('stddevs', []).append(np.std(data))
                self._statistics[selected_property].setdefault('medians', []).append(np.median(data))
                self._statistics[selected_property].setdefault('1st quantiles', []).append(np.quantile(data, 0.25))
                self._statistics[selected_property].setdefault('3rd quantiles', []).append(np.quantile(data, 0.75))
                self._statistics[selected_property].setdefault('skewnesses', []).append(stats.skew(data))
                self._statistics[selected_property].setdefault('kurtosis', []).append(stats.kurtosis(data))

        return self._statistics[selected_property]

    def get_coverages(self, selected_property='APs'):
        """Compute the coverages for a given property.

        The coverage of a property is the ratio between the number of valid values over the total number of values for a given property over a given record interval.

        Args:
            selected_property (str): the selected properrty for which the coverages will be calculated.

        Returns:
            list of float: the coverages for each record interval
        """

        if not self._record_intervals:
            logging.warning('No record intervals defined yet')
            return []

        coverages = []
        # Compute for each record interval the average and standard deviation of the selected property
        for interval in self._record_intervals:
            first_index, last_index = interval
            coverage = 0.0
            for j in range(first_index, last_index):
                # If the value can be casted to a float, the value is considered to be valid
                try:
                    _ = float(self._data[selected_property].iloc[j])
                except ValueError:
                    continue
                else:
                    coverage += 1.0
            coverages.append(100.0*coverage/(last_index-first_index))

        return coverages

    def get_t_final_index(self):
        """Return the first index whose time is superior to Tfinal.
        """

        for index, time in enumerate(self._data['Time']):
            delta_t = datetime.strptime(self._parameters['Tfinal'], self._time_fmt) - datetime.strptime(time, self._time_fmt)
            if delta_t.days < 0:
                return index

        return len(self._data['Time'])

    def reset_statistics_cache(self):
        """Reset the statistics cache.
        """

        self._statistics = {}

    def set_record_intervals(self, intervals):
        """Set the record intervals.

        Args:
            intervals (list of 4-tuples): the record time in seconds. List of 4-tuples of the form (start,end,record,offset).
        """

        # Clear the statistics cache
        self.reset_statistics_cache()

        t_max = self.get_t_final_index()

        t_minus_10 = datetime.strptime(self._data['Time'].iloc[self._t_minus_10_index], self._time_fmt)

        self._record_intervals = []

        # Loop over each interval
        for interval in intervals:
            start, end, record, offset = interval
            # Convert strptime to timedelta for further use
            start = (datetime.strptime(start, self._time_fmt) - datetime.strptime('00:00:00', self._time_fmt)).seconds
            end = (datetime.strptime(end, self._time_fmt) - datetime.strptime('00:00:00', self._time_fmt)).seconds

            enter_interval = True
            exit_interval = True
            last_record_index = None
            # Loop over the times [t0-10,end] for defining the first and last indexes (included) that falls in the running interval
            for t_index in range(self._t_minus_10_index, t_max):
                delta_t = (datetime.strptime(self._data['Time'].iloc[t_index], self._time_fmt) - t_minus_10).seconds
                # We have not entered yet in the interval, skip.
                if delta_t < start:
                    continue
                # We entered in the interval.
                else:
                    # We are in the interval
                    if delta_t < end:
                        # First time we entered in the interval, record the corresponding index
                        if enter_interval:
                            first_record_index = t_index
                            enter_interval = False
                    # We left the interval
                    else:
                        # First time we left the interval, record the corresponding index
                        if exit_interval:
                            last_record_index = t_index
                            exit_interval = False

            # If the last index could not be defined, set it to the last index of the data
            if last_record_index is None:
                last_record_index = len(self._data.index)

            starting_index = first_record_index
            delta_ts = []
            for t_index in range(first_record_index, last_record_index):
                t0 = datetime.strptime(self._data['Time'].iloc[starting_index], self._time_fmt)
                t1 = datetime.strptime(self._data['Time'].iloc[t_index], self._time_fmt)
                delta_t = (t1 - t0).seconds
                delta_ts.append((t_index, delta_t))

                if delta_t > record + offset:
                    for r_index, delta_t in delta_ts:
                        if delta_t > record:
                            self._record_intervals.append((starting_index, r_index))
                            break
                    starting_index = t_index
                    delta_ts = []

    @ property
    def parameters(self):
        """Returns the global parameters for the pig.

        This is the first data block stored in the csv file.

        Returns:
            collections.OrderedDict: the pig's parameters.
        """

        return self._parameters

    @property
    def record_intervals(self):
        """Return the current record intervals (if any).

        Returns:
            list of 2-tuples: the record inervals.
        """

        return self._record_intervals

    @property
    def record_times(self):
        """Return the starting and ending times of each record interval

        Returns:
            list of 2-tuples: the list of starting and ending time for each record interval
        """

        record_times = [(self._data['Time'].iloc[start], self._data['Time'].iloc[end-1]) for start, end in self._record_intervals]

        return record_times

    def t_interval_index(self, time):
        """Returns the index of the interval which contains a given time.

        Returns:
            int: the index
        """

        record_times = self.record_times

        for index, (_, ending) in enumerate(record_times):
            delta_t = datetime.strptime(time, self._time_fmt) - datetime.strptime(ending, self._time_fmt)
            if delta_t.days < 0:
                return index

        return -1

    @property
    def t_final_interval_index(self):
        """Returns the index of the interval which contains Tfinal.

        Returns:
            int: the index
        """

        return self.t_interval_index(self._parameters['Tfinal'])

    @property
    def t_initial_interval_index(self):
        """Returns the index of the interval which contains Tinitial.

        Returns:
            int: the index
        """

        return self.t_interval_index(self._parameters['Tinitial'])

    def write_summary(self, filename, selected_property='APs'):
        """Write the summay about the statistics for a selected property to an excel file.

        Args:
            filename (str): the excel filename
            selected_property (str): the selected property for which the summary will be written.
        """

        stats = self._statistics.get(selected_property, self.get_descriptive_statistics(selected_property))
        if not stats:
            return

        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet(os.path.basename(self._filename) if len(self._filename) <= 31 else 'pig')
        worksheet.write('K1', 'Selected property')
        worksheet.write('K2', selected_property)
        worksheet.write('A1', 'Interval')
        worksheet.write('B1', 'Average')
        worksheet.write('C1', 'Std Dev')
        worksheet.write('D1', 'Median')
        worksheet.write('E1', '1st quartile')
        worksheet.write('F1', '3rd quartile')
        worksheet.write('G1', 'Skewness')
        worksheet.write('H1', 'kurtosis')

        for i, interval in enumerate(stats['intervals']):

            worksheet.write('A{}'.format(i+2), interval)
            worksheet.write('B{}'.format(i+2), stats['averages'][i])
            worksheet.write('C{}'.format(i+2), stats['stddevs'][i])
            worksheet.write('D{}'.format(i+2), stats['medians'][i])
            worksheet.write('E{}'.format(i+2), stats['1st quantiles'][i])
            worksheet.write('F{}'.format(i+2), stats['3rd quantiles'][i])
            worksheet.write('G{}'.format(i+2), stats['skewnesses'][i])
            worksheet.write('H{}'.format(i+2), stats['kurtosis'][i])

        workbook.close()


if __name__ == '__main__':

    reader = PiCCO2FileReader(sys.argv[1])
    reader.set_record_intervals([('00:00:00', '10:00:00', 120, 30)])
    print(reader.record_intervals)
    print(reader.record_times)
    print(reader.t_initial_interval_index)
    print(reader.get_t_final_index())
    print(reader.get_descriptive_statistics(interval_indexes=[1, 2]))
