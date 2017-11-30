from __future__ import print_function
import sys, os, random

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from series import Series
from helpers import get_logger

import logging
logging.basicConfig(level=logging.DEBUG)
log = get_logger(__name__)


class SimuViewer(QMainWindow):
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
            print(hdf5_path)
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

    def window_load_file(self):
        """ hdf5 file loading dialog. """
        file_choices = "HDF5 (*.h5);;ALL (*)"
        path, _ = QFileDialog.getOpenFileName(self,
            'Save file', '',
            file_choices)
        if path:
            status = self.load_file(path)
            if not isinstance(status, Exception):
                # load success
                log.info("hdf5 file %s loaded"%path)
            else:
                # load fail
                msg = str(status)
                QMessageBox.information(self, "Fail to open file:\n", msg)
        self.on_refresh()

    def save_plot(self):
        """ Save current image """
        file_choices = "PNG (*.png);;JPEG (*.jpg);;TIFF (*.tif);;ALL (*)"
        path, _ = QFileDialog.getSaveFileName(self,
            'Open file', 'image.png', file_choices)
        if path:
            self.canvas.print_figure(path, dpi=self.dpi)
            log.info("Save image file to %s"%path)

    def on_about(self):
        """ Show about text. """
        msg = """ A simple GUI for view fMRI time series and simulation calling result:

        * Input Series hdf5 file.
        * View 4D fMRI image.
        * View simulation region.
        * Select region by click then:
            generate the time series line plot.
            generate the pvalue bar plot.
        * Save images.

        """
        QMessageBox.about(self, "About this software", msg.strip())

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
                value = mat[int(y), int(x)]
            except:
                value = 0.0
            self.status_text.setText("position: (%d, %.2f, %.2f, %d) value: %.2f"%(
                self.position['t'],
                x, y,
                self.position['z'],
                value
            ))

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

            self.canvas.draw()
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

    def on_slide(self):
        """
        handler for slider value change event.
        """
        t = self.slider_t.value()
        z = self.slider_z.value()
        self.position['t'] = t
        self.position['z'] = z
        if hasattr(self, 'series'):
            tiv = self.series.time_interval
        else:
            tiv = 0
        self.label_slider_t.setText("T Axis: %d (%.2fs)"%(t, t*tiv))
        self.label_slider_z.setText("Z Axis: %d"%z)
        self.on_draw()

    def clear_points(self):
        """
        handler for points_clear_button click event.
        """
        log.info("clear selected points.")
        self.selected_points = set([])
        self.points_list.clear()

    def draw_series_line(self):
        """
        handler for points_draw_series click event.
        
        launch SeriesLineView Dialog.
        """
        points = list(self.selected_points)
        points_series = [self.series.get_series(x, y, z) for x, y, z in points]
        line_dialog = SeriesLineView(points, points_series)
        line_dialog.exec_()


    def create_main_frame(self):
        """
        Create main frame and manage the frame layout.

        main_frame(QVBoxLayout)
        -----------------------
        canvas(FigureCanvas)
        NavigationToolBar
        control(QHBoxLayout)
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

        # Create points hbox
        #
        points_hbox = self.create_points_hbox()

        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(control_hbox)
        vbox.addLayout(points_hbox)

        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)

    def create_control_hbox(self):
        """
        Control_hbox
        ------------
        Grid_check_box
        sliders
        """
        # Grid check box
        #
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.grid_cb.stateChanged.connect(self.on_draw) #int

        # sliders
        #
        sliders = self.create_sliders()

        #
        # Layout with box sizers
        #
        hbox = QHBoxLayout()

        for w in [self.grid_cb]:
            hbox.addWidget(w)
            hbox.setAlignment(w, Qt.AlignVCenter)
        hbox.addLayout(sliders)
        return hbox

    def create_points_hbox(self):
        """
        points_hbox
        -----------
        points_list
        buttons
            clear_button
            draw_series_button
        """
        #
        # points_list
        self.points_list = QListWidget()
        #
        # clear button
        self.points_clear_button = QPushButton("Clear")
        self.points_clear_button.clicked.connect(self.clear_points)
        #
        # draw_series_button
        self.points_draw_series_button = QPushButton("Draw series")
        self.points_draw_series_button.clicked.connect(self.draw_series_line)
        #
        # buttons
        buttons = QVBoxLayout()
        buttons.addWidget(self.points_clear_button)
        buttons.addWidget(self.points_draw_series_button)
        #
        # hbox
        hbox = QHBoxLayout()
        hbox.addWidget(self.points_list)
        hbox.addLayout(buttons)
        return hbox

    def create_status_bar(self):
        self.status_text = QLabel("position: value:")
        self.statusBar().addWidget(self.status_text, 1)

    def create_menu(self):
        """
        Menu
        ----
        File
            Load file
            Save plot
            Quit
        Help
            About
        """
        def create_action(text, slot=None, shortcut=None,
                          icon=None, tip=None, checkable=False,
                          signal="triggered()"):
            """ helper function for create action """
            action = QAction(text, self)
            if icon is not None:
                action.setIcon(QIcon(":/%s.png" % icon))
            if shortcut is not None:
                action.setShortcut(shortcut)
            if tip is not None:
                action.setToolTip(tip)
                action.setStatusTip(tip)
            if slot is not None:
                action.triggered.connect(slot)
            if checkable:
                action.setCheckable(True)
            return action

        def add_actions(target, actions):
            """ helper function for add actions to menu """
            for action in actions:
                if action is None:
                    target.addSeparator()
                else:
                    target.addAction(action)

        #
        # file menu
        self.file_menu = self.menuBar().addMenu("&File")
        load_file_action = create_action("&Load file",
            shortcut="Ctrl+O", slot=self.window_load_file,
            tip="Save the plot")
        save_image_action = create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot,
            tip="Save the plot")
        quit_action = create_action("&Quit", slot=self.close,
            shortcut="Ctrl+Q", tip="Close the application")
        add_actions(self.file_menu, (load_file_action, save_image_action, quit_action))

        #
        # help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = create_action("&About",
            shortcut='F1', slot=self.on_about,
            tip='About the demo')

        add_actions(self.help_menu, (about_action,))

    def create_slider(self, label, max_value, init_value=0):
        """
        Generate slider widget with the label.
        :label: slider label
        :max_value: slider range's max value
        """
        slider_label = QLabel(label + " " + str(init_value))
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, max_value)
        slider.setValue(init_value)
        slider.setTracking(True)
        slider.setTickPosition(QSlider.TicksBothSides)
        slider.valueChanged.connect(self.on_slide) # connect to refresh
        return slider, slider_label

    def create_sliders(self):
        """
        sliders(QVBoxLayout)
        --------------------
            label_slider_t(QLabel)
            slider_t
            label_slider_z
            slider_z
        """
        if hasattr(self, 'series'):
            t_max = self.series.shape[0] - 1
            z_max = self.series.shape[3] - 1
        else:
            t_max = 1
            z_max = 1
        self.slider_t, self.label_slider_t = self.create_slider("T axis:", t_max)
        self.slider_z, self.label_slider_z = self.create_slider("Z axis:", z_max)
        sliders = QVBoxLayout()
        for w in [self.label_slider_t, self.slider_t, self.label_slider_z, self.slider_z]:
            sliders.addWidget(w)
        return sliders


class SeriesLineView(QDialog):
    """
    Dialog for view time series lines.
    """
    def __init__(self, points, points_series, parent=None):
        """
        :points: (list) a list of points (x, y, z)
        :points_series: (list) a list of timeseries(numpy array) correspond to points
        """
        log.info("SerirsLineView window launched with %d points"%len(points))
        #
        # init points
        self.points = points
        self.points_series = points_series

        #
        # init window
        super(SeriesLineView, self).__init__(parent)
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

        #   Grid check box
        #
        self.cb_label = QCheckBox("Show &Label")
        self.cb_label.setChecked(False)
        self.cb_label.stateChanged.connect(self.on_draw) #int

        control_hbox = QHBoxLayout()
        control_hbox.addWidget(self.cb_label)

        vbox = QVBoxLayout()
        vbox.addWidget(self.mpl_toolbar)
        vbox.addWidget(self.canvas)
        vbox.addLayout(control_hbox)

        self.setLayout(vbox)

    def on_draw(self):
        self.axes.clear()
        log.debug("draw series lines")
        lines = []
        for p, s in zip(self.points, self.points_series):
            line = self.axes.plot(s, label=str(p))
            lines.append(line)
        if self.cb_label.isChecked():
            labels = [str(p) for p in self.points]
            self.axes.legend(labels, loc=2)
        self.canvas.draw()
    
    def on_pick(self):
        pass


def main():
    app = QApplication(sys.argv)
    simuviewer = SimuViewer()
    simuviewer.show()
    app.exec_()


if __name__ == "__main__":
    main()