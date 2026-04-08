"""
Core RL environment logic for code-review-env.
Manages state, step transitions, and reward accumulation.
"""
from typing import Optional, Dict, Any

from app.models import Action, Observation, Reward, StepResponse, StateResponse
from app.tasks import ALL_TASKS
from app.graders import GRADERS

MAX_STEPS = 8
TASK_ORDER = ["lint-fix", "bug-detect", "security-audit"]


class CodeReviewEnv:
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self.reset()

    def reset(self, task_name: Optional[str] = None) -> Observation:
        """Reset environment to initial state. Defaults to first task."""
        target_task = task_name or TASK_ORDER[0]
        task = ALL_TASKS[target_task]

        self._state = {
            "task_name": target_task,
            "task": task,
            "step_count": 0,
            "total_reward": 0.0,
            "done": False,
            "previous_feedback": None,
            "rewards_history": [],
        }

        return self._build_observation()

    def step(self, action: Action) -> StepResponse:
        """Process one agent action and return next observation + reward."""
        if self._state["done"]:
            obs = self._build_observation()
            reward = Reward(score=0.001, breakdown={}, feedback="Episode already done.")
            return StepResponse(observation=obs, reward=reward, done=True, info={})

        task = self._state["task"]
        task_name = self._state["task_name"]
        grader = GRADERS[task_name]

        reward = grader(action, task)

        self._state["step_count"] += 1
        self._state["total_reward"] += reward.score
        self._state["previous_feedback"] = reward.feedback
        self._state["rewards_history"].append(reward.score)

        done = (
            self._state["step_count"] >= MAX_STEPS
            or reward.score >= 0.95  # early termination on near-perfect score
        )
        self._state["done"] = done

        obs = self._build_observation()
        info = {
            "task_name": task_name,
            "step": self._state["step_count"],
            "cumulative_reward": round(self._state["total_reward"], 4),
        }

        return StepResponse(observation=obs, reward=reward, done=done, info=info)

    def get_state(self) -> StateResponse:
        return StateResponse(
            task_id=self._state["task"]["task_id"],
            step_count=self._state["step_count"],
            total_reward=round(self._state["total_reward"], 4),
            done=self._state["done"],
            current_task=self._state["task_name"],
        )

    def _build_observation(self) -> Observation:
        task = self._state["task"]
        return Observation(
            task_id=task["task_id"],
            code=task["code"],
            language="python",
            task_description=task["task_description"],
            step_count=self._state["step_count"],
            previous_feedback=self._state.get("previous_feedback"),
        )


# Singleton environment instance
_env_instance: Optional[CodeReviewEnv] = None


def get_env() -> CodeReviewEnv:
    global _env_instance
    if _env_instance is None:
        _env_instance = CodeReviewEnv()
    return _env_instance
