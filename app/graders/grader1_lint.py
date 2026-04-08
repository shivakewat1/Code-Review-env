"""
Lint grader: runs pylint on the submitted code and compares agent-reported
issues against pylint findings using precision/recall.
"""
import ast
import subprocess
import json
import tempfile
import os
from typing import List, Dict, Any

from app.models import Action, Reward


def _run_pylint(code: str) -> List[Dict]:
    """Run pylint on code string, return list of issue dicts."""
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["pylint", tmp_path, "--output-format=json", "--disable=all",
             "--enable=C,W,E,R"],
            capture_output=True, text=True, timeout=30
        )
        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            issues = []
        return issues
    except subprocess.TimeoutExpired:
        return []
    finally:
        os.unlink(tmp_path)


def _is_valid_python(code_snippet: str) -> bool:
    """Check if a code snippet is syntactically valid Python."""
    try:
        ast.parse(code_snippet)
        return True
    except SyntaxError:
        return False


def grade_lint(action: Action, task: Dict) -> Reward:
    code = task["code"]
    pylint_issues = _run_pylint(code)
    pylint_lines = {issue["line"] for issue in pylint_issues}

    agent_lines = {issue.line for issue in action.issues}

    # Precision: how many agent-reported lines are real issues
    if agent_lines:
        true_positives = len(agent_lines & pylint_lines)
        precision = true_positives / len(agent_lines)
    else:
        precision = 0.0

    # Recall: how many real issues the agent found
    if pylint_lines:
        true_positives = len(agent_lines & pylint_lines)
        recall = true_positives / len(pylint_lines)
    else:
        recall = 1.0  # no issues to find, full recall

    # F1 score as base
    if precision + recall > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = 0.0

    # Bonus: valid suggestions
    valid_suggestions = sum(
        1 for issue in action.issues
        if issue.suggestion and _is_valid_python(issue.suggestion)
    )
    suggestion_bonus = (valid_suggestions / max(len(action.issues), 1)) * 0.1

    # Penalty: hallucinated issues (lines not in pylint output)
    hallucinated = len(agent_lines - pylint_lines)
    hallucination_penalty = min(hallucinated * 0.05, 0.2)

    raw_score = f1 * 0.9 + suggestion_bonus - hallucination_penalty
    score = max(0.001, min(0.999, raw_score))

    breakdown = {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "pylint_issue_count": len(pylint_lines),
        "agent_issue_count": len(agent_lines),
        "true_positives": len(agent_lines & pylint_lines),
        "hallucinated": hallucinated,
        "valid_suggestions": valid_suggestions,
        "suggestion_bonus": round(suggestion_bonus, 3),
        "hallucination_penalty": round(hallucination_penalty, 3),
    }

    feedback_parts = []
    if precision < 0.5:
        feedback_parts.append("Many reported issues were not real lint violations.")
    if recall < 0.5:
        feedback_parts.append("Missed many actual lint issues.")
    if hallucinated > 0:
        feedback_parts.append(f"Hallucinated {hallucinated} non-existent issue(s).")
    if valid_suggestions > 0:
        feedback_parts.append(f"{valid_suggestions} suggestion(s) were syntactically valid.")
    if not feedback_parts:
        feedback_parts.append("Good job identifying lint issues.")

    return Reward(
        score=round(score, 4),
        breakdown=breakdown,
        feedback=" ".join(feedback_parts),
    )
