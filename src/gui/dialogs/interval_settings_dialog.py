import re

import numpy as np

from PyQt5 import QtCore, QtGui, QtWidgets


class TimeValidator(QtGui.QValidator):
    """Implements a Qt validator for 24 hours time format.
    """

    def validate(self, value, pos):
        """Validate the string.
        """

        regexp = '^([0-9]?):([0-9]?):([0-9]?)$'
        match = re.match(regexp, value)

        regexp = '^(0[0-9]|1[0-9]|2[0-3]):(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9]):(0[0-9]|1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-9])$'
        match = re.match(regexp, value)
        if match is None:
            regexp = '^([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2})$'
            match_weaker = re.match(regexp, value)
            if match_weaker:
                return (QtGui.QValidator.Intermediate, value, pos)
            else:
                return (QtGui.QValidator.Invalid, value, pos)
        else:
            return (QtGui.QValidator.Acceptable, value, pos)

    def fixup(self, s):

        hours, minutes, seconds = s.split(':')
        s = '{:02d}:{:02d}:{:02d}'.format(int(hours), int(minutes), int(seconds))

        return s


class IntervalSettingsDialog(QtWidgets.QDialog):

    def __init__(self, *args, **kwargs):

        super(IntervalSettingsDialog, self).__init__(*args, **kwargs)

        self.init_ui()

    def build_events(self):

        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)

    def build_layout(self):

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._form_group_box)
        main_layout.addWidget(self._button_box)

        layout = QtWidgets.QFormLayout()
        layout.addRow(self._start_label, self._start_line_edit)
        layout.addRow(self._end_label, self._end_line_edit)
        layout.addRow(self._record_label, self._record_spinbox)
        layout.addRow(self._offset_label, self._offset_spinbox)

        self._form_group_box.setLayout(layout)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):

        self._form_group_box = QtWidgets.QGroupBox("Interval settings (starting from t-10)")

        self._start_label = QtWidgets.QLabel('Start (H:M:S)')
        self._end_label = QtWidgets.QLabel('End (H:M:S)')
        self._record_label = QtWidgets.QLabel('Record (s)')
        self._offset_label = QtWidgets.QLabel('Offset (s)')

        validator = TimeValidator()

        self._start_line_edit = QtWidgets.QLineEdit('00:00:00')
        self._start_line_edit.setValidator(validator)

        self._end_line_edit = QtWidgets.QLineEdit('01:00:00')
        self._end_line_edit.setValidator(validator)

        self._record_spinbox = QtWidgets.QSpinBox()
        self._record_spinbox.setMinimum(1)
        self._record_spinbox.setMaximum(20000)
        self._record_spinbox.setValue(300)

        self._offset_spinbox = QtWidgets.QSpinBox()
        self._offset_spinbox.setMinimum(0)
        self._offset_spinbox.setMaximum(20000)
        self._offset_spinbox.setValue(60)

        self._button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)

    def value(self):

        start = self._start_line_edit.text()
        end = self._end_line_edit.text()
        record = self._record_spinbox.value()
        offset = self._offset_spinbox.value()

        return (start, end, record, offset)

    def init_ui(self):
        """
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()
