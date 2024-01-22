import numpy as np
from tabulate import tabulate

def convert_to_decimal_format(time_str):
    minutes, seconds = map(int, time_str.split('.'))
    total_minutes = minutes + seconds / 100
    return total_minutes

def convert_to_time_format(decimal_time):
    sign = '-' if decimal_time < 0 else ''
    total_seconds = abs(decimal_time) * 60  # Convert minutes to seconds
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    return f"{sign}{minutes:02d}:{seconds:02d}"

# RAW data
pre = [
        1.33,   # 0
        2.41,   # 1
        1.59,   # 2
        5.05,   # 3 
        9.55,   # 4
        2.17    # 5
        ]
post = [1.25,   # 0
        2.19,   # 1
        5.03,   # 2
        0.0,    # 3
        9.55,   # 4
        3.0     # 5
        ]

main_pre = list((pre[2],))  # 3 excluded as no post time
main_post = list((post[2],))
control_pre = list((pre[4], pre[5]))
control_post = list((post[4], post[5]))
calibration_pre = list((pre[0], pre[1]))
calibration_post = list((post[0], post[1]))

pre.pop(4-1) # 3 excluded as no post time
post.pop(4-1)

pre_decimal_format_times = [convert_to_decimal_format(str(time)) for time in pre]
post_decimal_format_times = [convert_to_decimal_format(str(time)) for time in post]
main_pre_dec = [convert_to_decimal_format(str(time)) for time in main_pre]
main_post_dec = [convert_to_decimal_format(str(time)) for time in main_post]
control_pre_dec = [convert_to_decimal_format(str(time)) for time in control_pre]
control_post_dec = [convert_to_decimal_format(str(time)) for time in control_post]
calibration_pre_dec = [convert_to_decimal_format(str(time)) for time in calibration_pre]
calibration_post_dec = [convert_to_decimal_format(str(time)) for time in calibration_post]


# Convert the data back to time format for the table
converted_data = [
    ["N", len(pre), len(post), len(main_pre_dec), len(main_post_dec), len(control_pre_dec), len(control_post_dec), len(calibration_pre_dec), len(calibration_post_dec)],
    ["Mean (min)", convert_to_time_format(np.mean(pre_decimal_format_times)), convert_to_time_format(np.mean(post_decimal_format_times)),
     convert_to_time_format(np.mean(main_pre_dec)), convert_to_time_format(np.mean(main_post_dec)),
     convert_to_time_format(np.mean(control_pre_dec)), convert_to_time_format(np.mean(control_post_dec)),
     convert_to_time_format(np.mean(calibration_pre_dec)), convert_to_time_format(np.mean(calibration_post_dec))],
    ["STD (min)", convert_to_time_format(np.std(pre_decimal_format_times)), convert_to_time_format(np.std(post_decimal_format_times)),
     convert_to_time_format(np.std(main_pre_dec)), convert_to_time_format(np.std(main_post_dec)),
     convert_to_time_format(np.std(control_pre_dec)), convert_to_time_format(np.std(control_post_dec)),
     convert_to_time_format(np.std(calibration_pre_dec)), convert_to_time_format(np.std(calibration_post_dec))]
]

converted_headers = ["", "Pre", "Post", "Main\_Pre", "Main\_Post", "Control\_Pre", "Control\_Post", "Calibration\_Pre", "Calibration\_Post"]

converted_table = tabulate(converted_data, converted_headers, tablefmt="fancy_grid")
print(converted_table)

converted_table_latex = tabulate(converted_data, converted_headers, tablefmt="latex_raw")
print(converted_table_latex)

#------------------------------
print("="*30)

diff_main = np.mean(main_post_dec) - np.mean(main_pre_dec)
diff_control = np.mean(control_post_dec) - np.mean(control_pre_dec)
diff_calibration = np.mean(calibration_post_dec) - np.mean(calibration_pre_dec)

print("\nIntermediate Steps:")
print("Difference in Average Times (Post - Pre) for Main:", np.mean(main_post_dec), "-", np.mean(main_pre_dec), "=", diff_main)
print("Difference in Average Times (Post - Pre) for Control:", np.mean(control_post_dec), "-", np.mean(control_pre_dec), "=", diff_control)
print("Difference in Average Times (Post - Pre) for Calibration:", np.mean(calibration_post_dec), "-", np.mean(calibration_pre_dec), "=", diff_calibration)

# Convert differences and times back to minutes
diff_main_time = convert_to_time_format(diff_main)
diff_control_time = convert_to_time_format(diff_control)
diff_calibration_time = convert_to_time_format(diff_calibration)

# Display the differences in time format
print("\nDifference in Average Times (Post - Pre) in Time Format:")
print("Main: ", diff_main_time)
print("Control: ", diff_control_time)
print("Calibration: ", diff_calibration_time)
