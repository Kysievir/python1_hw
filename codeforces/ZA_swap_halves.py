string = input()
half_len = len(string) // 2
new_string = string[half_len:] + string[:half_len]
print(new_string)