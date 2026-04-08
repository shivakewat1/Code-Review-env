"""inference.py — Runs an LLM agent through all 3 tasks of code-review-env."""
import os
import json
import time
import requests

# Validator injects these — MUST use os.environ
API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

MAX_STEPS = 8
TASKS = ["lint-fix", "bug-detect", "security-audit"]

SYSTEM_PROMPT = """You are an expert Python code reviewer. You will be given Python code and must identify issues.

Respond ONLY with a valid JSON object in this exact format:
{
  "issues": [
    {
      "line": <integer line number>,
      "issue_type": "<lint|bug|security>",
      "severity": "<info|warning|error|critical>",
      "description": "<clear explanation of the issue>",
      "suggestion": "<corrected code snippet or fix>"
    }
  ]
}

Do not include any text outside the JSON object."""


def call_llm(messages: list) -> str:
    """Call LLM proxy directly via requests — avoids OpenAI SDK URL issues."""
    url = API_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2048,
    }
    print(f"[DEBUG] LLM request to: {url}", flush=True)
    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def call_env(method: str, path: str, payload: dict = None) -> dict:
    url = f"{ENV_BASE_URL}{path}"
    try:
        if method == "POST":
            resp = requests.post(url, json=payload, timeout=60)
        else:
            resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise RuntimeError(f"ENV call failed [{method} {path}]: {e}") from e


def build_user_prompt(obs: dict) -> str:
    prompt = f"""Task: {obs['task_description']}

Code to review:
```python
{obs['code']}
```
"""
    if obs.get("previous_feedback"):
        prompt += f"\nPrevious feedback: {obs['previous_feedback']}\n"
    prompt += "\nIdentify all issues and respond with the JSON format specified."
    return prompt


def clamp(score: float) -> float:
    """Ensure score is strictly between 0 and 1."""
    return max(0.01, min(0.99, score))


def run_task(task_name: str) -> dict:
    print(f"[START] task={task_name} env=code-review-env model={MODEL_NAME}", flush=True)

    all_rewards = []
    final_score = 0.01
    total_steps = 0
    success = False

    try:
        obs = call_env("POST", f"/reset?task={task_name}")
    except Exception as e:
        err = str(e)[:120]
        print(f"[END] success=false steps=0 score=0.01 rewards=0.01 error={err}", flush=True)
        return {"task": task_name, "success": False, "steps": 0, "score": 0.01, "rewards": [0.01]}

    for step_num in range(1, MAX_STEPS + 1):
        user_prompt = build_user_prompt(obs)
        error_msg = "null"
        action_data = {"issues": []}
        action_str = "{}"

        try:
            raw_content = call_llm([
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ])
            action_data = json.loads(raw_content)
            action_str = json.dumps(action_data, separators=(",", ":"))
        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {str(e)[:80]}"
        except Exception as e:
            error_msg = str(e)[:80]
            print(f"[DEBUG] LLM call failed: {error_msg}", flush=True)

        try:
            step_result = call_env("POST", "/step", action_data)
            reward = clamp(step_result["reward"]["score"])
            done = step_result["done"]
            obs = step_result["observation"]
        except Exception as e:
            reward = 0.01
            done = True
            error_msg = str(e)[:80]

        all_rewards.append(reward)
        final_score = reward
        total_steps = step_num

        print(
            f"[STEP] step={step_num} action={action_str[:120]} "
            f"reward={reward:.2f} done={str(done).lower()} error={error_msg}",
            flush=True,
        )

        if done:
            success = reward >= 0.5
            break

    rewards_str = ",".join(f"{r:.2f}" for r in all_rewards)
    final_score = clamp(final_score)
    print(
        f"[END] success={str(success).lower()} steps={total_steps} "
        f"score={final_score:.2f} rewards={rewards_str}",
        flush=True,
    )

    return {
        "task": task_name,
        "success": success,
        "steps": total_steps,
        "score": final_score,
        "rewards": all_rewards,
    }


def main():
    print(f"[DEBUG] API_BASE_URL={API_BASE_URL}", flush=True)
    print(f"[DEBUG] MODEL={MODEL_NAME}", flush=True)

    results = []
    for task in TASKS:
        result = run_task(task)
        results.append(result)
        time.sleep(1)

    avg_score = sum(r["score"] for r in results) / len(results)
    print(f"\n=== FINAL SUMMARY ===", flush=True)
    for r in results:
        print(
            f"  {r['task']}: score={r['score']:.2f} steps={r['steps']} success={r['success']}",
            flush=True,
        )
    print(f"  average_score={avg_score:.2f}", flush=True)


if __name__ == "__main__":
    main()
