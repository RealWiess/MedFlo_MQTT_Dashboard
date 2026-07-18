# Let's write a small python script to parse the raw data from the image to understand the useless data
raw_hex = "02010614084D4544464C4F"
import binascii
print(binascii.unhexlify(raw_hex[10:]))
