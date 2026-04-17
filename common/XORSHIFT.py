class XorShift32:
    def __init__(self, seed: int):
        if seed == 0:
            seed = 0x12345678
        self.state = seed & 0xFFFFFFFF

    def next(self) -> int:
        x = self.state
        x ^= (x << 16) & 0xFFFFFFFF
        x ^= (x >> 29) & 0xFFFFFFFF
        x ^= (x << 7) & 0xFFFFFFFF
        self.state = x
        return x & 0xFFFFFFFF

    def rand_bytes(self, n: int) -> bytes:
        out = bytearray()
        while len(out) < n:
            out += self.next().to_bytes(4, 'little')
        return bytes(out[:n])


def Beta(seed: str) -> int:
    seed = int(seed)
    prng = XorShift32(seed)
    return int.from_bytes(prng.rand_bytes(8), 'little')
