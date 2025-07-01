def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_primes(start, end):
    primes = []
    for num in range(start, end + 1):
        if is_prime(num):
            primes.append(num)
    return primes

if __name__ == "__main__":
    primes = find_primes(1, 100)
    print("1から100までの素数:")
    for i, prime in enumerate(primes, 1):
        print(f"{prime:3d}", end=" ")
        if i % 10 == 0:
            print()
    print(f"\n\n合計: {len(primes)}個の素数")