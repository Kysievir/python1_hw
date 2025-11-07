list_len = int(input())
input_list = input().split(" ")

output_str = " ".join(input_list[::2])
print(output_str)