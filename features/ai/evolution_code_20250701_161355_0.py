def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


primes = [n for n in range(1, 101) if is_prime(n)]
print("Prime numbers from 1 to 100:")
for i, prime in enumerate(primes, 1):
    print(f"{prime:3d}", end=" ")
    if i % 10 == 0:
        print()
print(f"\n\nTotal count: {len(primes)}")
