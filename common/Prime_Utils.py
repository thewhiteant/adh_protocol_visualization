def is_prime_wheel(n):
    if n<2: return False
    if n in (2,3,5): return True
    if n%2==0 or n%3==0 or n%5==0: return False
    increments=[6,4,2,4,2,4,6,2]
    i,idx=7,0
    while i*i<=n:
        if n%i==0: return False
        i+=increments[idx]; idx=(idx+1)%len(increments)
    return True

def next_prime_wheel(n):
    candidate = n+1 if n%2==0 else n+2
    while not is_prime_wheel(candidate):
        candidate+=2
    return candidate

def PrimeFun(pa, pb):
    res = pa ^ pb
    return next_prime_wheel(res)
