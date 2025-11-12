string = input()
letter = input()

half_len = len(string) // 2
out = string[:half_len] + letter + string[half_len:]
print(out)