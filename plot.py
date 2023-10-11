# Real-time input plotting from ItsyBitsy serial data
# Author: Alexis Dumelié
#------------------------------
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import serial

DEBUG = 0

import random
def dummy_read():
   return random.random() * 3

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

    curve.setData(data_x, data_y)
#------------------------------
app = QtWidgets.QApplication([])

win = pg.GraphicsLayoutWidget()
win.setWindowTitle("Real-Time Data Plotting")
win.show()

y_min = 0
y_max = 3.3
step = 10 # In ms

plot = win.addPlot(title="Real-Time Data Plot")
plot.setYRange(y_min, y_max)

YAXIS = "left"
XAXIS = "bottom"
plot.setLabel(YAXIS, "Voltage")
plot.setLabel(XAXIS, "Time (update " + str(step) +" ms")
plot.setTitle("Input data - FSR Glove")

curve = plot.plot(pen=pg.mkPen(color='r'), width=15)
data_x = [i for i in range(step * 100)]
data_y = [0 for _ in data_x]

ser = serial.Serial('/dev/ttyACM0', 9600) 

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(step) 
#------------------------------
if __name__ == '__main__':
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        sys.exit(app.exec_())
