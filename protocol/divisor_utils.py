import random

# Function to perform the Miller-Rabin primality test

def is_probable_prime(n, k=5):
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0:
        return False

    # Find r such that n = 2^d * r + 1 with r odd
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1

    # Witness loop
    for _ in range(k):
        # Randomly pick a base 'a' from [2, n - 2]
        a = random.randint(2, n - 2)
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True

# Function for Pollard's Rho algorithm for integer factorization

def pollard_rho(n):
    if n % 2 == 0:
        return [2]
    x = random.randint(1, n - 1)
    y = x
    c = random.randint(1, n - 1)
    d = 1

    while d == 1:
        x = (pow(x, 2, n) + c) % n
        y = (pow(y, 2, n) + c) % n
        y = (pow(y, 2, n) + c) % n
        d = gcd(abs(x - y), n)
    if d == n:
        return []  # Failure to find a factor
    else:
        return [d] + pollard_rho(n // d)

# Function to recursively factorize a number

def _factorize(n):
    factors = []
    if is_probable_prime(n):
        return [n]
    for factor in pollard_rho(n):
        if factor:
            factors.extend(_factorize(factor))
    return factors

# Function to count the total number of divisors

def count_divisors(n):
    if n == 1:
        return 1
    count = 0
    factors = _factorize(n)
    unique_factors = set(factors)
    for factor in unique_factors:
        count += factors.count(factor) + 1
    return count

# Function to mix two divisors

def FdivisorMixer(divA, divB):
    return int(abs((divA ** divB) + divA - 100))