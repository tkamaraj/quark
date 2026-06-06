import ctypes
import struct

# 1. Define ctypes integers
val1 = ctypes.c_int(-42)
val2 = ctypes.c_uint16(65535)

# 2. Pack using struct format characters:
# 'i' represents a 4-byte signed integer
# 'H' represents a 2-byte unsigned short
# '<' forces little-endian format
packed_bytes = struct.pack("<iH", val1.value, val2.value)

print(packed_bytes)        # Output: b'\xd6\xff\xff\xff\xff\xff'
print(packed_bytes.hex())  # Output: d6ffffffffff
