"""
Security grader: runs bandit on the code and cross-references with known
ground-truth vulnerabilities.
Scoring per vulnerability:
  - Detected?              +0.5 (normalized)
  - Severity correct?      +0.25 (normalized)
  - Fix is valid Python?   +0.25 (normalized)
"""
import ast
import subprocess
import json
import tempfile
import os
from typing import List, Dict, Any

from app.models import Action, Reward

# Severity mapping: normalize agent severity strings to canonical levels
SEVERITY_MAP = {
    "low": 1, "medium": 2, "high": 3, "critical": 4,
    "info": 1, "warning": 2, "error": 3,
}

# Acceptable severity tolerance (within 1 level is ok)
SEVERITY_TOLERANCE = 1


def _run_bandit(code: str) -> List[Dict]:
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        tmp_path = f.name
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", "-q", tmp_path],
            capture_output=True, text=True, timeout=30
        )
        try:
            data = json.loads(result.stdout)
            return data.get("results", [])
        except json.JSONDecodeError:
            return []
    except subprocess.TimeoutExpired:
        return []
    finally:
        os.unlink(tmp_path)


def _is_valid_python(snippet: str) -> bool:
    try:
        ast.parse(snippet)
        return True
    except SyntaxError:
        return False


def _severity_correct(agent_severity: str, known_severity: str) -> bool:
    agent_level = SEVERITY_MAP.get(agent_severity.lower(), 0)
    known_level = SEVERITY_MAP.get(known_severity.lower(), 0)
    return abs(agent_level - known_level) <= SEVERITY_TOLERANCE


def grade_security(action: Action, task: Dict) -> Reward:
    known_vulns = task["known_vulnerabilities"]
    known_lines = {v["line"] for v in known_vulns}
    known_by_line = {v["line"]: v for v in known_vulns}

    # Also run bandit for additional signal
    bandit_results = _run_bandit(task["code"])
    bandit_lines = {r["line_number"] for r in bandit_results}

    # Union of known + bandit lines as "real" issues
    real_lines = known_lines | bandit_lines

    total_vulns = len(known_vulns)
    detection_score = 0.0
    severity_score = 0.0
    fix_score = 0.0
    hallucinated = 0

    agent_lines = {issue.line for issue in action.issues}

    for issue in action.issues:
        if issue.line not in real_lines:
            hallucinated += 1
            continue

        # Detection credit
        detection_score += 0.5

        # Severity credit (compare against known if available)
        if issue.line in known_by_line:
            known_sev = known_by_line[issue.line]["severity"]
            if _severity_correct(issue.severity, known_sev):
                severity_score += 0.25

        # Fix validity
        if issue.suggestion and _is_valid_python(issue.suggestion):
            fix_score += 0.25

    # Normalize by total known vulns
    if total_vulns > 0:
        detection_score = detection_score / total_vulns
        severity_score = severity_score / total_vulns
        fix_score = fix_score / total_vulns

    # Recall: fraction of known vulns found
    found_known = len(agent_lines & known_lines)
    recall = found_known / total_vulns if total_vulns > 0 else 0.0

    hallucination_penalty = min(hallucinated * 0.05, 0.2)

    raw_score = (detection_score + severity_score + fix_score) * recall - hallucination_penalty
    score = max(0.001, min(0.999, raw_score))

    breakdown = {
        "known_vulnerabilities": total_vulns,
        "vulns_found": found_known,
        "recall": round(recall, 3),
        "bandit_issues": len(bandit_lines),
        "detection_score": round(detection_score, 3),
        "severity_score": round(severity_score, 3),
        "fix_score": round(fix_score, 3),
        "hallucinated": hallucinated,
        "hallucination_penalty": round(hallucination_penalty, 3),
    }

    feedback_parts = []
    if found_known == 0:
        feedback_parts.append("No known vulnerabilities were identified.")
    elif found_known < total_vulns:
        feedback_parts.append(f"Found {found_known}/{total_vulns} known vulnerabilities.")
    else:
        feedback_parts.append("All known vulnerabilities identified.")
    if hallucinated > 0:
        feedback_parts.append(f"Hallucinated {hallucinated} non-existent issue(s).")
    if severity_score > 0:
        feedback_parts.append("Severity ratings were mostly accurate.")

    return Reward(
        score=round(score, 4),
        breakdown=breakdown,
        feedback=" ".join(feedback_parts),
    )
