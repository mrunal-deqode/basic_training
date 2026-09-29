# Solution 1
numbers = [10, 20, 30, 40]

numbers[0], numbers[-1] = numbers[-1], numbers[0]

print(numbers)