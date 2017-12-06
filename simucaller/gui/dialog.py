from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from simucaller.series import Series
from simucaller.helpers import get_logger

log = get_logger(__name__)


class SeriesLineView(QDialog):
    """
    Dialog for view time series lines.
    """
    def __init__(self, points, points_series, parent_window):
        """
        :points: (list) a list of points (x, y, z)
        :points_series: (list) a list of timeseries(numpy array) correspond to points
        """
        log.info("SerirsLineView window launched with %d points"%len(points))
        self.parent = parent_window
        #
        # init points
        self.points = points
        self.points_series = points_series

        #
        # init window
        super(SeriesLineView, self).__init__(None)
        self.create_main_frame()
        self.on_draw()

    def create_main_frame(self):

        # Create the mpl Figure and FigCanvas objects.
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((6, 3), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self)

        self.axes = self.fig.add_subplot(111)

        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self)

        # Create control hbox
        #

        #     label check box
        #
        self.cb_label = QCheckBox("Show &Label")
        self.cb_label.setChecked(False)
        self.cb_label.stateChanged.connect(self.on_draw)

        #     break points check box
        #
        self.cb_break_points = QCheckBox("break points")
        self.cb_break_points.setChecked(False)
        self.cb_break_points.stateChanged.connect(self.on_draw)

        #     simulation interval check box
        #
        self.cb_simu_intervals = QCheckBox("simulation intervals")
        self.cb_simu_intervals.setChecked(False)
        self.cb_simu_intervals.stateChanged.connect(self.on_draw)

        #     mean check box
        self.cb_mean = QCheckBox("mean")
        self.cb_mean.setChecked(False)
        self.cb_mean.stateChanged.connect(self.on_draw)

        control_hbox = QHBoxLayout()
        control_hbox.addWidget(self.cb_label)
        control_hbox.addWidget(self.cb_break_points)
        control_hbox.addWidget(self.cb_simu_intervals)
        control_hbox.addWidget(self.cb_mean)

        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(control_hbox)

        self.setLayout(vbox)

    def on_draw(self):
        import matplotlib.patches as patches
        import matplotlib.transforms as transforms
        trans = transforms.blended_transform_factory(
                self.axes.transData, self.axes.transAxes)

        self.axes.clear()
        log.debug("draw series lines")

        # draw line
        #
        if self.cb_mean.isChecked():
            series = np.asarray(self.points_series)
            s = series.mean(axis=0)            
            self.axes.plot(s, label="mean")
        else:
            lines = []
            for p, s in zip(self.points, self.points_series):
                line = self.axes.plot(s, label=str(p))
                lines.append(line)
            # add label
            if self.cb_label.isChecked():
                labels = [str(p) for p in self.points]
                self.axes.legend(labels, loc=2)

        # draw break points high light band
        #
        if self.cb_break_points.isChecked() and\
           hasattr(self.parent.series, 'break_points'):
            start, end = self.parent.series.break_points
            rect = patches.Rectangle(
                (start, 0),
                width=(end - start),
                height=1,
                transform=trans,
                color='red', alpha=0.5
            )
            self.axes.add_patch(rect)
        # draw intervals high light band
        #
        if self.cb_simu_intervals.isChecked() and\
           hasattr(self.parent.series, 'simu_intervals'):
            intervals = self.parent.series.simu_intervals
            rects = [
                patches.Rectangle(
                    (start, 0),
                    width=(end - start),
                    height=1,
                    transform=trans,
                    color='#1bc5d1', alpha=0.5
                )
                for start, end in intervals
            ]
            for rect in rects:
                self.axes.add_patch(rect)
        self.canvas.draw()


class HeatmapLoadingDialog(QDialog):
    """
    Dialog for loading heatmap.
    """
    def __init__(self, parent_window):
        """
        :series: simucaller.series.Series
        :parent_window: the main SimuViewer instance
        """
        log.info("HeatmapLoadingDialog window launched.")
        #
        # init window
        super(HeatmapLoadingDialog, self).__init__(None)
        self.parent = parent_window

        vbox = QVBoxLayout()

        self.heatmap_list = QListWidget()
        self.load_list_items()

        self.load_button = QPushButton("Load")
        self.load_button.clicked.connect(self.load_heatmap)

        vbox.addWidget(self.heatmap_list)
        vbox.addWidget(self.load_button)
        self.setLayout(vbox)

    def load_heatmap(self):
        """
        load heat map to parent
        """
        res_path = self.heatmap_list.selectedItems()[0].text()
        algorithm, name = res_path.split('/')
        log.info("heatmap {} loaded".format(res_path))
        self.parent.heatmap = self.parent.series.get_simu_result(algorithm, name)
        self.close()

    def load_list_items(self):
        """
        load all items into list widget
        """
        self.heatmap_list.clear()
        res_list = self.parent.series.list_simu_result()
        for res_path in res_list:
            self.heatmap_list.addItem(res_path)
