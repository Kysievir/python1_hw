num_a = int(input())
num_b = int(input())


if num_a % 2 == 0:
    for number in range(num_a, num_b + 1, 2):
        print(number)
else:
    for number in range(num_a + 1, num_b + 1, 2):
        print(number)