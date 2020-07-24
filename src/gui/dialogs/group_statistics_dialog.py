import numpy as np

from PyQt5 import QtWidgets

from inspigtor.gui.widgets.group_effect_widget import GroupEffectWidget
from inspigtor.gui.widgets.time_effect_widget import TimeEffectWidget


class GroupStatisticsDialog(QtWidgets.QDialog):

    def __init__(self, pigs_model, groups_model, parent):

        super(GroupStatisticsDialog, self).__init__(parent)

        self._pigs_model = pigs_model

        self._groups_model = groups_model

        self._selected_property = self._pigs_model.selected_property

        self.init_ui()

    def build_events(self):
        """Set the signal/slots of the main window
        """

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        tabs_layout = QtWidgets.QVBoxLayout()

        tabs_layout.addWidget(self._tabs)

        main_layout.addLayout(tabs_layout)

        self.setGeometry(0, 0, 400, 400)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Statistics for {} property'.format(self._selected_property))

        self._tabs = QtWidgets.QTabWidget()

        self._group_effect_widget = GroupEffectWidget(self._groups_model, self)

        self._time_effect_widget = TimeEffectWidget(self._groups_model, self)

        self._tabs.addTab(self._group_effect_widget, 'Group effect')

        self._tabs.addTab(self._time_effect_widget, 'Time effect')

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()
