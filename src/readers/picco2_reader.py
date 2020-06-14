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
        self._data = self._data.sort_values(by=['Time'])

        self._time_fmt = '%H:%M:%S'
        self._exp_start = datetime.strptime(self._data.iloc[0]['Time'], self._time_fmt)

        csv_file.close()

        self._first_valid_row = 0
        self._last_valid_row = self._first_valid_row

    def get_valid_intervals(self, selected_property='APs', t_merge=0):
        """Returns the list of valid intervals.

        A valid interval is an interval wwhere a given property has a value which can 
        be casted to a float.

        Args:
            selected_property (str): the property used to check for valid row
            t_merge (int): the time (in seconds) used to merge valid inervals

        Returns:
            list: the list of valid intervals
        """

        row_index = 0

        # Loop first to check the first valid row (if any)
        while True:

            if row_index >= len(self._data.index):
                break

            row = self._data.iloc[row_index]

            try:
                # The row is valid
                _ = float(row[selected_property])
            except ValueError:
                pass
            else:
                first_valid_row = row_index
                while True:
                    if row_index >= len(self._data.index):
                        valid_intervals.append((first_valid_row,row_index))
                        break

                    row = self._data.iloc[row_index]

                    try:
                        # The row is valid
                        _ = float(row[selected_property])
                    except ValueError:
                        valid_intervals.append((first_valid_row,row_index))
                        break
                    else:
                        row_index +=1
            finally:
                row_index += 1

        if t_merge > 0:
            to_merge = []
            # Second pass, merge the intervals whose gap is smaller than t_merge
            for i in range(len(valid_intervals)-1):
                _,last_index =  valid_intervals[i]
                first_index, _ =  valid_intervals[i+1]
                t0 = datetime.strptime(self._data['Time'].iloc[last_index-1],self._time_fmt)
                t1 = datetime.strptime(self._data['Time'].iloc[first_index],self._time_fmt)
                if (t1-t0).seconds < t_merge:
                    to_merge.append(i)
            to_merge.reverse()

            for i in merge:
                current_interval = valid_intervals[i]
                interval_to_merge = valid_intervals.pop(i+1)
                valid_intervals[i] = (current_interval[0],interval_to_merge[1])

        return valid_intervals

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

    def get_record_intervals(self, t_record, t_offset=0, t_merge=0):
        """Computes and returns the record intervals found in the csv data. For each valid interval (i.e. intervals for which APs 
        property is a valid number), the time is splitted on the following way [offset_1,record_1,offset_2,record_2 ...].
        The records intervals are returned as a  nested list of the first and last indexes of each record interval found.

        Args:
            t_offset (int): the offset time in seconds
            t_offset (int): the record time in seconds

        Returns:
            list: the list of the record intervals found in the csv data.
        """

        intervals = [interval for interval in self]
        if not intervals:
            return []

        stats_per_interval = []
        # Loop over the valid intervals
        for interval in intervals:
            first_index, last_index = interval

            starting_index = first_index
            index = starting_index
            first = True
            first_record_index = None
            while True:
                if index == last_index:
                    break
                t0 = datetime.strptime(self._data.iloc[starting_index]['Time'], self._time_fmt)
                t1 = datetime.strptime(self._data.iloc[index]['Time'], self._time_fmt)
                delta_t = (t1 - t0).seconds

                # Case of a time within the offset, skip.
                if delta_t < t_offset:
                    index += 1
                # Case of a time within the record interval, save the first time of the record interval
                elif (delta_t >= t_offset) and (delta_t < t_offset + t_record):
                    if first:
                        first_record_index = index
                        first = False
                    index += 1
                # A new offset-record interval is started
                else:
                    stats_per_interval.append((first_record_index, index))
                    starting_index = index

        return stats_per_interval

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
    print(reader.get_record_intervals(300, 60))
