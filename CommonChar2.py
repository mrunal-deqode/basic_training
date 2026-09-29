# Solution 2
text1 = input("Enter first string: ")
text2 = input("Enter second string: ")

common = set(text1) & set(text2)

print(common)