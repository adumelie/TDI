"""
# Targeted Dream Incubation client code
# Author: Alexis Dumelié
#
# Code prototyping aided by LLM
# Final code: Alexis Dumelié
"""
#----------------------------------------
import time
import sys
import random
import glob
from datetime import datetime

import numpy as np
import serial

import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox

from pydub import AudioSegment
from pydub.playback import play
#----------------------------------------
NORMAL = 0
DEBUG_BASIC = 1
DEBUG_DUMMY = 2
DEBUG_REPLAY = 3
#----------------------------------------
class DataCollector(QThread):
    value_updated = pyqtSignal(float)

    def __init__(self, ser, debug_level, y_max, parent=None):
        # super(DataCollector, self).__init__(parent)
        super().__init__(parent)
        self._stop = False
        self.serial_interface = ser
        self.DEBUG = debug_level
        self.y_max = y_max

    def run(self):
        while not self._stop:
            value = self.get_value()
            self.value_updated.emit(value)
            self.msleep(10)  # Sleep for 10 milliseconds

    def stop(self):
        self._stop = True

    def get_value(self):
        if self.DEBUG == DEBUG_DUMMY:
            value = self._dummy_read()
        elif self.DEBUG == DEBUG_REPLAY:
            value = self._consume_replay_data()
        else:
            value = self._read_serial_data()
        if self.DEBUG >= DEBUG_BASIC:
            print(value)
        return value

    def _dummy_read(self):
        return random.random() * self.y_max

    def _read_serial_data(self):
        data = self.serial_interface.readline().decode().strip()
        return float(data) if data else None
#----------------------------------------
class PlotWindow(QMainWindow):
    def __init__(self, debug_level=0, replay_file=None):
        super().__init__()

        self.DEBUG = debug_level
        self.LOG_FILE = "LOGS/" + str(datetime.now()).replace(" ", "_")
        self.LOGGING_DATA = []

        if self.DEBUG == DEBUG_REPLAY:
            self.REPLAY_FILE = replay_file
            self.REPLAY_DATA = []
            if self.REPLAY_FILE:
                self._load_replay_data()

        self.soundDir = "Sounds/"

        self.y_min = 0
        self.y_max = 1.5
        self.stepMS = 10    # 100 Hz sampling
        self.N_VALUES = self.stepMS * 100

        # Start dummy data for plot to have line at start
        self.data_x = list(range(self.N_VALUES))
        self.data_y = [0 for _ in self.data_x]

        self.TRIGGERED = False
        self.average = 0
        self.THRESHOLD = 0.3
        self.BAUD_RATE = 9600
        self._serial_setup()

        self.data_collector = DataCollector(self.ser, debug_level, self.y_max)
        self.data_collector.value_updated.connect(self.update_value)
        self.data_collector.start()

        # Calibration phase
        open_values, closed_values = self._calibration()
        self.mean_open = np.mean(open_values)
        self.mean_closed =np.mean(closed_values)
        self.std_open = np.std(open_values)
        self.std_closed = np.std(closed_values)
        range_factor = 3 
        self.y_top = self.mean_open - range_factor * self.std_open
        self.y_bottom = self.mean_open - range_factor * self.std_open
        self.y_bottom = 1 # TODO debug RM


        self.initUI()

    def _calibration(self, num_actions=3):
        open_values = []
        closed_values = []
        for _ in range(num_actions):
            action_close = "Please close your fist, press Enter when done"
            closed_values.append(self.record_action(action_close, is_open=False))

            action_open = "Please open your fist, press Enter when done"
            open_values.append(self.record_action(action_open, is_open=True))
        return open_values, closed_values

    def record_action(self, action_name, is_open):
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

    def _load_replay_data(self):
        if self.REPLAY_FILE:
            with open(self.REPLAY_FILE, 'r', encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            value = float(line)
                            self.REPLAY_DATA.append(value)
                        except ValueError:
                            pass  # Ignore non-numeric data

    def _serial_setup(self, ):
        if self.DEBUG == DEBUG_DUMMY:
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

        self.plot.setYRange(self.y_min, self.y_max)
        YAXIS = "left"; XAXIS = "bottom"
        self.plot.setLabel(YAXIS, "Voltage")
        self.plot.setLabel(XAXIS, "Time (update " + str(self.stepMS) + " ms)")
        self.plot.setTitle("Input data - FSR Glove")
        self.curve = self.plot.plot(pen=pg.mkPen(color='r'), width=15)

        self.avg_text_item = pg.TextItem("", anchor=(0, 0), color='w', border='b')
        self.plot.addItem(self.avg_text_item) # TODO: anchor not working as expected (MINOR)

        # Detection threshold lines for visual reference
        self.plot.addLine(y=self.y_top, pen=pg.mkPen('y'))
        self.plot.addLine(y=self.y_bottom, pen=pg.mkPen('y'))

        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.stepMS)

    def update_value(self, value):
        self.new_value = value

    def get_value(self):
        return self.new_value

    def update(self):
        value = self.get_value()

        # Updating data
        self.data_y = self.data_y[1:]  # Remove first element
        self.data_y.append(value)

        # Process update
        self.check_for_trigger(self.data_y)

        # Log and plot
        self.LOGGING_DATA.append(value)
        self.curve.setData(self.data_x, self.data_y)

        if self.average is not None:
            self.avg_text_item.setText(f"Average: {self.average:.2f}")
        if self.TRIGGERED:
            self.curve.setPen(pg.mkPen(color='g'))



    def _replay_from_log(self, log_file):
        with open(log_file, 'r', encoding="utf-8") as f:
            for line in f:
                data = line.strip().split(',')
                if len(data) == 2:
                    x_value, y_value = float(data[0]), float(data[1])
                    self.data_x.append(x_value)
                    self.data_y.append(y_value)
                    self.plotWidget.plot(self.x, self.y, pen=pg.mkPen('b'))
                time.sleep(0.1)

    def _consume_replay_data(self):
        NO_MORE_DATA = 0
        if self.REPLAY_DATA:
            return self.REPLAY_DATA.pop(0)
        return NO_MORE_DATA

    def check_for_trigger(self, values):
        # Once CHECK is true, check if value returns to range of beginning
        # TODO use y_top y_bottom
        if not self.TRIGGERED:
            self.average = sum(values) / len(values)
            # Allow the first N values to elapse before checking
            if len(self.LOGGING_DATA) > self.N_VALUES:
                if self.average >= self.y_bottom:
                    self.triggered()
                    self.TRIGGERED = True

    def triggered(self):
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

    app = QApplication(sys.argv)
    window = PlotWindow(debug_level, replay_file)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
