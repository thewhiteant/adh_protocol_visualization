import base64
import time

def rotate_left(val, r_bits, max_bits=8):
    return ((val << r_bits) & (2**max_bits - 1)) | (val >> (max_bits - r_bits))

def rotate_right(val, r_bits, max_bits=8):
    return (val >> r_bits) | ((val << (max_bits - r_bits)) & (2**max_bits - 1))

def generate_substitution_table(timestamp, mode):
    base = list(range(256))
    row = int(timestamp) % 16
    col = sum(ord(c) for c in mode[::-1]) % 16
    for i in range(256):
        swap_index = (i * row + col * 13 + timestamp) % 256
        base[i], base[swap_index] = base[swap_index], base[i]
    return base

def pad_message(msg, block_size=8):
    pad_len = block_size - (len(msg) % block_size)
    return msg + chr(pad_len) * pad_len

def unpad_message(msg):
    pad_len = ord(msg[-1])
    return msg[:-pad_len]

def feistel_round(left, right, key_byte, sub_table, round_num):
    f = (right ^ key_byte ^ sub_table[(right + round_num) % 256]) & 0xFF
    new_left = right
    new_right = left ^ f
    return new_left, new_right

def encrypt(message: str, key: str, mode: str = "base64") -> tuple:
    """Returns (ciphertext, timestamp, sub_table_preview)"""
    timestamp = int(time.time())
    sub_table = generate_substitution_table(timestamp, mode)
    padded = pad_message(message)
    encrypted_bytes = bytearray()
    for i in range(0, len(padded), 2):
        L = ord(padded[i])
        R = ord(padded[i+1]) if i+1 < len(padded) else 0
        for r in range(3):
            k = ord(key[(i + r) % len(key)])
            L, R = feistel_round(L, R, k, sub_table, r)
        encrypted_bytes.append(L)
        encrypted_bytes.append(R)
    encrypted_bytes.extend(timestamp.to_bytes(4, "big"))
    if mode == "hex":
        return encrypted_bytes.hex(), timestamp, sub_table[:16]
    else:
        return base64.b64encode(encrypted_bytes).decode(), timestamp, sub_table[:16]

def decrypt(ciphertext: str, key: str, mode: str = "base64") -> str:
    if mode == "hex":
        encrypted_bytes = bytearray.fromhex(ciphertext)
    else:
        encrypted_bytes = bytearray(base64.b64decode(ciphertext))
    timestamp = int.from_bytes(encrypted_bytes[-4:], "big")
    sub_table = generate_substitution_table(timestamp, mode)
    encrypted_bytes = encrypted_bytes[:-4]
    decrypted_chars = []
    for i in range(0, len(encrypted_bytes), 2):
        L = encrypted_bytes[i]
        R = encrypted_bytes[i+1] if i+1 < len(encrypted_bytes) else 0
        for r in reversed(range(3)):
            k = ord(key[(i + r) % len(key)])
            R, L = feistel_round(R, L, k, sub_table, r)
        decrypted_chars.append(chr(R))
        decrypted_chars.append(chr(L))
    return unpad_message(''.join(decrypted_chars))
