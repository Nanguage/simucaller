from PyQt5.QtWidgets import QListWidget, QPushButton, QVBoxLayout, QHBoxLayout

from simucaller.helpers import get_logger
from simucaller.gui.dialog import SeriesLineView

log = get_logger(__name__)

class PointsPanel(object):
    """
    Abstract class for create PointsPanel.

    PointsPanel(QHBoxLayout)

    * points_list
    * buttons
        - clear_button
        - draw_series_button

    """
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
        line_dialog = SeriesLineView(points, points_series, self)
        line_dialog.exec_()

    def create_points_hbox(self):
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

