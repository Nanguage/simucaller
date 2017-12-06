from functools import partial

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QLabel, QSlider, QVBoxLayout, QHBoxLayout

from simucaller.helpers import get_logger

log = get_logger(__name__)

class ControlPanel(object):
    """
    Abstract class for create control panel.

    ControlPanel(QHBoxLayout)

    * checkboxes(QVBoxLayout)
        - grid_checkbox
    * sliders(QVBoxLayout)
    """
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
        if hasattr(self, 'heatmap'):
            self.load_heatmap2d()
        self.label_slider_t.setText("T Axis: %d (%.2fs)"%(t, t*tiv))
        self.label_slider_z.setText("Z Axis: %d"%z)
        #
        # draw heatmap when heatmap checked
        if hasattr(self, 'heatmap') and self.heatmap_cb.isChecked():
            try:
                pvalue = float(self.heatmap_cutoff_input.text())
                self.heatmap_cutoff = pvalue
                self.on_draw()
            except ValueError as e:
                log.error(e)
        else:
            self.on_draw()

    def create_slider(self, axis, max_value, init_value=0):
        """
        Generate slider widget with the label.
        """
        label = axis.upper() + "Axis"
        slider_label = QLabel(label + ": " + str(init_value))
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

        * label_slider_t(QLabel)
        * slider_t
        * label_slider_z
        * slider_z
        """
        if hasattr(self, 'series'):
            t_max = self.series.shape[0] - 1
            z_max = self.series.shape[3] - 1
        else:
            t_max = 1
            z_max = 1
        self.slider_t, self.label_slider_t = self.create_slider("t", t_max)
        self.slider_z, self.label_slider_z = self.create_slider("z", z_max)
        sliders = QVBoxLayout()
        for w in [self.label_slider_t, self.slider_t, self.label_slider_z, self.slider_z]:
            sliders.addWidget(w)
        return sliders

    def create_control_hbox(self):
        # checkboxes
        checkboxes = QVBoxLayout()

        # Grid check box
        #
        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(False)
        self.grid_cb.stateChanged.connect(self.on_draw)

        checkboxes.addWidget(self.grid_cb)

        # sliders
        #
        sliders = self.create_sliders()

        #
        # Layout with box sizers
        #
        hbox = QHBoxLayout()

        hbox.addLayout(checkboxes)
        hbox.addLayout(sliders)
        return hbox
    