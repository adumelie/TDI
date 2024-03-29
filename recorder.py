import sounddevice as sd
import time
import numpy as np
import wave
import os
from datetime import datetime

from pydub import AudioSegment
from pydub.playback import play

from PyQt5.QtCore import QThread, pyqtSignal

class Recorder(QThread):
    finished_signal = pyqtSignal()
    log_send = pyqtSignal(str)

    def __init__(self, cycle, parent=None):
        super().__init__(parent)
        self.output_folder = 'REC/' + str(datetime.now()).replace(" ", "_")
        self.soundDir = 'recorded_prompts/'
        self.cycle = cycle
        self.MAX_CYCLE = 2

    def run(self):
        print("Allowing 3 min of sleep...")
        self.log_send.emit("Sleep period")
        time.sleep(60*3)    # Sleep for predefined amount

        sound = AudioSegment.from_file(self.soundDir + 'prompt_1.wav', format='wav')
        play(sound) # "[Name] You are falling asleep"
        self.log_send.emit("Prompt 1")

        sound = AudioSegment.from_file(self.soundDir + 'prompt_2.wav', format='wav')
        play(sound) # "Please tell me what is going on through your mind ?"
        self.log_send.emit("Prompt 2")
        filename = "cycle_" + str(self.cycle)
        output_file = self.output_folder + filename
        duration = 60
        self.log_send.emit("Recording...")
        response = self.record_audio(duration)
        self.save_audio(response, output_file)
        self.log_send.emit("Saving audio...")

        # Comment or uncomment this block based on control group of live group
        sound = AudioSegment.from_file(self.soundDir + 'prompt_3.wav', format='wav')
        play(sound) # "Remember to think of [PROMPT]"
        self.log_send.emit("Prompt 3")

        sound = AudioSegment.from_file(self.soundDir + 'prompt_4.wav', format='wav')
        play(sound) # "You can fall back asleep now, hold on to glove again"
        self.log_send.emit("Prompt 4")

        if self.cycle == self.MAX_CYCLE:
            prompt_final = AudioSegment.from_file(self.soundDir + 'prompt_5.wav', format='wav')
            play(prompt_final) # "You can wake up fully"
            self.log_send.emit("Wake up")
        self.finished_signal.emit() # Terminate and move to next cycle upon restart

    def record_audio(self, duration, sample_rate=44100):
        print("Recording...")
        audio_data = sd.rec(int(duration * sample_rate), 
                            samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        print("Recording complete.")
        return audio_data.flatten()

    def save_audio(self, audio_signal, output_file, sample_rate=44100):
        with wave.open(output_file, 'w') as wf:
            wf.setnchannels(1)  # Mono audio
            wf.setsampwidth(2)  # 2 bytes per sample for int16 data type
            wf.setframerate(sample_rate)
            wf.writeframes(audio_signal.tobytes())
