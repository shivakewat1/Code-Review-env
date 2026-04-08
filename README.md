---
title: Code Review Env
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

<p align="center">
  <img src="https://img.shields.io/badge/OpenEnv-Compliant-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.11-green?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/FastAPI-0.111-teal?style=for-the-badge&logo=fastapi" />
  <img src="https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker" />
  <img src="https://img.shields.io/badge/HuggingFace-Space-yellow?style=for-the-badge&logo=huggingface" />
</p>

<h1 align="center">code-review-env</h1>
<p align="center">
  An OpenEnv-compliant Reinforcement Learning environment where AI agents learn to perform Python code review.<br/>
  Built for the <strong>Scaler x Hugging Face OpenEnv Hackathon</strong>.
</p>

<p align="center">
  <a href="https://huggingface.co/spaces/shiva0999/code-review-env">HuggingFace Space</a> •
  <a href="https://github.com/shivakewat1/Code-Review-env">GitHub</a> •
  <a href="https://shiva0999-code-review-env.hf.space/docs">Live API Docs</a>
</p>

---

## 👥 Team — Terminal Agents

| Name | Role |
|---|---|
| Shiva Kewat | Environment Architecture & API |
| Aayush Pandey | Graders & Reward Design |
| Roshan Kumar Singh | Tasks & Inference Pipeline |

---

## 🧠 What is this?

An AI agent is given real Python source files and must act as a code reviewer — identifying bugs, lint violations, and security vulnerabilities. For every action the agent takes, it receives a structured reward signal between `0.0` and `1.0`.

The environment is fully OpenEnv-compliant with a REST API, deterministic graders, and three progressively harder tasks.

```
Agent receives Python code
        ↓
Agent identifies issues (line, type, severity, fix)
        ↓
Grader evaluates: location accuracy + explanation + fix validity
        ↓
Reward score returned (0.0 – 1.0)
```

---

## 🔗 Links

| Resource | URL |
|---|---|
| HuggingFace Space | https://huggingface.co/spaces/shiva0999/code-review-env |
| GitHub Repo | https://github.com/shivakewat1/Code-Review-env |
| Live API | https://shiva0999-code-review-env.hf.space |
| Swagger UI | https://shiva0999-code-review-env.hf.space/docs |

---

## 🎯 Tasks

### Task 1 — lint-fix `[Easy]`
- **Input:** Python file with unused imports, bad naming (camelCase, non-CapWords), missing docstrings, spacing violations
- **Agent must:** Return list of issues with line numbers, types, and fix suggestions
- **Grader:** Runs `pylint`, computes precision/recall F1 against real pylint output
- **Baseline score:** `0.72`

### Task 2 — bug-detect `[Medium]`
- **Input:** Python file with 4 subtle logical bugs — off-by-one errors, wrong operators (`=+` vs `+=`), float division used as index, index out of bounds
- **Agent must:** Identify exact line, explain the bug, suggest corrected code
- **Grader:** AST-verified line matching + keyword-based explanation check + syntax validation of fix
- **Baseline score:** `0.54`

### Task 3 — security-audit `[Hard]`
- **Input:** Flask web app with SQL injection, hardcoded API keys, unsafe `eval()`, command injection via `os.system()`, path traversal
- **Agent must:** List all vulnerabilities with severity (`low/medium/high/critical`) and secure fix
- **Grader:** `bandit` static analysis + ground-truth cross-reference + severity tolerance check
- **Baseline score:** `0.38`

---

## 🏆 Reward Function

| Event | Score Delta |
|---|---|
| Correct line identified | +0.4 |
| Correct issue type | +0.3 |
| Valid fix suggestion (AST-verified) | +0.3 |
| Hallucinated non-existent issue | -0.1 |

> All scores are deterministically clamped to `[0.0, 1.0]`. No randomness.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok"}` |
| `POST` | `/reset` | Reset env, returns initial Observation |
| `POST` | `/step` | Submit Action, returns Reward + next Observation |
| `GET` | `/state` | Current task, step count, cumulative reward |
| `GET` | `/docs` | Swagger UI |

### Example: Reset to a task
```bash
curl -X POST "https://shiva0999-code-review-env.hf.space/reset?task=bug-detect"
```

### Example: Submit an action
```bash
curl -X POST "https://shiva0999-code-review-env.hf.space/step" \
  -H "Content-Type: application/json" \
  -d '{
    "issues": [
      {
        "line": 6,
        "issue_type": "bug",
        "severity": "error",
        "description": "Off-by-one error: range goes out of bounds",
        "suggestion": "for i in range(1, len(numbers)):"
      }
    ]
  }'
```

### Example Response
```json
{
  "observation": { "task_id": "bug-detect-001", "step_count": 1, ... },
  "reward": {
    "score": 0.72,
    "breakdown": { "line_score": 0.4, "explanation_score": 0.3, "fix_score": 0.3 },
    "feedback": "Found 2/4 known bugs. Fix suggestions were syntactically valid."
  },
  "done": false,
  "info": { "cumulative_reward": 0.72 }
}
```

---

## 🗂️ Observation & Action Space

### Observation
```python
class Observation(BaseModel):
    task_id: str
    code: str
    language: str = "python"
    task_description: str
    step_count: int
    previous_feedback: Optional[str]
```

### Action
```python
class Action(BaseModel):
    issues: List[Issue]

class Issue(BaseModel):
    line: int
    issue_type: str   # "lint" | "bug" | "security"
    severity: str     # "info" | "warning" | "error" | "critical"
    description: str
    suggestion: str
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| API Framework | FastAPI + Uvicorn |
| Data Validation | Pydantic v2 |
| Lint Grader | Pylint |
| Security Grader | Bandit |
| Bug Grader | AST parsing (stdlib) |
| LLM Client | OpenAI SDK (HF Router) |
| Containerization | Docker |
| Deployment | HuggingFace Spaces |

---

## 🚀 Run Locally

```bash
git clone https://github.com/shivakewat1/Code-Review-env
cd Code-Review-env
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

Open http://localhost:7860/docs for the Swagger UI.

---

## 🐳 Run with Docker

```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

---

## 🤖 Run Inference (LLM Agent)

```bash
set HF_TOKEN=your_hf_token_here
set ENV_BASE_URL=https://shiva0999-code-review-env.hf.space
python inference.py
```

The agent uses `Qwen/Qwen2.5-72B-Instruct` via the HuggingFace router by default. Override with:
```bash
set MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
```

Expected output format:
```
[START] task=lint-fix env=code-review-env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action={...} reward=0.72 done=false error=null
[END] success=true steps=3 score=0.72 rewards=0.72,0.80,0.85
```

---

## 📊 Baseline Results

| Task | Difficulty | Model | Score | Steps |
|---|---|---|---|---|
| lint-fix | Easy | Qwen2.5-72B | 0.72 | 3 |
| bug-detect | Medium | Qwen2.5-72B | 0.54 | 5 |
| security-audit | Hard | Qwen2.5-72B | 0.38 | 6 |

---

## ⚙️ Environment Constraints

- Runs on 2 vCPU, 8GB RAM
- All graders are fully deterministic (no randomness)
- Scores always in `[0.0, 1.0]`
- `reset()` always returns a clean state
- All task code samples are hardcoded — no external APIs needed for the environment itself
- Max 8 steps per task, total inference runtime under 20 minutes

---

## 📁 Project Structure

```
code-review-env/
├── Dockerfile
├── openenv.yaml
├── pyproject.toml
├── requirements.txt
├── inference.py
├── server/
│   └── app.py          # OpenEnv entry point with main()
└── app/
    ├── main.py         # FastAPI routes
    ├── env.py          # Core RL environment logic
    ├── models.py       # Pydantic models
    ├── tasks/
    │   ├── task1_lint.py
    │   ├── task2_bugdetect.py
    │   └── task3_security.py
    └── graders/
        ├── grader1_lint.py
        ├── grader2_bug.py
        └── grader3_security.py
```

---

<p align="center">Built with dedication by <strong>Team Terminal Agents</strong> for the Scaler x HuggingFace OpenEnv Hackathon</p>
