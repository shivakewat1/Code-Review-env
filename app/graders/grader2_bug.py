"""
Bug grader: checks agent-reported bugs against known ground-truth bugs.
Uses AST parsing to verify fix suggestions are syntactically valid.
Scoring:
  - Bug line correct?          +0.4 per bug (normalized)
  - Explanation valid?         +0.3 per bug (rule-based keyword check)
  - Suggested fix valid Python? +0.3 per bug (AST parse)
"""
import ast
from typing import List, Dict, Any

from app.models import Action, Reward


# Keywords that indicate a valid explanation for each known bug type
BUG_EXPLANATION_KEYWORDS = {
    6:  ["off-by-one", "range", "len", "index", "out of bounds", "overflow"],
    14: ["index", "len", "off by one", "right", "out of bounds", "indexerror"],
    26: ["=+", "+=", "assignment", "operator", "reset", "count"],
    34: ["integer", "floor", "division", "//", "float", "index", "type"],
}


def _is_valid_python(snippet: str) -> bool:
    try:
        ast.parse(snippet)
        return True
    except SyntaxError:
        return False


def _explanation_valid(description: str, line: int) -> bool:
    keywords = BUG_EXPLANATION_KEYWORDS.get(line, [])
    if not keywords:
        # Unknown line — accept any non-empty description
        return bool(description and len(description) > 10)
    desc_lower = description.lower()
    return any(kw in desc_lower for kw in keywords)


def grade_bug(action: Action, task: Dict) -> Reward:
    known_bugs = task["known_bugs"]
    known_lines = {b["line"] for b in known_bugs}

    total_bugs = len(known_bugs)
    line_score = 0.0
    explanation_score = 0.0
    fix_score = 0.0
    hallucinated = 0

    agent_lines = {issue.line for issue in action.issues}

    for issue in action.issues:
        if issue.line not in known_lines:
            hallucinated += 1
            continue

        # Line correct
        line_score += 0.4

        # Explanation valid
        if _explanation_valid(issue.description, issue.line):
            explanation_score += 0.3

        # Fix syntactically valid
        if issue.suggestion and _is_valid_python(issue.suggestion):
            fix_score += 0.3

    # Normalize by number of known bugs
    if total_bugs > 0:
        line_score = line_score / total_bugs
        explanation_score = explanation_score / total_bugs
        fix_score = fix_score / total_bugs

    # Recall bonus: reward finding more known bugs
    found_known = len(agent_lines & known_lines)
    recall = found_known / total_bugs if total_bugs > 0 else 0.0

    hallucination_penalty = min(hallucinated * 0.1, 0.3)

    raw_score = (line_score + explanation_score + fix_score) * recall - hallucination_penalty
    score = max(0.001, min(0.999, raw_score))

    breakdown = {
        "known_bugs": total_bugs,
        "bugs_found": found_known,
        "recall": round(recall, 3),
        "line_score": round(line_score, 3),
        "explanation_score": round(explanation_score, 3),
        "fix_score": round(fix_score, 3),
        "hallucinated": hallucinated,
        "hallucination_penalty": round(hallucination_penalty, 3),
    }

    feedback_parts = []
    if found_known == 0:
        feedback_parts.append("No known bugs were correctly identified.")
    elif found_known < total_bugs:
        feedback_parts.append(f"Found {found_known}/{total_bugs} known bugs.")
    else:
        feedback_parts.append("All known bugs identified.")
    if hallucinated > 0:
        feedback_parts.append(f"Hallucinated {hallucinated} non-existent bug(s).")
    if fix_score > 0:
        feedback_parts.append("Some fix suggestions were syntactically valid.")

    return Reward(
        score=round(max(0.001, min(0.999, score)), 4),
        breakdown=breakdown,
        feedback=" ".join(feedback_parts),
    )
