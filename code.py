# Itsybitsy board cod (FSR TDI)
# Author: Alexis Dumelié

import time
import board
import adafruit_dotstar
from analogio import AnalogIn
import busio

uart = busio.UART(board.TX, board.RX, baudrate=9600)

input_voltage_max = 3.3
eye_protection_offset = 0.75
#==============================

def get_voltage(pin):
    voltage = 3.3
    bit_range = 65536 # 2^16
    return (pin.value * voltage) / bit_range

#==============================
analog_in = AnalogIn(board.A1)

dotstar = adafruit_dotstar.DotStar(board.APA102_SCK, board.APA102_MOSI, 1)
dotstar.brightness = 0.0
dotstar[0] = (255, 0, 0)  # Initialize the color to red

while True:
    input_voltage = get_voltage(analog_in)
    time.sleep(0.001)
    if input_voltage is not None:
        dotstar.brightness = (input_voltage / input_voltage_max) - eye_protection_offset
        print(input_voltage)
