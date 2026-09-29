# Solution 2
text = input("Enter a string: ")
char = input("Enter character: ")

count = 0

for st in text :
    if st.lower() == char :
        count += 1
        
print(count)