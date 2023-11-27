"""
# Targeted Dream Incubation client code
# Author: Alexis Dumelié
#
# Note: Code prototyping aided by LLM
# Final code: Alexis Dumelié
"""
#----------------------------------------
import time
import sys
import glob
from datetime import datetime

import numpy as np
import serial

import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

from pydub import AudioSegment
from pydub.playback import play
#----------------------------------------
from DEBUG_ENUM import NORMAL, DEBUG_DUMMY, DEBUG_REPLAY
from PHASES_ENUM import CALIBRATION, RUNNING, DETECTED, PROMPTING, RECORDING
from Datacollector import DataCollector
#----------------------------------------
class PlotWindow(QMainWindow):
    def __init__(self, debug_level=0, replay_file=None, is_live=True):
        super().__init__()
        self.LIVE = is_live
        self.DEBUG = debug_level
        self.LOG_FILE = "LOGS/" + str(datetime.now()).replace(" ", "_")
        self.LOGGING_DATA = []
        self.PHASE = CALIBRATION
        self.START_TIME = time.time()
        self.CALIBARTION_PERIOD = 90 # 1.5 min
        self.STABLE_STATE = 0
        self.NEW_STATE = 0
        self.NEW_STATE_START_TIME = 0
        self.NEW_STABLE_STATE_TIME_WINDOW = 10 # sec
        self.STATE_CHANGING = False

        self.soundDir = "Sounds/"

        self.stepMS = 10    # 100 Hz sampling
        self.N_VALUES = self.stepMS * 100 
        self.time_start = 0
        self.AVG_WAIT = 0   # TODO RM ?
        self.avg_last_sec = 0

        # Start dummy data for plot to have line at start
        self.data_x = list(range(self.N_VALUES))
        self.data_y = [0 for _ in self.data_x]
        # Data_y has values over last 1 second

        self.TRIGGERED = False  # TODO move to using phase attribute
        self.BAUD_RATE = 9600
        self._serial_setup()

        self.data_collector = DataCollector(self.ser, debug_level, replay_file)
        self.data_collector.value_updated.connect(self.update_value)
        self.data_collector.start()
        self.new_value = 0

        # TODO TMP Values
        self.y_top = 0
        self.y_bottom = 0

        self.initUI()

    def set_phase(self, phase): 
        self.PHASE = phase
        # TODO phase change logging

    def _calibration(self, num_actions=3):  # TODO RM
        open_values = []
        closed_values = []
        for _ in range(num_actions):
            action_close = "Please close your fist, press Enter when done"
            closed_values.append(self.record_action(action_close, is_open=False))

            action_open = "Please open your fist, press Enter when done"
            open_values.append(self.record_action(action_open, is_open=True))
        return open_values, closed_values

    def record_action(self, action_name, is_open): # TODO RM
        message = (f'<p style="font-size:20px; font-weight:bold;\
            color:{"green" if is_open else "red"}">'
            f'{"OPEN" if is_open else "CLOSE"} your fist</p>'
            f'<p>{action_name}</p>')
        msg_box = QMessageBox()
        msg_box.setWindowTitle("User Action - Calibration Phase")
        RICH_TEXT_FORMAT = 1
        msg_box.setTextFormat(RICH_TEXT_FORMAT)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        return self.get_value()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q and event.modifiers() & Qt.ControlModifier:
            self.close()    # CTRL-Q close shortcut

    def _serial_setup(self, ):
        if self.DEBUG >= DEBUG_DUMMY:
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

        self.avg_text_item = pg.TextItem("", anchor=(0, 0), color='w', border='b')
        self.plot.addItem(self.avg_text_item) # TODO: anchor not working as expected (MINOR)

        # Detection threshold lines for visual reference
        self.plot.addLine(y=self.y_top, pen=pg.mkPen('g'))
        self.plot.addLine(y=self.y_bottom, pen=pg.mkPen('y'))

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.stepMS)

    def update_value(self, value):
        self.new_value = value

    def get_value(self):
        return self.new_value

    def update_data(self, value):
        # TODO 1euro filter denoising
        self.data_y = self.data_y[1:]  # Remove first element
        self.data_y.append(value)
        self.avg_last_sec_last_sec = np.mean(self.data_y)
        self.LOGGING_DATA.append(value)

    def update_plot(self):
        self.curve.setData(self.data_x, self.data_y)
        if self.avg_last_sec is not None:
            self.avg_text_item.setText(f"Average: {self.avg_last_sec:.2f}")
        if self.TRIGGERED:
            self.curve.setPen(pg.mkPen(color='g'))

    def update(self):   # MAIN FUNCTION
        value = self.get_value()
        self.update_data(value)
        self.check_for_trigger()

        if self.PHASE == CALIBRATION:
            if time.time() - self.START_TIME >= self.CALIBRATION_PERIOD:
                self.STABLE_STATE = self.calibration_avg
                self.set_phase(RUNNING)
            else:
                # Running average update
                self.calibration_total += value
                self.calibration_avg_count += 1
                self.calibration_avg = self.calibration_total / self.calibration_avg_count

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
        if not self.LIVE:
            return  # Ignore checking when dry run
        if self.TRIGGERED:
            return # Ignore checking if already in triggered state

        sensory_repeatability = 0.02 
        state_change_range = 0.1
        delta_percent = sensor_repeatability + state_change_range
        original_upper_bound_stable = self.STABLE_STATE * (1 + delta_percent) 

        if self.STATE_CHANGING:
            # state already changing (past original stable state)
            # has exited upper bound
            # now see if still changing or stabilize into new state
            # get new state, see if next new state, ie: X-time after
            # is still within state_range of new state
            changing_state_upper_bound = self.NEW_STATE * (1 + delta_percent)
            if self.avg_last_sec >= changing_state_upper_bound:
                # more than 10+2% above last state observed, still changing !
                # update new state
                self.NEW_STATE = self.avg_last_sec
                # reset new state timer
                self.NEW_STATE_START_TIME = time.time()
            else:
                # Not past new state upper bound
                # did we stabilize ? or are we potential climbing again
                # check timer :
                if time.time() - self.NEW_STATE_START_TIME >= self.NEW_STABLE_STATE_TIME_WINDOW:
                    # enough time has passed in new state
                    # hence this is a new STABLE state
                    # we have achieved detection
                    self.triggered()
            

        # check if 2 + 10 % above ORIGINAL stable state
        if self.avg_last_sec >= original_upper_bound_stable:
            self.STATE_CHANGING = True
            self.NEW_STATE = self.avg_last_sec
            self.NEW_STATE_START_TIME = time.time()
            # check if has been in new

    def triggered(self):    # TDI PROTOCOL
        self.TRIGGERED = True
        self.set_phase(DETECTED)
        # TODO: recording and dormio cycles
        # WIP
        print("Detected !")
        self.LOGGING_DATA.append("DETECTED")

        time.sleep(30)
        sound = AudioSegment.from_file(self.soundDir + 'dreamQ1.mp3', format='mp3')
        play(sound)
        self.LOGGING_DATA.append("QUEUE 1")
        time.sleep(60 * 5)  # Time for dream, then wake up
        sound = AudioSegment.from_file(self.soundDir + 'dreamWake.mp3', format='mp3')
        self.LOGGING_DATA.append("WAKE UP")
        play(sound)

    def closeEvent(self, event):
        print("Window is being closed")
        print("Logging data")
        with open(self.LOG_FILE, "w", encoding="utf-8") as f:
            for item in self.LOGGING_DATA:
                f.write(str(item) + "\n")
        event.accept()
#----------------------------------------
def main():
    replay_file = None
    debug_level = NORMAL

    if len(sys.argv) > 1:
        debug_level = int(sys.argv[1])
        if debug_level == DEBUG_REPLAY and len(sys.argv) > 2:
            replay_file = sys.argv[2]
            if not replay_file.startswith("LOGS/"):
                replay_file = "LOGS/" + replay_file
    elif len(sys.argv) > 3:
        print("Usage: python your_script.py <debug_level> [<replay_file>]")
        sys.exit(1)

    LIVE = False    # False if DRY RUN --> NO DETECTION
    app = QApplication(sys.argv)
    window = PlotWindow(debug_level, replay_file, LIVE)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
