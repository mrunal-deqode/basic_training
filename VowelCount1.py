# Solution 1
text = input("Enter String :- ")

count = 0

for char in text :
    if char.lower() in "aeiou":
        count +=1
        
print(f"total Count of Vowel in Provided String is :- {count}")