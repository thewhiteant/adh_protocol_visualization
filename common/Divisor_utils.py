import random, math

def is_probable_prime(n, k=6):
    if n < 2: return False
    small_primes = [2,3,5,7,11,13,17,19,23,29,31]
    for p in small_primes:
        if n % p == 0:
            return n == p
    d, r = n-1, 0
    while d % 2 == 0:
        d //= 2
        r += 1
    bases = [2,3,5,7,11,13,17] if n.bit_length() <= 256 else random.sample(range(2,n-2), k)
    for a in bases:
        x = pow(a,d,n)
        if x==1 or x==n-1: continue
        for _ in range(r-1):
            x = pow(x,2,n)
            if x==n-1: break
        else:
            return False
    return True

def pollard_rho(n):
    if n%2==0: return 2
    if n%3==0: return 3
    while True:
        c = random.randrange(1,n)
        f = lambda x: (pow(x,2,n)+c)%n
        x,y,d = 2,2,1
        for _ in range(1,100000):
            x = f(x); y = f(f(y))
            d = math.gcd(abs(x-y),n)
            if d==n: break
            elif d>1: return d

def _factorize(n, factors):
    if n==1: return
    if is_probable_prime(n):
        factors.append(n); return
    d = pollard_rho(n)
    if d==n: d = pollard_rho(n+random.randint(2,10))
    if d < n//d:
        _factorize(d,factors); _factorize(n//d,factors)
    else:
        _factorize(n//d,factors); _factorize(d,factors)

def count_divisors(n: int) -> int:
    if n==1: return 1
    small_primes = [2,3,5,7,11,13,17,19,23,29,31]
    freq = {}
    for p in small_primes:
        while n%p==0:
            freq[p]=freq.get(p,0)+1; n//=p
    if n>1:
        factors=[]
        _factorize(n,factors)
        for f in factors:
            freq[f]=freq.get(f,0)+1
    result=1
    for exp in freq.values():
        result*=(exp+1)
    return result

def FdivisorMixer(divA: int, divB: int) -> int:
    return int(abs((divA ^ divB) + divA - 100))
