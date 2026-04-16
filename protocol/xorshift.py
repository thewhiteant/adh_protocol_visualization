import os

class XorShift32:
    def __init__(self, seed=None):
        if seed is None:
            seed = os.urandom(4)
        self.state = int.from_bytes(seed, 'little')

    def next(self):
        self.state ^= (self.state << 13) & 0xFFFFFFFF
        self.state ^= (self.state >> 17) & 0xFFFFFFFF
        self.state ^= (self.state << 5) & 0xFFFFFFFF
        return self.state & 0xFFFFFFFF

    def rand_int(self, min_value, max_value):
        return min_value + self.next() % (max_value - min_value + 1)

    def rand_bytes(self, n):
        return bytes(self.next() & 0xFF for _ in range(n))

    @staticmethod
    def Beta(prng):
        return int.from_bytes(prng.rand_bytes(8), 'little')
