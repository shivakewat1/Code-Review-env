"""
server/app.py — OpenEnv-compliant entry point.
Validator requires a callable main() function here.
"""
import uvicorn
from app.main import app  # noqa: F401  re-export for import compatibility


def main():
    """Start the code-review-env FastAPI server."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=7860, reload=False)


if __name__ == "__main__":
    main()
