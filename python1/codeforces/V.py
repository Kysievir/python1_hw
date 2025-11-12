num_inputs = int(input())

count = 0
for round in range(num_inputs):
    input_number = int(input())
    if input_number == 0: count += 1

print(count)