BUG_CODE = '''def find_max(numbers):
    """Find the maximum value in a list."""
    if len(numbers) == 0:
        return None
    max_val = numbers[0]
    for i in range(1, len(numbers) + 1):  # off-by-one: should be len(numbers)
        if numbers[i] > max_val:
            max_val = numbers[i]
    return max_val


def is_palindrome(s):
    """Check if a string is a palindrome."""
    s = s.lower().strip()
    left, right = 0, len(s)  # bug: right should be len(s) - 1
    while left < right:
        if s[left] != s[right]:  # IndexError when right == len(s)
            return False
        left += 1
        right -= 1
    return True


def count_occurrences(lst, target):
    """Count how many times target appears in lst."""
    count = 0
    for i in range(len(lst)):
        if lst[i] == target:
            count =+ 1  # bug: should be count += 1, not count =+ 1
    return count


def binary_search(arr, target):
    """Binary search — returns index or -1."""
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) / 2  # bug: should use // for integer division
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
'''

BUG_TASK = {
    "task_id": "bug-detect-001",
    "name": "bug-detect",
    "difficulty": "medium",
    "code": BUG_CODE,
    "task_description": (
        "Review the following Python code and identify all logical bugs. "
        "For each bug provide: the exact line number, issue type ('bug'), severity, "
        "a clear explanation of why it is a bug, and a corrected code suggestion. "
        "Focus on off-by-one errors, wrong operators, type issues, and index errors."
    ),
    "known_bugs": [
        {
            "line": 6,
            "description": "Off-by-one error: range should be range(1, len(numbers)) not range(1, len(numbers)+1)",
            "fix": "for i in range(1, len(numbers)):",
        },
        {
            "line": 14,
            "description": "right should be len(s) - 1 to avoid IndexError on s[right]",
            "fix": "left, right = 0, len(s) - 1",
        },
        {
            "line": 26,
            "description": "count =+ 1 resets count to +1 each time; should be count += 1",
            "fix": "count += 1",
        },
        {
            "line": 34,
            "description": "Integer division required for mid index; / returns float causing TypeError on arr[mid]",
            "fix": "mid = (low + high) // 2",
        },
    ],
}
