#Solution 1
num = int(input(("Enter a number :- ")))

reverse = 0

while num > 0:
    digit = num % 10
    reverse = (reverse * 10) + digit
    num = int(num / 10)
    
print(reverse)