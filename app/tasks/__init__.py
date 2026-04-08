from .task1_lint import LINT_TASK
from .task2_bugdetect import BUG_TASK
from .task3_security import SECURITY_TASK

ALL_TASKS = {
    "lint-fix": LINT_TASK,
    "bug-detect": BUG_TASK,
    "security-audit": SECURITY_TASK,
}
