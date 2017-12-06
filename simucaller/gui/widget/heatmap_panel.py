from PyQt5.QtWidgets import QHBoxLayout, QMessageBox, QLabel, QPushButton, QCheckBox, QLineEdit

from simucaller.helpers import get_logger
from simucaller.gui.heatmap import pvalue2zscore

log = get_logger(__name__)

class HeatmapPanel(object):
    """
    Abstract class for create heatmap panel.

    HeatmapPanel(QHBoxLayout)

    * heatmap_checkbox
    * heatmap_label
    * heatmap_cutoff_input(QLineEdit)
    * heatmap_cutoff_button
    """
    def load_heatmap2d(self):
        """ load 2d heatmap, and 2d zscore """
        assert hasattr(self, 'heatmap')
        z = self.position['z']
        self.heatmap2d = self.heatmap[:, :, z]

    def show_heatmap(self):
        """ handler for deal with heatmap checkbox state change """
        if hasattr(self, 'heatmap'):
            log.debug("heatmap checkbox draw.")
            self.load_heatmap2d()
            try:
                pvalue = float(self.heatmap_cutoff_input.text())
                self.heatmap_cutoff = pvalue
                self.on_draw()
            except ValueError as e:
                log.error(e)
        else:
            msg = "Please load heatmap firstly \"Menu >> View >> Load Heatmap\""
            QMessageBox.information(self, "Message", msg)
            self.heatmap_cb.setChecked(False)

    def on_heatmap_click(self):
        """ handler for deal heatmap cutoff button click """
        if hasattr(self, 'heatmap'):
            self.load_heatmap2d()
            try:
                pvalue = float(self.heatmap_cutoff_input.text())
                self.heatmap_cutoff = pvalue
                self.on_draw()
            except ValueError as e:
                log.error(str(e))

    def create_heatmap_hbox(self):
        hbox = QHBoxLayout()

        # heatmap check box
        #
        self.heatmap_cb = QCheckBox("Show &Heatmap")
        self.heatmap_cb.setChecked(False)

        self.heatmap_cb.stateChanged.connect(self.show_heatmap)

        # heatmap_cutoff_slider
        #
        heatmap_label = QLabel("heatmap cutoff (pvalue):")
        self.heatmap_cutoff_input = QLineEdit(self)
        self.heatmap_cutoff_input.setText("0.05")
        self.heatmap_cutoff_bt = QPushButton("OK")
        self.heatmap_cutoff_bt.clicked.connect(self.on_heatmap_click)

        hbox.addWidget(self.heatmap_cb)
        hbox.addWidget(heatmap_label)
        hbox.addWidget(self.heatmap_cutoff_input)
        hbox.addWidget(self.heatmap_cutoff_bt)
        return hbox
