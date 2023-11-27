"""
# Datacollector to interface with serial from itsybitsy
# Author: Alexis Dumelié
"""
import random
from PyQt5.QtCore import QThread, pyqtSignal
from DEBUG_ENUM import DebugLevel

class DataCollector(QThread):
    value_updated = pyqtSignal(float)

    def __init__(self, serial, debug_level, replay_file=None, parent=None):
        super().__init__(parent)
        self._stop = False
        self.serial_interface = serial
        self.DEBUG = debug_level
        self.y_max = 1.5

        if self.DEBUG == DebugLevel.REPLAY:
            self.REPLAY_FILE = replay_file
            self.REPLAY_DATA = []
            if self.REPLAY_FILE:
                self._load_replay_data()

    def max(self):
        return self.y_max

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
    #------------------------------
    def run(self):
        while not self._stop:
            value = self.get_value()
            self.value_updated.emit(value)
            self.msleep(10)  # Sleep for 10 milliseconds

    def stop(self):
        self._stop = True
    #------------------------------

    def get_value(self):
        if self.DEBUG == DebugLevel.DUMMY:
            value = self._dummy_read()
        elif self.DEBUG == DebugLevel.REPLAY:
            value = self._consume_replay_data()
        else:
            value = self._read_serial_data()
        if self.DEBUG >= DebugLevel.BASIC:
            print(value)
        return value

    def _dummy_read(self):
        return random.random() * self.y_max

    def _consume_replay_data(self):
        NO_MORE_DATA = 0
        if self.REPLAY_DATA:
            return self.REPLAY_DATA.pop(0)
        return NO_MORE_DATA

    def _read_serial_data(self):
        data = self.serial_interface.readline().decode().strip()
        return float(data) if data else None

#----------------------------------------
