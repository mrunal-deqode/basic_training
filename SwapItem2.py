# Solution 2
numbers = [10, 20, 30, 40]

temp = numbers[0]
numbers[0] = numbers[-1]
numbers[-1] = temp

print(numbers)