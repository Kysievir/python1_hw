input_len = int(input())
input_list = input().split(" ")
addend = int(input())

output_list = [str(int(number) + addend) for number in input_list]
print(" ".join(output_list))