"""
FastAPI application for code-review-env OpenEnv-compliant RL environment.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models import Action, Observation, StepResponse, StateResponse
from app.env import get_env, TASK_ORDER

app = FastAPI(
    title="code-review-env",
    description="OpenEnv-compliant RL environment for AI code review agents",
    version="1.0.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset", response_model=Observation)
def reset(task: Optional[str] = Query(default=None, description="Task name to reset to")):
    """Reset the environment and return the initial observation."""
    if task and task not in TASK_ORDER:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task '{task}'. Valid tasks: {TASK_ORDER}",
        )
    env = get_env()
    obs = env.reset(task_name=task)
    return obs


@app.post("/step", response_model=StepResponse)
def step(action: Action):
    """Submit an action and receive the next observation, reward, and done flag."""
    env = get_env()
    response = env.step(action)
    return response


@app.get("/state", response_model=StateResponse)
def state():
    """Return the current environment state."""
    env = get_env()
    return env.get_state()
