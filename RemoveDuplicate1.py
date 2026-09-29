# Solution 1
list_ = [9,11,1,2,3,4,4,3,5,2,6,4,7,6,4,8,9]

result = []

for number in list_ :
    if number not in result :
        result.append(number)
        
print(result)