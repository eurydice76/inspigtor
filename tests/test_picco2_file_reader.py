import math
import os

from inspigtor.readers.picco2_reader import PiCCO2FileReader

tolerance = 1.0e-6


class TestPicco2FileReader:

    def setup(self):

        tests_dir = os.path.dirname(__file__)
        self._filename = os.path.join(tests_dir, 'pig1.csv')
        self._filename1 = os.path.join(tests_dir, 'pig2.csv')

    def test___init___(self):

        reader = PiCCO2FileReader(self._filename)
        assert(reader.filename == self._filename)

        parameters = reader.parameters
        assert(parameters['Weight'] == '28')
        assert(parameters['Height'] == '130')
        assert(parameters['Gender'] == 'Male')
        assert(parameters['category'] == 'Adult')
        assert(parameters['TD cath'] == 'PV2014L16F')
        assert(parameters['BSA'] == '1.01')
        assert(parameters['PBW'] == '30')
        assert(parameters['PBSA'] == '1.03')

        data = reader.data
        assert(data['Time'][7] == '09:39:05')
        assert(math.isclose(float(data['PCCO'].iloc[9]), 3.51, abs_tol=tolerance))

    def test_set_valid_intervals(self):

        reader = PiCCO2FileReader(self._filename)
        reader.set_valid_intervals(selected_property='APs')
        valid_intervals = reader.valid_intervals

        assert(valid_intervals[0] == (0, 40))
        assert(valid_intervals[1] == (50, 111))
        assert(valid_intervals[2] == (112, 122))

        reader = PiCCO2FileReader(self._filename1)
        reader.set_valid_intervals(selected_property='APs')
        valid_intervals = reader.valid_intervals

        assert(valid_intervals[0] == (1, 17))
        assert(valid_intervals[1] == (23, 33))
        assert(valid_intervals[2] == (34, 41))

    def test_get_record_intervals(self):

        reader = PiCCO2FileReader(self._filename)
        reader.set_valid_intervals(selected_property='APs')
        record_intervals = reader.get_record_intervals(t_record=120)

        assert(record_intervals[0] == (0, 12))
        assert(record_intervals[1] == (12, 22))
        assert(record_intervals[2] == (22, 32))
        assert(record_intervals[3] == (50, 60))
        assert(record_intervals[4] == (60, 70))
        assert(record_intervals[5] == (70, 80))
        assert(record_intervals[6] == (80, 90))
        assert(record_intervals[7] == (90, 100))
        assert(record_intervals[8] == (100, 110))

        record_intervals = reader.get_record_intervals(t_record=120, t_merge=30)
        assert(record_intervals[0] == (0, 12))
        assert(record_intervals[1] == (12, 22))
        assert(record_intervals[2] == (22, 32))
        assert(record_intervals[3] == (50, 60))
        assert(record_intervals[4] == (60, 70))
        assert(record_intervals[5] == (70, 80))
        assert(record_intervals[7] == (90, 100))
        assert(record_intervals[8] == (100, 110))
        assert(record_intervals[9] == (110, 120))

        record_intervals = reader.get_record_intervals(t_record=120, t_offset=30, t_merge=30)
        assert(record_intervals[0] == (3, 14))
        assert(record_intervals[1] == (17, 27))
