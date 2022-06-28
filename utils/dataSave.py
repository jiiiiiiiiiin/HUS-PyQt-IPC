import pandas as pd
# import numpy as np
# import os


def write_data(data: dict, filename):
    key_ids = data.keys()
    tmp = {}
    list_len = []
    for key_id in key_ids:
        key_names = data.get(key_id).keys()
        for key_name in key_names:
            list_len.append(len(data.get(key_id).get(key_name)))
            tmp[f"id:{key_id}-{key_name}"] = data.get(key_id).get(key_name)

    len_max = max(list_len)
    for key in tmp:
        if len(tmp[key]) < len_max:
            tmp[key].extend([0 for i in range(len_max - len(tmp[key]))])

    df = pd.DataFrame(tmp)
    df.to_csv(f'{filename}.csv')


# if __name__ == '__main__':
#     data = {
#         0x01: {
#             "pv_input_voltage": [0, 1, 2, 3],
#             "pv_input_current": [0],
#             "pv_output_voltage": [0],
#             "pv_output_current": [0],
#         },
#         0x02: {
#             "dcdc1_input_voltage": [0],
#             "dcdc1_input_current": [0],
#             "dcdc1_output_voltage": [0],
#             "dcdc1_output_current": [0]
#         }
#     }
#
#     write_data(data, '123')