string = input()
is_palindrome = string[::-1] == string

if is_palindrome:
    print("YES")
else:
    print("NO")