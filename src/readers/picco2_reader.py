import collections
from datetime import datetime
import logging
import os
import sys

import numpy as np

import pandas as pd


class PiCCO2FileReader:
    """This class implements the PiCCO2 device reader.

    This is the base class of inspigtor application. It reads and parses a PiCCO2 file and computes statistics on 
    the properties stored in the file (columns). To be read properly, the file must contain a cell with the starting 
    time and ending time of the experiment. The T0 time will be used to define a T0 - 10 minutes time starting from 
    which records intervals will be computed. Those record intervals are those interval on which the average and std
    of a given property are computed. The Tfinal time will be used to compute pre-mortem statistics. 
    """

    def __init__(self, filename):

        if not os.path.exists(filename):
            raise IOError('The picco file {} does not exist'.format(filename))

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

        if 'T0' not in general_info_dict:
            raise IOError('Missing T0 value in the general parameters section.')

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
        t_minus_10_strptime = datetime.strptime(general_info_dict['T0'], self._time_fmt) - datetime.strptime('00:10:00', self._time_fmt)

        # If the t_zero - 10 is earlier than the beginning of the experiment set t_minus_10_strptime to the starting time of the experiment
        if t_minus_10_strptime.days < 0 or t_minus_10_strptime.seconds < 600:
            logging.warning(
                'T0 - 10 minutes is earlier than the beginning of the experiment for file {}. Will use its starting time instead.'.format(self._filename))
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
            raise IOError('Invalid value for T0 parameters')

        # Add a column to the original data which show the delta t regarding t_zero - 10 minutes
        self._data.insert(loc=2, column='delta_t', value=delta_ts)

        csv_file.close()

        self._record_intervals = []

        # This dictionary will cache the statistics computed for selected properties to save some time
        self.reset_statistics_cache()

    def get_averages(self, selected_property='APs'):
        """Compute the statistics for a given property for the current record intervals.

        For each record interval, computes the average and the standard deviation of the selected property and its coverage.

        Args:
            selected_property (str): the selected property

        Returns:
            dict: a dictionary which stores the computed statistics.
        """

        # If the selected property is cached, just return its current value
        if selected_property in self._statistics:
            return self._statistics[selected_property]

        # Some record intervals must have been set before
        if not self._record_intervals:
            logging.warning('No record intervals defined yet')
            return {}

        self._statistics[selected_property] = []

        # Compute for each record interval the average and standard deviation of the selected property
        for i, interval in enumerate(self._record_intervals):
            first_index, last_index = interval
            values = []
            for j in range(first_index, last_index):
                try:
                    values.append(float(self._data[selected_property].iloc[j]))
                except ValueError:
                    continue
            if not values:
                logging.warning('No values to compute statistics for interval {:d} of file {}'.format(i+1, self._filename))
            else:
                self._statistics[selected_property].append((i, np.average(values), np.std(values)))

        return self._statistics[selected_property]

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

        n_times = len(self._data['Time'])

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
            for t_index in range(self._t_minus_10_index, n_times):
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

            first = True
            starting_index = first_record_index
            for t_index in range(first_record_index, last_record_index):
                t0 = datetime.strptime(self._data['Time'].iloc[starting_index], self._time_fmt)
                t1 = datetime.strptime(self._data['Time'].iloc[t_index], self._time_fmt)
                delta_t = (t1 - t0).seconds

                # Case of a time within the offset, skip.
                if delta_t < offset:
                    continue
                # Case of a time within the record interval, save the first time of the record interval
                elif (delta_t >= offset) and (delta_t < offset + record):
                    if first:
                        first_record_index = t_index
                        first = False

                    continue
                # A new offset-record interval is started
                else:
                    self._record_intervals.append((first_record_index, t_index))
                    starting_index = t_index
                    first = True

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

    def write_summary(self, selected_property='APs'):
        """Write the summay about the statistics for a selected property

        Args:
            selected_property (str): the selected property for which the summary will be written.
        """

        # The selected property must be in the cache
        if not selected_property in self._statistics:
            logging.warning('Statistics for property {} has not yet been computed.'.format(selected_property))
            return

        summary_file_dirname = os.path.dirname(self._filename)
        summary_file_basename = os.path.splitext(os.path.basename(self._filename))[0]
        summary_file = os.path.join(summary_file_dirname, '{}_summary_{}.txt'.format(summary_file_basename, selected_property))

        averages = [np.nan if v is None else v for v in self._statistics[selected_property]['averages']]
        stds = [np.nan if v is None else v for v in self._statistics[selected_property]['stds']]

        n_intervals = len(averages)

        with open(summary_file, 'w') as fout:
            fout.write('interval;average;std')
            fout.write('\n')
            for i in range(n_intervals):
                fout.write('{:d};{:f};{:f}\n'.format(i+1, averages[i], stds[i]))


if __name__ == '__main__':

    reader = PiCCO2FileReader(sys.argv[1])
    reader.set_record_intervals([('00:00:00', '01:00:00', 300, 60)])
    print(reader.record_intervals)
