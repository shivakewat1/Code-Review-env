---
title: Code Review Env
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# code-review-env

An OpenEnv-compliant RL environment for training AI agents to perform Python code review. Built for the Scaler x Hugging Face OpenEnv Hackathon.

## Tasks

- lint-fix (Easy) - baseline ~0.45
- bug-detect (Medium) - baseline ~0.35
- security-audit (Hard) - baseline ~0.30

## API

- GET /health
- POST /reset
- POST /step
- GET /state

## Setup

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 7860
