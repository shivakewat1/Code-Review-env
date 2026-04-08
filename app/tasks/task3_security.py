SECURITY_CODE = '''import sqlite3
from flask import Flask, request

app = Flask(__name__)

# Hardcoded credentials
DB_PASSWORD = "admin123"
API_KEY = "sk-1234567890abcdef"


def get_user(username):
    """Fetch user from database."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result


@app.route("/eval")
def eval_code():
    """Evaluate user-provided code."""
    code = request.args.get("code", "")
    # Unsafe eval
    result = eval(code)
    return {"result": result}


@app.route("/exec")
def exec_command():
    """Execute user-provided command."""
    cmd = request.args.get("cmd", "")
    # Command injection
    import os
    os.system(cmd)
    return {"status": "executed"}


def load_config(filename):
    """Load config from file."""
    # Path traversal vulnerability
    with open(f"/app/config/{filename}", "r") as f:
        return f.read()
'''

SECURITY_TASK = {
    "task_id": "security-audit-001",
    "name": "security-audit",
    "difficulty": "hard",
    "code": SECURITY_CODE,
    "task_description": (
        "Perform a security audit on the following Python web application code. "
        "Identify all security vulnerabilities including: SQL injection, hardcoded secrets, "
        "unsafe eval/exec, command injection, and path traversal. "
        "For each vulnerability provide: line number, issue type ('security'), "
        "severity (low/medium/high/critical), description, and a secure fix suggestion."
    ),
    "known_vulnerabilities": [
        {
            "line": 7,
            "type": "hardcoded_secret",
            "severity": "high",
            "description": "Hardcoded database password in source code",
        },
        {
            "line": 8,
            "type": "hardcoded_secret",
            "severity": "critical",
            "description": "Hardcoded API key in source code",
        },
        {
            "line": 16,
            "type": "sql_injection",
            "severity": "critical",
            "description": "SQL injection vulnerability using f-string with user input",
        },
        {
            "line": 27,
            "type": "code_injection",
            "severity": "critical",
            "description": "Unsafe eval() with user-controlled input",
        },
        {
            "line": 36,
            "type": "command_injection",
            "severity": "critical",
            "description": "Command injection via os.system() with user input",
        },
        {
            "line": 43,
            "type": "path_traversal",
            "severity": "high",
            "description": "Path traversal vulnerability allowing arbitrary file access",
        },
    ],
}
