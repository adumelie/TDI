from enum import IntEnum

class Phases(IntEnum):
    CALIBRATION = 0
    RUNNING = 1
    DETECTED = 2
    PROMPTING = 3
    RECORDING = 4
