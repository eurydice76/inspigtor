import collections
import csv
import logging
import os
import sys

from datetime import datetime

import pandas as pd


class PiCCO2FileReader:

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
        general_info_fields = line.split(';')

        # Read the third line which contains the values of the general parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        general_info = line.split(';')

        # Create a dict outof those parameters
        general_info_dict = collections.OrderedDict(zip(general_info_fields, general_info))

        if 'T0' not in general_info_dict:
            raise IOError('Missing T0 value in the general parameters section.')

        # Read the fourth line which contains the titles of the pig id parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        pig_id_fields = line.split(';')

        # Read the fifth line which contains the values of the pig id parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        pig_id = line.split(';')

        # Create a dict outof those parameters
        pig_id_dict = collections.OrderedDict(zip(pig_id_fields, pig_id))

        # Concatenate the pig id parameters dict and the general parameters dict
        self._parameters = {**pig_id_dict, **general_info_dict}

        self._data = pd.read_csv(self._filename, sep=';', skiprows=7, skipfooter=1, engine='python')

        # Some times are not placed in chronological order in the csv file, so sort them before doing anything
        self._data = self._data.sort_values(by=['Time'])

        self._time_fmt = '%H:%M:%S'
        self._exp_start = datetime.strptime(self._data.iloc[0]['Time'], self._time_fmt)

        # The evaluation of intervals starts at t0 - 10 minutes (as asked by experimentalist)
        t_minus_10_strptime = datetime.strptime(general_info_dict['T0'], self._time_fmt) - self._exp_start
        # If the t0 - 10 is earlier than the beginning of the experiment set t_minus_10_strptime to be the starting time of the experiment
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
        for i, t in enumerate(self._data['Time']):
            delta_t = datetime.strptime(t, self._time_fmt) - t_minus_10_strptime
            # If the difference between the current time and t0 - 10 is positive for the first time, then record the corresponding
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

        # Add a column to the original data which show the delta t regarding t0 - 10 minutes
        self._data.insert(loc=2, column='delta_t', value=delta_ts)

        csv_file.close()

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

    def get_record_intervals(self, intervals):
        """Computes and returns the record intervals found in the csv data.

        Args:
            t_record (int): the record time in seconds
            t_offset (int): the offset time in seconds

        Returns:
            list: the list of the record intervals found in the csv data.
        """

        n_times = len(self._data['Time'])

        t0 = datetime.strptime(self._data['Time'].iloc[self._t_minus_10_index], self._time_fmt)

        record_intervals = []

        for interval in intervals:
            start, end, record, offset = interval
            start = (datetime.strptime(start, self._time_fmt) - datetime.strptime('00:00:00', self._time_fmt)).seconds
            end = (datetime.strptime(end, self._time_fmt) - datetime.strptime('00:00:00', self._time_fmt)).seconds

            enter_interval = True
            exit_interval = True
            last_record_index = None
            for t_index in range(self._t_minus_10_index, n_times):
                delta_t = (datetime.strptime(self._data['Time'].iloc[t_index], self._time_fmt) - t0).seconds
                if delta_t < start:
                    continue
                else:
                    if delta_t < end:
                        if enter_interval:
                            first_record_index = t_index
                            enter_interval = False
                    else:
                        if exit_interval:
                            last_record_index = t_index
                            exit_interval = False

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
                    record_intervals.append((first_record_index, t_index))
                    starting_index = t_index
                    first = True

        return record_intervals

    @ property
    def parameters(self):
        """Property for the pig's overall parameters.

        This is the first data block stored in the csv file.

        Returns:
            collections.OrderedDict: the pig's parameters.
        """

        return self._parameters


if __name__ == '__main__':

    reader = PiCCO2FileReader(sys.argv[1])
    print(reader.get_record_intervals([('00:00:00', '01:00:00', 300, 60)]))
