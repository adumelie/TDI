"""
# Targeted Dream Incubation client code
# Author: Alexis Dumelié
"""
#----------------------------------------
import time
import sys
import glob
from datetime import datetime

import numpy as np
import serial

from OneEuroFilter import OneEuroFilter
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
#----------------------------------------
from DEBUG_ENUM import DebugLevel
from PHASES_ENUM import Phases
from Datacollector import DataCollector
from recorder import Recorder
#----------------------------------------
class PlotWindow(QMainWindow):
    def __init__(self, debug_level=0, replay_file=None, is_live=True):
        super().__init__()
        self.LIVE = is_live
        self.DEBUG = debug_level
        self.LOG_FILE = "LOGS/" + str(datetime.now()).replace(" ", "_")
        self.LOGGING_DATA = []
        self.PHASE = Phases.CALIBRATION
        self.START_TIME = time.time()
        self.CALIBRATION_PERIOD = 90 # 1.5 min
        self.STABLE_STATE = 0
        self.NEW_STATE = 0
        self.NEW_STATE_START_TIME = 0
        self.NEW_STABLE_STATE_TIME_WINDOW = 10 # seconds
        self.STATE_CHANGING = False
        self.GRACE_PERIOD_START = 0 
        self.GRACE = False
        self.GRACE_WINDOW = 10
        self.calibration_total = 0
        self.calibration_avg_count = 0
        self.calibration_avg = 0

        euroFilterConfig = {
                'freq': 100,       # Hz
                'mincutoff': 1.0,  # Hz
                'beta': 0.1,       
                'dcutoff': 1.0    
                }
        self.filter = OneEuroFilter(**euroFilterConfig)
        self.total_data_count = 0

        self.stepMS = 10    # 100 Hz sampling
        self.N_VALUES = self.stepMS * 100 
        self.avg_last_sec = 0

        # Start dummy data for plot to have line at start
        self.data_x = list(range(self.N_VALUES))
        self.data_y = [0 for _ in self.data_x]
        self.data_y_raw = [0 for _ in self.data_x]
        # Data_y has values over last 1 second

        self.TRIGGERED = False 
        self.BAUD_RATE = 9600
        self._serial_setup()

        self.data_collector = DataCollector(self.ser, debug_level, replay_file)
        self.data_collector.value_updated.connect(self.update_value)
        self.data_collector.start()
        self.new_value = 0

        self.recorder = None
        self.cycle = 0
        self.set_recorder()

        self.waitForUser()
        self.initUI()

    def set_recorder(self):
        self.recorder = Recorder(self.cycle)
        self.recorder.finished_signal.connect(self.reset_trigger)
        self.recorder.log_send.connect(self.log_tdi)

    def log_tdi(self, log_record):
        self.LOGGING_DATA.append(log_record)
        
    def reset_trigger(self):    # Called on Recorder termination
        self.cycle += 1
        self.STABLE_STATE = self.calibration_avg
        self.NEW_STATE = 0
        self.NEW_STATE_START_TIME = 0
        self.STATE_CHANGING = False
        self.GRACE_PERIOD_START = time.time()
        self.GRACE = True
        self.set_recorder()
        self.TRIGGERED = False

    def set_phase(self, phase): 
        self.PHASE = phase
        self.LOGGING_DATA.append(self.PHASE)

    def waitForUser(self):
        message = "Press ok when ready !"
        msg_box = QMessageBox()
        msg_box.setWindowTitle("User Action - Device check")
        RICH_TEXT_FORMAT = 1
        msg_box.setTextFormat(RICH_TEXT_FORMAT)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
            self.close()    # CTRL-Q close shortcut

    def _serial_setup(self, ):
        if self.DEBUG >= DebugLevel.DUMMY:
            self.port = None
            self.ser = None
        else:
            self.port = self._detect_tty()
            self.ser = serial.Serial(self.port, self.BAUD_RATE)
            try: # Test readable
                _ = self.ser.readline()
            except PermissionError:
                print(f"Permission error when reading from serial {self.port} \
                      run './serial_setup.sh'")
                sys.exit(1)

    @staticmethod
    def _detect_tty():
        tty_files = glob.glob('/dev/tty*')
        acm_files = [file for file in tty_files if 'ACM' in file]
        if acm_files:
            port = acm_files[0]
        else:
            print("No tty available !")
            port = None
        return port

    def initUI(self):
        self.setWindowTitle('Real-time data plot from sensor')

        self.WINDOW_WIDTH = 800
        self.WINDOW_HEIGHT = 600
        self.setGeometry(100, 100, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        self.plot = pg.PlotWidget()
        self.setCentralWidget(self.plot)

        self.plot.setXRange(0, self.N_VALUES)
        self.plot.setYRange(0, self.data_collector.max())

        YAXIS = "left"; XAXIS = "bottom"
        self.plot.setLabel(YAXIS, "Voltage")
        self.plot.setLabel(XAXIS, "Time (update " + str(self.stepMS) + " ms)")
        self.plot.setTitle("Input data - FSR Glove")
        self.curve = self.plot.plot(pen=pg.mkPen(color='r'), width=15)
        self.curve_raw = self.plot.plot(pen=pg.mkPen(color='b'), width=10)

        self.avg_text_item = pg.TextItem("", anchor=(0, 0), color='w', border='b')
        self.plot.addItem(self.avg_text_item) # TODO: anchor not working as expected (MINOR)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.stepMS)

    def closeEvent(self, event):
        print("Window is being closed")
        print("Logging data")
        with open(self.LOG_FILE, "w", encoding="utf-8") as f:
            for item in self.LOGGING_DATA:
                f.write(str(item) + "\n")
        event.accept()

    def update_value(self, value):
        self.new_value = value

    def get_value(self):
        return self.new_value

    def update_data(self, value):
        filtered_value = self.filter(value, 0.001 * self.total_data_count)
        self.data_y = self.data_y[1:]  # Remove first element
        self.data_y_raw = self.data_y_raw[1:]
        self.data_y_raw.append(value)
        self.data_y.append(filtered_value)
        self.avg_last_sec = np.mean(self.data_y)
        self.total_data_count += 1
        self.LOGGING_DATA.append(value) # Log raw values to be able to replay filtering differently

    def update_plot(self):
        self.curve.setData(self.data_x, self.data_y)
        self.curve_raw.setData(self.data_x, self.data_y_raw)
        if self.avg_last_sec is not None:
            self.avg_text_item.setText(f"Average: {self.avg_last_sec:.3f}, AVG_T {np.mean(self.data_y):.3f}")
        if self.PHASE == Phases.CALIBRATION:
            self.curve.setPen(pg.mkPen(color='y'))
        else:
            self.curve.setPen(pg.mkPen(color='r'))
        if self.TRIGGERED:
            self.curve.setPen(pg.mkPen(color='g'))
    #---------------
    def update(self):
        value = self.get_value()
        self.update_data(value)
        if self.PHASE == Phases.CALIBRATION:
            if time.time() - self.START_TIME >= self.CALIBRATION_PERIOD:
                self.STABLE_STATE = self.calibration_avg
                self.plot.addLine(y=self.calibration_avg, pen=pg.mkPen('y'))
                self.set_phase(Phases.RUNNING)
                self.LOGGING_DATA.append("CAL_AVG: {0}".format(self.STABLE_STATE))
            else:
                # Running average update
                self.calibration_total += value
                self.calibration_avg_count += 1
                self.calibration_avg = self.calibration_total / self.calibration_avg_count
        else:
            self.check_for_trigger()
        self.update_plot()

    def check_for_trigger(self):
        """
        Base case:
            State has no yet changed
            If our current value is above the original state + delta
            then we are in a changing phase
            Set new state as being current value
            Start timer (timer is reset upon value changing out of bounded range)
        Changing case:
            We are in changing state, we have passed out of the range
            from the original stable state
            New upper bound based on previous new state + delta
            Now see if we are still changing (value is above this new bound)
            Or if we are within bound of the new state
            If above, we are still changing, set new state, reset state timer
            If still in range: check timer, are we potentially waiting to
            climb more ? Or have we been in this new state for long enough ?
            If we have been here for long enough then this is a NEW STABLE state
            Hence we have achieved detection !
        """
        if time.time() - self.GRACE_PERIOD_START >= self.GRACE_WINDOW:
            self.GRACE = False

        if not self.LIVE:
            return  # Ignore checking when dry run
        if self.TRIGGERED:
            return # Ignore checking if already in triggered state
        if self.GRACE:
            print("Grace {0}".format(time.time())) # RM
            return # After closing hand again small grace period of checking

        sensor_repeatability = 0.02 
        state_change_range = 0.015
        delta_percent = sensor_repeatability + state_change_range

        if self.STATE_CHANGING:
            # TODO what if we go back down ?
            changing_state_upper_bound = self.NEW_STATE * (1 + delta_percent)
            print("DEBUG: STATE CHANGING + {0}".format(changing_state_upper_bound))  # RM
            if self.avg_last_sec >= changing_state_upper_bound:
                self.NEW_STATE = self.avg_last_sec # Still changing
                self.NEW_STATE_START_TIME = time.time()
            else:
                STABILIZED = time.time() - self.NEW_STATE_START_TIME >= self.NEW_STABLE_STATE_TIME_WINDOW
                if STABILIZED:
                    self.triggered()
        else: # Still in range of original stable state
            original_upper_bound_stable = self.STABLE_STATE * (1 + delta_percent) 
            if self.avg_last_sec >= original_upper_bound_stable:
                self.STATE_CHANGING = True
                self.NEW_STATE = self.avg_last_sec
                self.NEW_STATE_START_TIME = time.time()

    def triggered(self):    # TDI PROTOCOL
        self.TRIGGERED = True
        self.set_phase(Phases.DETECTED)
        print(self.PHASE)
        print("Starting prompting/recording phase, graph will keep updating...")
        self.recorder.start()

#----------------------------------------
def main():
    replay_file = None
    debug_level = DebugLevel.NORMAL
    if len(sys.argv) > 1:
        debug_level = int(sys.argv[1])
        if debug_level == DebugLevel.REPLAY and len(sys.argv) > 2:
            replay_file = sys.argv[2]
            if not replay_file.startswith("LOGS/"):
                replay_file = "LOGS/" + replay_file
    elif len(sys.argv) > 3:
        print("Usage: python your_script.py <debug_level> [<replay_file>]")
        sys.exit(1)
    # False if DRY RUN --> NO DETECTION
    LIVE = True
    print("LIVE: ", LIVE)
    app = QApplication(sys.argv)
    window = PlotWindow(debug_level, replay_file, LIVE)
    window.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()
