# Solution 1
str = input("Enter String :- ")
char = input("Enter char to be removed :- ")

result = str.replace(char,"")

print(f"String after removing character :- {result}")