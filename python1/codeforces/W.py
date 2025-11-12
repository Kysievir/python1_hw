num_heroes = int(input())
heroes = set(range(1, num_heroes + 1))
for round in range(num_heroes - 1):
    heroes.remove(int(input()))

print(heroes.pop())