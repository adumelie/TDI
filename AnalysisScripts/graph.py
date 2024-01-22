# Graph analysis of experiment log
import sys
import numpy as np
from matplotlib import pyplot as plt
from OneEuroFilter import OneEuroFilter

file = sys.argv[1]
try:
    SHOW = False if sys.argv[2] in ["0", "False", "FALSE", "false"] else True
except IndexError:
    SHOW = True

euroFilterConfig = {
        'freq': 100,       # Hz
        'mincutoff': 1.0,  # Hz
        'beta': 0.1,       
        'dcutoff': 1.0    
        }
filter = OneEuroFilter(**euroFilterConfig)

data = []
raw = []
total_data_count = 0
calibration = True
cal_total = 0
cal_avg = 0
npavg = 0 # None
detection_times = []

with open(file, "r") as f:
    for line in f.readlines():
        try:
            value = float(line)
            raw.append(value)
            total_data_count += 1
            filtered_value = filter(value, 0.01 * total_data_count)
            data.append(filtered_value)
            if calibration:
                cal_total += filtered_value
                cal_avg = cal_total / total_data_count
        except ValueError:
            print(line)
            if line.strip() == "Phases.RUNNING":
                print("End of calibration")
                print("NOW: ", total_data_count)
                print("in sec ", 0.01 * total_data_count)
                calibration = False
                npavg = np.mean(data)
            elif line.strip() == "Phases.DETECTED":
                print("NOW: ", total_data_count)
                print("in sec ", 0.01 * total_data_count)
                detection_times.append(0.01 * total_data_count) 
            continue

print("AVG: ", cal_avg)
print("NP AVG: ", npavg)

time_in_ms = np.arange(0, 60*60*1000, 10)  # X min in milliseconds (10ms interval)
time_in_ms = time_in_ms[:len(data)]
time_in_minutes = time_in_ms / (1000 * 60)
final_min = time_in_minutes[-1]


max_index = np.argmax(data[:-120]) # Ignoring end spike
max_time_in_minutes = time_in_minutes[max_index]

print("Index where data is maximum:", max_index)
print("Corresponding time_in_ms value:", time_in_ms[max_index])
print("Time in minutes where data is maximum:", max_time_in_minutes)
plt.axvline(x=max_time_in_minutes, color='red', linestyle='--', label='Max Data Location')

# Set x-axis ticks every 5 minutes
plt.xticks(np.arange(0, max(time_in_minutes) + 1, 5))

avg = cal_avg
user = file.split("USERS")[1].split("/")[1]

# FROM TDI code
sensor_repeatability = 0.02 
state_change_range = 0.015
delta_percent = sensor_repeatability + state_change_range
plt.axhline(y=avg*(1+delta_percent), color='red', linestyle='-.', label='TDI Detection threshold')

detection_legend_added = False
for detection_tick in detection_times:
    detection_time_in_minutes = detection_tick / 60 
    print(detection_time_in_minutes)
    plt.axvline(x=detection_time_in_minutes, color='purple', linestyle='-.', label='Detection' if not detection_legend_added else '_nolegend_')
    detection_legend_added = True

plt.xlabel('Time (minutes)')
plt.ylabel('Voltage')
plt.axhline(y=avg, color='green', linestyle='--', label='1.5 min calibration average')
plt.axvline(x=1.5, color='green', linestyle='-', label='Calibration period end')
plt.axhline(y=avg*(1+sensor_repeatability), color='cyan', linestyle='--', label='+2% sensor repeatability')
plt.axhline(y=avg*(1+delta_percent), color='black', linestyle='--', label='Delta % state threshold')
plt.plot(time_in_minutes, data, color='blue', label='Filtered')
plt.plot(time_in_minutes, raw, color='red', alpha=0.5, label='Raw')
title = """
User {0}, 100Hz sampling,
Filter:'freq':100, 'mincutoff':1.0, 'beta':0.1,'dcutoff':1.0
""".format(user)
plt.title(title)

x_point = final_min 
plt.text(x_point, avg*0.9, 'End', color='black') # Place end marker near end

plt.legend()
plt.savefig(file + "-User" + user + "-Data.png")
print(SHOW)
if SHOW:
    plt.show()
plt.close()


