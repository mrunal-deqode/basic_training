# Python Programming Practice

This document contains my preferred solutions for each programming problem.
For each question, I compared two possible approaches and selected the one I consider better based on readability, logic, portability, and understanding.
*File Name* :- `Represent File name which is i prefer as a solution of a particular problem`
---

## Q1. Write a program to reverse a number.

### Preferred Solution: Solution 1

I prefer **Solution 1** because it uses basic arithmetic operations to reverse the number. Although Solution 2 is shorter, Solution 1 is better for human understanding because it demonstrates how the digits of a number can be manipulated.

Another advantage is that the arithmetic approach can be implemented in almost any programming language, while converting the number to a string and using string operations may not always be the preferred approach.

**File Name** :- `ReverseNumber1.py`

---

## Q2. Write a program to reverse a string.

### Preferred Solution: Solution 2

I prefer **Solution 2** because it uses a loop to reverse the string and helps understand the basic logic behind string manipulation.

Although Python provides a shorter solution using slicing, the loop-based approach gives a better understanding of how strings can be processed character by character.

**File Name** :- `ReverseString2.py`

---

## Q3. Write a program to reverse a list.

### Preferred Solution: Solution 2

I prefer **Solution 2** because it uses Python's built-in `reverse()` method.

The `reverse()` method is specifically designed to reverse a list, making the solution simple and readable.

**File Name** :- `ReverseList2.py`

---

## Q4. Write a program to count the number of vowels in a string.

### Preferred Solution: Solution 1

I prefer **Solution 1** because it uses basic programming logic instead of relying completely on the built-in `count()` method.

By traversing the string and checking each character, we understand how the counting process actually works.

**File Name** :- `VowelCount1.py`

---

## Q5. Write a program to remove a given character from a string.

### Preferred Solution: Solution 1

I prefer **Solution 1** because it uses Python's built-in `replace()` method, which is specifically designed for replacing or removing characters from a string.

Solution 2 is also useful for understanding the basic logic, but the built-in method provides a simpler and more readable solution for this particular problem.

**File Name** :- `RevomeChar1.py`

---

## Q6. Write a program to count occurrences of a given character in a string.

### Preferred Solution: Solution 2

I prefer **Solution 2** because it uses Python's built-in `count()` method.

It is a simple and readable way to count how many times a character occurs in a string.

Solution 1 is also useful because it helps understand the basic logic behind counting occurrences by traversing the string.

**File Name** :- `CountOccurence2.py`

---

## Q7. Write a program to remove duplicates from a list.

### Preferred Solution: Solution 2

I prefer **Solution 2** because it uses a `set`, which automatically removes duplicate values.

It provides a short and efficient solution for removing duplicates.

Solution 1 is also useful for understanding the underlying logic because it manually checks whether an item has already been added to the result.

**File Name** :- `RemoveDuplicate2.py`

---

## Q8. Write a program to find which number is not present in the second list.

### Preferred Solution: Solution 2

I prefer **Solution 2** because it uses sets to find the difference between the two lists.

Set difference provides a direct way to identify elements that exist in the first list but not in the second list.

Solution 1 is also useful because it uses a normal loop to traverse the list and check whether each element exists in the second list.

**File Name** :- `FindNumberinList2.py`

---

## Q9. Write a program to swap the first and last item of a list.

### Preferred Solution: Solution 2

I prefer **Solution 2** because it uses an additional temporary variable to perform the swap.

Although it requires an extra variable, the logic is simple and can be applied to almost any programming language.

Solution 1 uses Python's multiple assignment feature, which is shorter but multiple assignment is not supported in the same way by many other programming languages.

**File Name** :- `SwapItem2.py`

---

## Q10. Write a program to check common characters in two given strings.

### Preferred Solution: Solution 1

I prefer **Solution 1** because it uses a basic loop to traverse the characters and check whether they are present in both strings.

Solution 2, using sets, is also a good approach and can be more efficient for larger collections. However, for small strings, I prefer the loop-based approach because it makes the underlying logic easier to understand.

**File Name** :- `CommonChar1.py`

---

## Conclusion

While built-in Python methods and data structures often provide shorter and more efficient solutions, basic implementations are also important because they help build a strong understanding of programming logic.

My preference is therefore based not only on the shortest solution, but also on:

* Understanding the underlying logic
* Readability
* Simplicity
* Portability across programming languages
* Appropriate use of Python's built-in features
