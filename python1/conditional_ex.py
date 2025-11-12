x = int(input())

if x % 2 == 0:
    # print("A")
    if x % 3 != 0:
        print("B")
    else:
        print("C")
else:
    print("D")