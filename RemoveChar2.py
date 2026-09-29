# Solution 2
text = input("Enter a string :- ")
char = input("Enter character to be removed :- ")

result = ""

for current in text:
    if current != char:
        result += current

print(result)