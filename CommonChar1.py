# Solution 1
text1 = input("Enter first string ;- ")
text2 = input("Enter second string :- ")

common = []

for char in text1:
    if char in text2 and char not in common:
        common.append(char)

print(common)