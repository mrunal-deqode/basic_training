list1 = [1, 2, 3, 4, 5, 6, 7]
list2 = [1, 2, 3, 5]

result = []

for number in list1 :
    if number not in list2 :
        result.append(number)
        
print(result)