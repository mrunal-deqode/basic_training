# Solution 2
text = input("Enter your String :- ")

reverse = ""

for char in text :
    reverse = char + reverse
    
print(reverse)