import collections
import csv
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

        self._time_fmt = '%H:%M:%S'
        self._exp_start = self._data.iloc[0]['Time']

        # self._data['Date'] = pd.to_datetime(self._data['Date'], format='%d.%m.%Y')
        # self._data['Time'] = pd.to_datetime(self._data['Time'], format='%H:%M:%S')

        csv_file.close()

        self._first_valid_row = 0
        self._last_valid_row = self._first_valid_row

    def __next__(self):
        """Returns the next valid interval in the reader.

        A valid interval is an interval wwhere the parameter APs is a float.
        """

        # Loop first to check the first valid row (if any)
        while True:
            if self._first_valid_row >= len(self._data.index):
                raise StopIteration

            row = self._data.iloc[self._first_valid_row]
            try:
                _ = float(row['APs'])
                break

            except ValueError:
                self._first_valid_row += 1

        self._last_valid_row = self._first_valid_row

        while True:
            if self._last_valid_row >= len(self._data.index):
                raise StopIteration
            row = self._data.iloc[self._last_valid_row]
            try:
                _ = float(row['APs'])
                self._last_valid_row += 1

            except ValueError:
                break

        interval = (self._first_valid_row, self._last_valid_row)

        self._first_valid_row = self._last_valid_row

        return interval

    def __iter__(self):

        self._first_valid_row = 0
        self._last_valid_row = self._first_valid_row

        return self

    @ property
    def data(self):
        return self._data

    @ property
    def filename(self):
        return self._filename

    @ property
    def parameters(self):
        return self._parameters

    def interval_statistics(self, t_zero, t_offset, duration, property):

        intervals = [interval for interval in self]

        if not intervals:
            return []

        stat = []
        for interval in intervals:
            first_index, last_index = interval
            first_time = self._data.iloc[first_index]['Time']
            delta_t = datetime.strptime(self._exp_start, self._time_fmt) - \
                datetime.strptime(first_time, self._time_fmt)
            if delta_t.seconds < t_zero:
                stat.append((interval, None))

        return stat


if __name__ == '__main__':

    reader = PiCCO2FileReader(sys.argv[1])
    print(reader.interval_statistics(120, 10, 20, 'APs'))
