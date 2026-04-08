from .grader1_lint import grade_lint
from .grader2_bug import grade_bug
from .grader3_security import grade_security

GRADERS = {
    "lint-fix": grade_lint,
    "bug-detect": grade_bug,
    "security-audit": grade_security,
}
