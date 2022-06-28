import hid

vendor_id = 0
product_id = 0
for device_dict in hid.enumerate():
    keys = list(device_dict.keys())
    for key in keys:
        print(key, device_dict[key])
        if key == "manufacturer_string" and device_dict[key] == "ANO TC":
            vendor_id = device_dict["vendor_id"]
            product_id = device_dict["product_id"]
            break
    print()
print(vendor_id, product_id)
#
# h = hid.device()
# h.open(vendor_id, product_id)
# # while True:
# #     print(h.read(10))
# h.write([11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
