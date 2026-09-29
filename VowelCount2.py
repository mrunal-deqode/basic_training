# Solution 2
text = input("Enter a string: ")

count = (
    text.lower().count("a")
    + text.lower().count("e")
    + text.lower().count("i")
    + text.lower().count("o")
    + text.lower().count("u")
)

print(count)