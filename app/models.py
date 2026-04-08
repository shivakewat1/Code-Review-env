from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Issue(BaseModel):
    line: int
    issue_type: str  # "lint" | "bug" | "security"
    severity: str    # "info" | "warning" | "error" | "critical"
    description: str
    suggestion: str


class Action(BaseModel):
    issues: List[Issue]


class Observation(BaseModel):
    task_id: str
    code: str
    language: str = "python"
    task_description: str
    step_count: int
    previous_feedback: Optional[str] = None


class Reward(BaseModel):
    score: float = Field(gt=0.0, lt=1.0)
    breakdown: Dict[str, Any]
    feedback: str


class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]


class StateResponse(BaseModel):
    task_id: str
    step_count: int
    total_reward: float
    done: bool
    current_task: str
