"""
inference.py — Runs an LLM agent through all 3 tasks of code-review-env.
Emits structured stdout logs in the required OpenEnv format.
"""
import os
import json
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://api-inference.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
HF_TOKEN = os.getenv("HF_TOKEN")
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


def get_client() -> OpenAI:
    """Create OpenAI-compatible client with full validation."""
    try:
        print(f"[DEBUG] BASE_URL={API_BASE_URL}", flush=True)
        print(f"[DEBUG] TOKEN_EXISTS={HF_TOKEN is not None}", flush=True)
        print(f"[DEBUG] MODEL={MODEL_NAME}", flush=True)

        if not API_BASE_URL:
            raise ValueError("API_BASE_URL is missing")
        if not HF_TOKEN:
            raise ValueError("HF_TOKEN is missing — set it as an environment variable")

        return OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)

    except Exception as e:
        print(f"[ERROR] Failed to create OpenAI client: {e}", flush=True)
        raise


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


def run_task(task_name: str) -> dict:
    print(f"[START] task={task_name} env=code-review-env model={MODEL_NAME}", flush=True)

    all_rewards = []
    final_score = 0.0
    total_steps = 0
    success = False

    # Reset env
    try:
        obs = call_env("POST", f"/reset?task={task_name}")
    except Exception as e:
        err = str(e)[:120]
        print(f"[END] success=false steps=0 score=0.00 rewards= error={err}", flush=True)
        return {"task": task_name, "success": False, "steps": 0, "score": 0.0, "rewards": []}

    # Init client — safe, per-task
    try:
        client = get_client()
    except Exception as e:
        err = str(e)[:120]
        print(f"[END] success=false steps=0 score=0.00 rewards= error={err}", flush=True)
        return {"task": task_name, "success": False, "steps": 0, "score": 0.0, "rewards": []}

    for step_num in range(1, MAX_STEPS + 1):
        user_prompt = build_user_prompt(obs)
        error_msg = "null"

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            raw_content = response.choices[0].message.content.strip()
            action_data = json.loads(raw_content)
            action_str = json.dumps(action_data, separators=(",", ":"))
        except json.JSONDecodeError as e:
            action_data = {"issues": []}
            action_str = "{}"
            error_msg = f"JSON parse error: {str(e)[:80]}"
        except Exception as e:
            action_data = {"issues": []}
            action_str = "{}"
            error_msg = str(e)[:80]

        try:
            step_result = call_env("POST", "/step", action_data)
            reward = step_result["reward"]["score"]
            done = step_result["done"]
            obs = step_result["observation"]
        except Exception as e:
            reward = 0.0
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
    try:
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

    except Exception as e:
        print(f"[FATAL] Unhandled exception: {e}", flush=True)
        raise


if __name__ == "__main__":
    main()
