# Real-time input plotting from ItsyBitsy serial data
# Author: Alexis Dumelié
#------------------------------
import numpy as np
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import serial
import time
from datetime import datetime

DEBUG = 0
LOG_FILE = "LOGS/" + str(datetime.now()).replace(" ", "_")
LOGGING_DATA = []

y_min = 0
y_max = 3.3
step = 10 # In ms
N = step * 100

TRIGGERED = False
TIME_START = N * 1 # To not directly play sound before pressing
THRESHOLD = 0.3

#------------------------------
import glob
def detect_tty():
    tty_files = glob.glob('/dev/tty*')
    acm_files = [file for file in tty_files if 'ACM' in file]
    if acm_files:
        port = acm_files[0]
    else:
        print("No tty available !")
        port = None
    return port
#------------------------------

import random
def dummy_read():
   return random.random() * 3

def on_close(event):
    print("Window is being closed")
    print("Logging data")
    with open(LOG_FILE, "w") as f:
        for item in LOGGING_DATA:
            f.write(str(item) + "\n")
    event.accept() 

def read_serial_data(ser):
    data = ser.readline().decode().strip()
    return float(data) if data else None

def update():
    global curve, data_x, data_y
    value = read_serial_data(ser)

    if DEBUG == 2:
        value = dummy_read()
    if DEBUG >= 1:
        print(value)
    data_y = data_y[1:]  # Remove first element
    data_y.append(value)

    trigger_event(data_y)

    LOGGING_DATA.append(value)
    curve.setData(data_x, data_y)

#------------------------------
from pydub import AudioSegment
from pydub.playback import play
def trigger_event(values):
    global TRIGGERED
    if not TRIGGERED:
        if len(LOGGING_DATA) > TIME_START:
            array = np.array(values)
            if (array < THRESHOLD).all():
                triggered()
                TRIGGERED = True
def triggered():
    print("Detected !")
    LOGGING_DATA.append("DETECTED")
    time.sleep(60*3)
    sound = AudioSegment.from_file('dreamQ1.mp3', format='mp3')
    play(sound)
    LOGGING_DATA.append("QUEUE 1")
    time.sleep(60*5) # Time for dream, then wake up
    sound = AudioSegment.from_file('dreamWake.mp3', format='mp3')
    LOGGING_DATA.append("WAKE UP")
    play(sound)

#------------------------------
port = detect_tty()
app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget()
win.setWindowTitle("Real-Time Data Plotting")
win.closeEvent = on_close
win.show()


plot = win.addPlot(title="Real-time data plot from sensor")
plot.setYRange(y_min, y_max)

YAXIS = "left"
XAXIS = "bottom"
plot.setLabel(YAXIS, "Voltage")
plot.setLabel(XAXIS, "Time (update " + str(step) +" ms)")
plot.setTitle("Input data - FSR Glove")

curve = plot.plot(pen=pg.mkPen(color='r'), width=15)
data_x = [i for i in range(N)]
data_y = [0 for _ in data_x]

ser = serial.Serial(port, 9600) 

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(step) 

#------------------------------
DRY_RUN = False
if __name__ == '__main__':
    if DRY_RUN:
        print("WARNING: DRY RUN")
        triggered()
    elif (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        sys.exit(app.exec_())
