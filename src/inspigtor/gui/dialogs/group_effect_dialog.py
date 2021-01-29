import logging

import pandas as pd

from PyQt5 import QtWidgets

import matplotlib.ticker as ticker
from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from pylab import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from inspigtor.gui.models.pvalues_data_model import PValuesDataModel
from inspigtor.gui.utils.helper_functions import func_formatter
from inspigtor.gui.utils.navigation_toolbar import NavigationToolbarWithExportButton
from inspigtor.gui.views.copy_pastable_tableview import CopyPastableTableView
from inspigtor.kernel.pigs.pigs_groups import PigsGroupsError


class GroupEffectDialog(QtWidgets.QDialog):
    """This class implements the dialog that shows the group effect. It is made of three plots which plots respectively the
    number of groups used to perform the statistical test, the p value resulting from the kruskal-wallis or Mann-Whitney 
    statistical test and the group-pairwise p values resulting from the Dunn test.
    """

    def __init__(self, selected_property, global_effect, pairwise_effect, parent=None):
        """
        """

        super(GroupEffectDialog, self).__init__(parent)

        self._selected_property = selected_property

        self._global_effect = global_effect

        self._pairwise_effect = pairwise_effect

        self.init_ui()

    def build_events(self):
        """Build the signal/slots
        """

        self._selected_time.currentIndexChanged.connect(self.on_select_time)
        self._plot_button.clicked.connect(self.on_display_p_value_plot)
        self._export_all_button.clicked.connect(self.on_export_all)

    def build_layout(self):
        """Build the layout.
        """

        main_layout = QtWidgets.QVBoxLayout()

        global_effect_groupbox_layout = QtWidgets.QVBoxLayout()
        global_effect_groupbox_layout.addWidget(self._global_effect_tableview)
        self._global_effect_groupbox.setLayout(global_effect_groupbox_layout)
        main_layout.addWidget(self._global_effect_groupbox)

        pairwise_effect_groupbox_layout = QtWidgets.QVBoxLayout()
        pairwise_effect_groupbox_layout.addWidget(self._selected_time)
        pairwise_effect_groupbox_layout.addWidget(self._pairwise_effect_tableview)
        plot_layout = QtWidgets.QHBoxLayout()
        plot_layout.addWidget(self._selected_group_1)
        plot_layout.addWidget(self._selected_group_2)
        plot_layout.addWidget(self._plot_button)
        pairwise_effect_groupbox_layout.addLayout(plot_layout)
        self._pairwise_effect_groupbox.setLayout(pairwise_effect_groupbox_layout)
        main_layout.addWidget(self._pairwise_effect_groupbox)

        main_layout.addWidget(self._export_all_button)

        self.setGeometry(0, 0, 600, 600)

        self.setLayout(main_layout)

    def build_widgets(self):
        """Build and/or initialize the widgets of the dialog.
        """

        self.setWindowTitle('Group effect statistics for {} property'.format(self._selected_property))

        self._global_effect_groupbox = QtWidgets.QGroupBox('Global effect (Mann-Whitney/Kruskal-Wallis test)')

        self._global_effect_tableview = CopyPastableTableView()
        model = PValuesDataModel(self._global_effect)
        self._global_effect_tableview.setModel(model)
        for col in range(model.columnCount()):
            self._global_effect_tableview.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)

        self._pairwise_effect_groupbox = QtWidgets.QGroupBox('Pairwise effect (Dunn test)')

        self._selected_time = QtWidgets.QComboBox()
        self._selected_time.addItems(self._global_effect.index)

        self._pairwise_effect_tableview = CopyPastableTableView()

        first_time = list(self._pairwise_effect.keys())[0]

        self._selected_group_1 = QtWidgets.QComboBox()
        self._selected_group_1.addItems(self._pairwise_effect[first_time].columns)

        self._selected_group_2 = QtWidgets.QComboBox()
        self._selected_group_2.addItems(self._pairwise_effect[first_time].columns)

        self._plot_button = QtWidgets.QPushButton('Plot')

        self._export_all_button = QtWidgets.QPushButton('Export all')

    def init_ui(self):
        """Initialiwes the dialog.
        """

        self.build_widgets()

        self.build_layout()

        self.build_events()

        self.on_select_time(0)

    def on_display_p_value_plot(self):
        """Event handler fired when the user click on the plot button of the dialog.
        """

        group1 = self._selected_group_1.currentText()
        group2 = self._selected_group_2.currentText()

        x = list(self._pairwise_effect.keys())
        y = []
        for data_frame in self._pairwise_effect.values():
            y.append(data_frame.loc[group1, group2])

        plot_widget = QtWidgets.QDialog(self)

        plot_widget.setGeometry(0, 0, 300, 300)

        plot_widget.setWindowTitle('p-values vs time for {} vs {} for {} property'.format(group1, group2, self._selected_property))

        figure = Figure()
        axes = figure.add_subplot(111)
        canvas = FigureCanvasQTAgg(figure)
        toolbar = NavigationToolbarWithExportButton(canvas, plot_widget)

        initial_interval_index = list(self._pairwise_effect.keys()).index('0h00')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(canvas)
        layout.addWidget(toolbar)
        plot_widget.setLayout(layout)

        axes.set_xlabel('time')
        axes.set_ylabel('p_value')
        axes.plot(x, y, 'o')
        loc = ticker.IndexLocator(base=10.0, offset=initial_interval_index)
        axes.xaxis.set_major_locator(loc)
        for tick in axes.xaxis.get_major_ticks():
            tick.label.set_fontsize(8)
            tick.label.set_rotation('vertical')
        canvas.draw()

        plot_widget.show()

    def on_export_all(self):
        """Export global and local effects in a excel file
        """

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, caption='Export statistics as ...', filter="Excel files (*.xls *.xlsx)")
        if not filename:
            return

        try:
            with pd.ExcelWriter(filename) as writer:
                self._global_effect.to_excel(writer, sheet_name='global effect')
                for k, v in self._pairwise_effect.items():
                    v.to_excel(writer, sheet_name=k)
        except:
            logging.error('Can not open file {} for writing.'.format(filename))

    def on_select_time(self, index):
        """Event handler called when the user select a different time from the time selection combo box.

        Args:
            index (int): the index of the newly selected time
        """

        selected_time = self._selected_time.currentText()

        model = PValuesDataModel(self._pairwise_effect[selected_time])
        self._pairwise_effect_tableview.setModel(model)

        for col in range(model.columnCount()):
            self._pairwise_effect_tableview.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
