import sounddevice as sd
import numpy as np
import wave
import os

def record_audio(duration, sample_rate=44100):
    print("Recording...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    sd.wait()
    print("Recording complete.")
    return audio_data.flatten()

def save_audio(audio_signal, output_file, sample_rate=44100):
    with wave.open(output_file, 'w') as wf:
        wf.setnchannels(1)  # Mono audio
        wf.setsampwidth(2)  # 2 bytes per sample for int16 data type
        wf.setframerate(sample_rate)
        wf.writeframes(audio_signal.tobytes())

def record_and_save_prompt(prompt, output_folder, index, duration=5):
    print(f"\t\tPrompt {index + 1}: {prompt}")
    audio_signal = record_audio(duration)
    output_file = os.path.join(output_folder, f'prompt_{index + 1}.wav')
    save_audio(audio_signal, output_file)
    print(f"Audio saved to {output_file}")

#----------------------------------------
record_duration = 5 # seconds
output_folder = 'recorded_prompts'
os.makedirs(output_folder, exist_ok=True)

prompt = "Spoon"
prompts = ["[Your NAME], You are falling asleep",
           "Please tell me what is going on through your mind ?",
           "Remember to think of {0}".format(prompt),
           "You can fall back asleep now",
           "You can wake up fully"]

for i, prompt in enumerate(prompts):
    record_and_save_prompt(prompt, output_folder, i, record_duration)
print("All prompts recorded and saved.")
