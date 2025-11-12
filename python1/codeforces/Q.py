num_apple = int(input())
num_orange = int(input())
bag_1_size = int(input())
bag_2_size = int(input())

out = "NO"
if num_apple <= bag_1_size:
    if num_orange <= bag_2_size:
        out = "YES"

if num_apple <= bag_2_size:
    if num_orange <= bag_1_size:
        out = "YES"

print(out)