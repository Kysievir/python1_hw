input_len = int(input())
input_list = input().split()

output_list = [number for number in input_list if int(number) % 2 == 0]
print(" ".join(output_list))