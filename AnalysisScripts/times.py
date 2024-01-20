import numpy as np
from tabulate import tabulate

def convert_to_decimal_format(time_str):
    minutes, seconds = map(int, time_str.split('.'))
    total_minutes = minutes + seconds / 100
    return total_minutes

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


pre_decimal_format_times = [convert_to_decimal_format(str(time)) for time in pre]
post_decimal_format_times = [convert_to_decimal_format(str(time)) for time in post]
main_pre_dec = [convert_to_decimal_format(str(time)) for time in main_pre]
main_post_dec = [convert_to_decimal_format(str(time)) for time in main_post]
control_pre_dec = [convert_to_decimal_format(str(time)) for time in control_pre]
control_post_dec = [convert_to_decimal_format(str(time)) for time in control_post]
calibration_pre_dec = [convert_to_decimal_format(str(time)) for time in calibration_pre]
calibration_post_dec = [convert_to_decimal_format(str(time)) for time in calibration_post]

data = [
    ["N", 6, 6, 1, 1, 2, 2, 2, 2],

    ["Mean (min)", np.mean(pre_decimal_format_times), np.mean(post_decimal_format_times),
     np.mean(main_pre_dec), np.mean(main_post_dec),
     np.mean(control_pre_dec), np.mean(control_post_dec),
     np.mean(calibration_pre_dec), np.mean(calibration_post_dec)],
    
    ["STD (min)", np.std(pre_decimal_format_times), np.std(post_decimal_format_times),
     np.std(main_pre_dec), np.std(main_post_dec),
     np.std(control_pre_dec), np.std(control_post_dec),
     np.std(calibration_pre_dec), np.std(calibration_post_dec)]
    
]

headers = ["", "Pre", "Post", "Main_Pre", "Main_Post", "Control_Pre", "Control_Post", "Calibration_Pre", "Calibration_Post"]

table = tabulate(data, headers, tablefmt="fancy_grid")
print(table)

table_latex = tabulate(data, headers, tablefmt="latex_raw")
print(table_latex)
