import hashlib
import time
from Crypto.Util.Padding import pad, unpad

class SawmerCipher:
    def rotate_left(self, value, bits):
        return ((value << bits) | (value >> (64 - bits))) & 0xFFFFFFFFFFFFFFFF

    def generate_round_keys(self):
        round_keys = []
        seed = hashlib.sha256(str(time.time()).encode()).digest()
        for i in range(16):
            round_keys.append(hashlib.sha256(seed + i.to_bytes(1, 'big')).digest())
        return round_keys

    def f_function(self, half_block, round_key):
        # Example Feistel function (you might want to change the implementation)
        return self.rotate_left(half_block, 5) ^ int.from_bytes(round_key, 'big')

    def process_block(self, block):
        left, right = block[:len(block)//2], block[len(block)//2:]
        round_keys = self.generate_round_keys()
        
        for i in range(16):
            temp = right
            right = left ^ self.f_function(int.from_bytes(right, 'big'), round_keys[i])
            left = temp
        
        return left + right

    def encrypt(self, plaintext):
        padded_plaintext = pad(plaintext, 16)
        ciphertext = self.process_block(padded_plaintext)
        return ciphertext

    def decrypt(self, ciphertext):
        left, right = ciphertext[:len(ciphertext)//2], ciphertext[len(ciphertext)//2:]
        round_keys = reversed(self.generate_round_keys())
        
        for i in range(16):
            temp = left
            left = right ^ self.f_function(int.from_bytes(left, 'big'), bytes(next(round_keys)))
            right = temp
        
        return unpad(left + right, 16)