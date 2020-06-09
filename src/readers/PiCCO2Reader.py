import collections
import csv
import os
import sys

import pandas as pd

class PiCCO2FileReader:

    def __init__(self, filename):

        if not os.path.exists(filename):
            raise IOError('The picco file {} does not exist'.format(filename))

        self._filename = filename

        csv_file = open(self._filename,'r')

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
        general_info_dict = collections.OrderedDict(zip(general_info_fields,general_info))

        # Read the fourth line which contains the titles of the pig id parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        pig_id_fields = line.split(';')

        # Read the fifth line which contains the values of the pig id parameters
        line = csv_file.readline().strip()
        line = line[:-1] if line.endswith(';') else line
        pig_id = line.split(';')

        # Create a dict outof those parameters
        pig_id_dict = collections.OrderedDict(zip(pig_id_fields,pig_id))

        # Concatenate the pig id parameters dict and the general parameters dict
        self._parameters = {**pig_id_dict,**general_info_dict}

        self._data = pd.read_csv(self._filename,sep=';', skiprows=7, skipfooter=1)
        self._data['Date'] = pd.to_datetime(self._data['Date'], format='%d.%m.%Y')
        self._data['Time'] = pd.to_datetime(self._data['Time'], format='%H:%M:%S')

        csv_file.close()

    @property
    def data(self):
        return self._data

    @property
    def filename(self):
        return self._filename

    @property
    def parameters(self):
        return self._parameters



if __name__ == '__main__':

    reader = PiCCO2FileReader(sys.argv[1])
    print(reader.data)
    print(reader.parameters)
