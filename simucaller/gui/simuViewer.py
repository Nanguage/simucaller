import sys, os, random

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from simucaller.series import Series
from simucaller.helpers import get_logger

from .widget.control_panel import ControlPanel
from .widget.heatmap_panel import HeatmapPanel
from .widget.points_panel import PointsPanel
from .widget.menu import Menu

import logging
logging.basicConfig(level=logging.DEBUG)
log = get_logger(__name__)


class SimuViewer(QMainWindow, ControlPanel, HeatmapPanel, PointsPanel, Menu):
    """ Main application window. """
    def __init__(self, hdf5_path=None, parent=None):
        # init position
        self.position = {
            'x': 0,
            'y': 0,
            'z': 0,
            't': 0,
        }

        # init points
        self.selected_points = set([])

        # init window
        QMainWindow.__init__(self, parent)
        self.setWindowTitle('SimuViewer')

        # create widgets
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        # load hdf5 file
        if hdf5_path:
            if os.path.exists(hdf5_path):
                status = self.load_file(hdf5_path)
                if isinstance(status, Exception):
                    raise IOError("Fail to open %s"%hdf5_path)
            else:
                raise IOError("%s not exist."%hdf5_path)
        else:
            # load hdf5 file from window
            self.window_load_file()

    def load_file(self, hdf5_path):
        """ Load Series from hdf5 file """
        try:
            self.series = Series(hdf5_path)
            return True
        except Exception as e:
            log.error(e)
            return e

    def save_plot(self):
        """ Save current image """
        file_choices = "PNG (*.png);;JPEG (*.jpg);;TIFF (*.tif);;ALL (*)"
        path, _ = QFileDialog.getSaveFileName(self,
            'Open file', 'image.png', file_choices)
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            log.info("Save image file to %s"%path)

    def on_click(self, event):
        """
        handle matplotlib.backend_bases.MouseEvent ('button_press_event')

        collection clicked positions.
        """
        t, z = self.position['t'], self.position['z']
        x, y = event.xdata, event.ydata
        if x and y:
            msg = "You've clicked on (%.2f, %.2f, %.2f, %.2f)"%(t, x, y, z)
            log.info(msg)
            point = x_, y_, z_ = int(x), int(y), int(z)
            if point not in self.selected_points:
                self.selected_points.add(point)
                self.points_list.addItem(str(point))

    def on_motion(self, event):
        """
        handle matplotlib.backend_bases.MouseEvent ('motion_notify_event')

        refersh status_text
        """
        x, y = event.xdata, event.ydata
        if x and y and hasattr(self, 'series'):
            mat = self.series.get_arr2d(self.position['t'],
                                        self.position['z'],
                                        axis='xy')
            try:
                value = mat[int(round(y)), int(round(x))]
            except:
                value = 0.0

            text = "position: (%d, %.2f, %.2f, %d) value: %.2f"%(
                self.position['t'], x, y,
                self.position['z'], value)

            if hasattr(self, 'heatmap2d') and self.heatmap_cb.isChecked():
                pvalue = self.heatmap2d[int(round(y)), int(round(x))]
                text += " pvalue: %f"%pvalue
            self.status_text.setText(text)

    def on_draw(self):
        """
        Refresh the figure.
        """
        if hasattr(self, 'series'):
            # self.series exist,
            # clear the axes and redraw the plot anew
            #
            self.axes.clear()
            self.axes.grid(self.grid_cb.isChecked())

            mat = self.series.get_arr2d(self.position['t'],
                                        self.position['z'],
                                        axis='xy')
            self.axes.matshow(mat, cmap='gray')

            if hasattr(self, 'heatmap') and self.heatmap_cb.isChecked():
                from .heatmap import draw_heatmap
                draw_heatmap(self.axes, self.heatmap2d, cutoff=self.heatmap_cutoff)

            try:
                self.canvas.draw()
            except AttributeError as e:
                self.axes.clear()
                self.axes.grid(self.grid_cb.isChecked())
                self.axes.matshow(mat, cmap='gray')
                self.canvas.draw()
                log.error(str(e))
        else:
            # self.series not exist
            # show text
            #
            msg = "Data empty, please open one hdf5 file."
            log.warning(msg)
            self.axes.text(0.1, 0.5, msg,
                           bbox={'facecolor':'red', 'alpha':0.5, 'pad':10})

    def on_refresh(self):
        """
        Refresh whole frame.
        """
        if hasattr(self, 'series'):
            t_max = self.series.shape[0] - 1
            z_max = self.series.shape[3] - 1
        else:
            t_max = 1
            z_max = 1
        self.slider_t.setRange(0, t_max)
        self.slider_z.setRange(0, z_max)
        self.on_draw()

    def create_main_frame(self):
        """
        Create main frame and manage the frame layout.

        main_frame(QVBoxLayout)
        -----------------------
        canvas(FigureCanvas)
        NavigationToolBar
        control(QHBoxLayout)
        points(QHBoxLayout)
        """
        self.main_frame = QWidget()

        # Create the mpl Figure and FigCanvas objects.
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((8, 6.4), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)

        # Since we have only one plot, we can use add_axes
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)

        # Bind the events for mouse clicking and motion
        #
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)

        # Create control hbox
        #
        control_hbox = self.create_control_hbox()

        # Create heatmap hbox
        heatmap_hbox = self.create_heatmap_hbox()

        # Create points hbox
        #
        points_hbox = self.create_points_hbox()

        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(control_hbox)
        vbox.addLayout(heatmap_hbox)
        vbox.addLayout(points_hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def create_status_bar(self):
        self.status_text = QLabel("position: value:")
        self.statusBar().addWidget(self.status_text, 1)


def main():
    """
    launch main gui window.
    """
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon.png')))
    simuviewer = SimuViewer()
    simuviewer.show()
    app.exec_()
