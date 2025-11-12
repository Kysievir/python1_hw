input_len = int(input())
input_list = input().split(" ")

input_list = [int(number) for number in input_list]

out = "NO"
sign = input_list[0] >= 0
for idx in range(len(input_list) - 1):
    number = input_list[idx+1]
    if (number >= 0) == sign:
        out = "YES"
        break
    else:
        sign = (number >= 0)

print(out)