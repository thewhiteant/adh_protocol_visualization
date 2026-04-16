import random
import math

class ADHProtocol:
    def __init__(self, time_ping, bitsize):
        self.time_ping = time_ping
        self.bitsize = bitsize
        self.secret = self.generate_random_secret()
        self.generator = self.generate_generator()
        self.prime_param = self.generate_prime_param()
        self.lambda_val = self.count_divisors(self.prime_param)

    def generate_random_secret(self):
        return random.getrandbits(self.bitsize)

    def generate_generator(self):
        # Simple implementation to generate a generator
        return random.randint(1, self.prime_param - 1)

    def generate_prime_param(self):
        # Using a simple prime generation method for demonstration
        return self.next_prime(random.randint(2**(self.bitsize-1), 2**self.bitsize))

    def count_divisors(self, n):
        count = 0
        for i in range(1, int(math.sqrt(n)) + 1):
            if n % i == 0:
                count += 1
                if i != n // i:
                    count += 1
        return count

    def next_prime(self, n):
        while True:
            if self.is_prime(n):
                return n
            n += 1

    def is_prime(self, n):
        if n <= 1:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True

    def get_generator(self):
        return self.generator

    def get_prime_param(self):
        return self.prime_param

    def get_lambda(self):
        return self.lambda_val

    def receive_generator(self, generator):
        self.generator = generator

    def receive_prime_param(self, prime_param):
        self.prime_param = prime_param

    def receive_lambda(self, lambda_val):
        self.lambda_val = lambda_val

    def compute_exchange_value(self, value):
        # Example implementation to compute exchange value
        return (value * self.generator) % self.prime_param

    def receive_exchange_value(self, exchange_value):
        # Placeholder implementation
        return exchange_value

    def get_debug_info(self):
        return {
            'time_ping': self.time_ping,
            'bitsize': self.bitsize,
            'secret': self.secret,
            'generator': self.generator,
            'prime_param': self.prime_param,
            'lambda_val': self.lambda_val
        }