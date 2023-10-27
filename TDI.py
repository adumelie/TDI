import numpy as np
import random
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow
import serial
import time
from datetime import datetime

import glob
from pydub import AudioSegment
from pydub.playback import play
#----------------------------------------
class PlotWindow(QMainWindow):
    def __init__(self, debug_level=0):
        super().__init__()

        self.DEBUG = debug_level 
        self.LOG_FILE = "LOGS/" + str(datetime.now()).replace(" ", "_")
        self.LOGGING_DATA = []
        self.DEBUG_BASIC = 1
        self.DEBUG_DUMMY = 2

        self.y_min = 0
        self.y_max = 3.3
        self.stepMS = 10
        self.N = self.stepMS * 100

        self.TRIGGERED = False
        self.TIME_START = self.N * 1  # To not directly play sound before pressing
        self.THRESHOLD = 0.3
        self.BAUD_RATE = 9600
        self._serial_setup()

        self.initUI()

    def _serial_setup(self, ):
        if self.DEBUG == self.DEBUG_DUMMY:
            self.port = None
            self.ser = None
        else:
            self.port = self._detect_tty()
            self.ser = serial.Serial(self.port, self.BAUD_RATE)

    def _detect_tty(self):
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
        self.setGeometry(100, 100, 800, 600)

        self.plot = pg.PlotWidget()
        self.setCentralWidget(self.plot)


        self.plot.setYRange(self.y_min, self.y_max)
        YAXIS = "left"; XAXIS = "bottom"
        self.plot.setLabel(YAXIS, "Voltage")
        self.plot.setLabel(XAXIS, "Time (update " + str(self.stepMS) + " ms)")
        self.plot.setTitle("Input data - FSR Glove")
        self.curve = self.plot.plot(pen=pg.mkPen(color='r'), width=15)

        # Start dummy data for plot to have line at start
        self.data_x = [i for i in range(self.N)]
        self.data_y = [0 for _ in self.data_x]


        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(self.stepMS)


    def update(self):
        if self.DEBUG == self.DEBUG_DUMMY:
            value = self._dummy_read()
        else:
            value = self._read_serial_data()

        if self.DEBUG >= self.DEBUG_BASIC:
            print(value)

        self.data_y = self.data_y[1:]  # Remove first element
        self.data_y.append(value)

        self.trigger_event(self.data_y)  # Check for trigger

        self.LOGGING_DATA.append(value)
        self.curve.setData(self.data_x, self.data_y)


    def _dummy_read(self):
        return random.random() * 3  # Range 0-3

    def _read_serial_data(self):
        data = self.ser.readline().decode().strip()
        return float(data) if data else None

    def trigger_event(self, values):
        if not self.TRIGGERED:
            if len(self.LOGGING_DATA) > self.TIME_START:
                array = np.array(values)
                if (array < self.THRESHOLD).all():
                    self.triggered()
                    self.TRIGGERED = True

    def triggered(self):
        print("Detected !")
        self.LOGGING_DATA.append("DETECTED")

        print("DEBUG")
        # time.sleep(60 * 3)
        # sound = AudioSegment.from_file('dreamQ1.mp3', format='mp3')
        # play(sound)
        # self.LOGGING_DATA.append("QUEUE 1")
        # time.sleep(60 * 5)  # Time for dream, then wake up
        # sound = AudioSegment.from_file('dreamWake.mp3', format='mp3')
        # self.LOGGING_DATA.append("WAKE UP")
        # play(sound)

    def closeEvent(self, event):
        print("Window is being closed")
        print("Logging data")
        with open(self.LOG_FILE, "w") as f:
            for item in self.LOGGING_DATA:
                f.write(str(item) + "\n")
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = PlotWindow(debug_level=2)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
