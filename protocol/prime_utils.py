def is_prime_wheel(n):
    """Determine if the number n is prime using wheel factorization."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def next_prime_wheel(n):
    """Find the next prime number after n."""
    prime = n + 1
    while not is_prime_wheel(prime):
        prime += 1
    return prime

def PrimeFun(pa, pb):
    """Compute res = pa ^ pb and return next_prime_wheel(res)."""
    res = pa ** pb
    return next_prime_wheel(res)