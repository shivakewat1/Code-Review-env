LINT_CODE = '''import os
import sys
import json
import re

x = 10
Y = 20
result=x+Y

def calculate(a,b):
    c = a+b
    d = a*b
    return c

def processData(data):
    for i in range(0, len(data)):
        item=data[i]
        print(item)

class myClass:
    def __init__(self):
        self.Value = 0

    def GetValue(self):
        return self.Value

    def SetValue(self,v):
        self.Value=v
'''

LINT_TASK = {
    "task_id": "lint-fix-001",
    "name": "lint-fix",
    "difficulty": "easy",
    "code": LINT_CODE,
    "task_description": (
        "Review the following Python code and identify all lint issues. "
        "Look for: unused imports, poor naming conventions (PEP8), missing spaces around operators, "
        "missing docstrings, and other style violations. "
        "For each issue provide the line number, issue type ('lint'), severity, description, and a fix suggestion."
    ),
    # Ground truth: known issues for grader reference
    "known_issues": {
        "unused_imports": [3, 4],   # json, re are unused
        "naming": [16, 21],         # processData (camelCase), myClass (not CapWords)
        "spacing": [8, 11, 12],     # result=x+Y, c = a+b (ok), missing spaces
        "missing_docstring": [10, 16, 21],
    },
}
