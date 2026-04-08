# code-review-env

An OpenEnv-compliant RL environment for training AI agents to perform Python code review.
Built for the Scaler x Hugging Face OpenEnv Hackathon.

## Environment Description

An AI agent receives Python source files and must identify issues — lint violations, logical bugs,
and security vulnerabilities — with line-level precision, correct severity ratings, and valid fix suggestions.

## Observation Space

```json
{
  "task_id": "string",
  "code": "string",
  "language": "python",
  "task_description": "string",
  "step_count": "integer",
  "previous_feedback": "string | null"
}
```

## Action Space

```json
{
  "issues": [
    {
      "line": "integer",
      "issue_type": "lint | bug | security",
      "severity": "info | warning | error | critical",
      "description": "string",
      "suggestion": "string"
    }
  ]
}
```

## Tasks

### Task 1 — lint-fix (Easy)
Input: Python file with unused imports, naming violations, missing docstrings, spacing issues.
Grader: Runs pylint, computes precision/recall F1 against pylint output.
Baseline score: ~0.45

### Task 2 — bug-detect (Medium)
Input: Python file with 4 logical bugs (off-by-one, wrong operator, index error, float division).
Grader: AST-verified line matching + keyword explanation check + syntax-valid fix check.
Scoring: line correct +0.4, explanation valid +0.3, fix valid Python +0.3 (per bug, normalized).
Baseline score: ~0.35

### Task 3 — security-audit (Hard)
Input: Flask web app with SQL injection, hardcoded secrets, unsafe eval, command injection, path traversal.
Grader: Bandit + ground-truth cross-reference; severity tolerance +/-1 level.
Scoring: detected +0.5, severity correct +0.25, fix valid Python +0.25 (per vuln, normalized).
Baseline score: ~0.30

## Reward Function

- File successfully parsed: +0.1
- Correct issue location identified: +0.2
- Correct issue type identified: +0.3
- Valid suggestion given: +0.2
- Suggestion passes static verification: +0.2
- Hallucinated non-existent issue: -0.1
- Suggestion breaks syntax: -0.2

All scores clamped to [0.0, 1.0].

## API Endpoints

- GET  /health  -> {"status": "ok"}
- POST /reset   -> returns initial Observation (optional ?task= query param)
- POST /step    -> takes Action, returns Observation + Reward + done + info
- GET  /state   -> returns current environment state

## Setup — Local

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860

# In another terminal
export HF_TOKEN=your_token_here
python inference.py
```

## Setup — Docker

```bash
docker build -t code-review-env .
docker run -p 7860:7860 -e HF_TOKEN=your_token code-review-env
```

## HuggingFace Space Deployment

1. Create a new Space, select Docker SDK
2. Push this repo:

```bash
git remote add space https://huggingface.co/spaces/<username>/code-review-env
git push space main
```

3. Add HF_TOKEN as a Space secret in Settings -> Variables and Secrets

## Baseline Scores

| Task           | Difficulty | Baseline |
|----------------|------------|----------|
| lint-fix       | Easy       | 0.45     |
| bug-detect     | Medium     | 0.35     |
| security-audit | Hard       | 0.30     |

## Constraints

- Runs on 2 vCPU, 8GB RAM
- All graders are deterministic
- Scores always in [0.0, 1.0]
- reset() always returns a clean state
- Task code samples are hardcoded — no external APIs needed for the environment
- Max 8 steps per task, total inference under 20 minutes
