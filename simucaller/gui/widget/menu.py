from PyQt5.QtWidgets import QMessageBox, QAction, QFileDialog
from PyQt5.QtGui import QIcon

from simucaller.gui.dialog import HeatmapLoadingDialog
from simucaller.helpers import get_logger

log = get_logger(__name__)

class Menu(object):
    """
    Abstract class for create menu.

    Menu

    * File
        - Load file
        - Save plot
        - Quit
    * View
        - Load Heatmap
    * Help
        - About
    """
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

    def window_load_heatmap(self):
        """ launch window for load heatmap. """
        dialog = HeatmapLoadingDialog(self)
        dialog.exec_()
        self.load_heatmap2d()

    def create_action(self, text, slot=None, shortcut=None,
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

    def add_actions(self, target, actions):
        """ helper function for add actions to menu """
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def on_about(self):
        """ Show about text. """
        msg = """ A simple GUI for view fMRI time series and simulation calling result:

        * View 4D fMRI image.
        * View simulation region.
        * Select region by click then:
            generate the time series line plot.
            generate the pvalue bar plot.
        * Save images.

        """
        QMessageBox.about(self, "About this software", msg.strip())

    def create_menu(self):
        #
        # file menu
        self.file_menu = self.menuBar().addMenu("&File")
        load_file_action = self.create_action("&Load file",
            shortcut="Ctrl+O", slot=self.window_load_file,
            tip="Load file")
        save_image_action = self.create_action("&Save plot",
            shortcut="Ctrl+S", slot=self.save_plot,
            tip="Save the plot")
        quit_action = self.create_action("&Quit", slot=self.close,
            shortcut="Ctrl+Q", tip="Close the application")
        self.add_actions(self.file_menu, (load_file_action, save_image_action, quit_action))

        #
        # view menu
        self.view_menu = self.menuBar().addMenu("&View")
        load_heatmap_action = self.create_action("&Load Heatmap",
            slot=self.window_load_heatmap,
            tip="Load Heatmap")
        self.add_actions(self.view_menu, (load_heatmap_action,))

        #
        # help menu
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About",
            shortcut='F1', slot=self.on_about,
            tip='About the demo')

        self.add_actions(self.help_menu, (about_action,))
