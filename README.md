AI Planning Decision Engine

A headless decision-intelligence engine that combines deterministic workforce planning outputs with a validated AI reasoning layer to produce executive-ready recommendations.

This project is intentionally designed to:

Separate math from narrative

Enforce strict schema validation on AI output

Run with or without external AI access

Be testable, explainable, and production-oriented

    # Architecture Overview

    ├── engine/          # Deterministic workforce planning logic
    │   ├── forecasting.py
    │   ├── staffing.py
    │   └── scenarios.py
    │
    ├── ai/              # AI reasoning + validation layer
    │   ├── schema.py    # Pydantic models (authoritative contract)
    │   ├── prompts.py   # System + user prompt construction
    │   ├── reasoning.py # Orchestration, validation, retries, fallback
    │   └── providers/
    │       └── openai_client.py
    │
    ├── config/          # Centralized settings (.env via pydantic-settings)
    │   └── settings.py
    │
    ├── tests/           # Pytest suite (no external calls)
    │
    ├── run_decision_engine.py  # Primary execution entrypoint
    ├── requirements.txt
    ├── requirements-dev.txt
    └── .env.example     # Template only (no secrets)

Core Design Principles
1. Deterministic First

All staffing, cost, SLA, and risk metrics are produced by deterministic engine logic (engine/).
The AI never computes new numbers.

2. AI as a Reasoning Layer

The AI layer:

Interprets scenario outputs

Compares tradeoffs

Produces grounded, executive-style recommendations

Must conform to a strict JSON schema

If output is invalid → it is rejected and corrected.

3. Strict Validation

All AI output is validated against Pydantic models:

No free-form text

No schema drift

No hallucinated metrics

Invalid responses trigger a correction retry or graceful fallback.

4. External Dependency Isolation

The system runs in three modes:

OpenAI provider (when quota/billing available)

DummyLLM fallback (no external access required)

Fully testable offline (pytest)

Execution
1. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

2. Configure environment

Create a local .env (not committed):

OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
APP_ENV=local
LOG_LEVEL=INFO
AI_PROVIDER=openai   # or "dummy"


.env is ignored by git.
Use .env.example as a template only.

3. Run the engine (headless)
python run_decision_engine.py


Behavior:

Generates workforce scenarios via engine/

Invokes AI reasoning

Validates the response

Falls back to DummyLLM if OpenAI is unavailable

Prints an executive summary and recommendation

Testing

All tests are offline and deterministic.

pip install -r requirements-dev.txt
pytest


Test coverage includes:

Scenario generation sanity checks

Staffing math validation

Occupancy and risk bounds

AI schema validation using DummyLLM

End-to-end reasoning without external APIs

AI Output Contract

AI output must conform to the AIResponse schema:

Executive summary

Grounded recommendation

Explicit tradeoffs (structured objects, not prose)

Scenario-level citations

Any deviation:

Fails validation

Triggers a correction prompt

Or falls back safely

This guarantees:

Explainability

Auditability

Deterministic inputs → controlled narrative outputs

Why This Matters

This project demonstrates:

Decision intelligence, not prompt engineering

Production-grade AI integration

Separation of concerns

Failure-tolerant design

Test-first thinking

It is intentionally not a UI demo and not a notebook experiment.

Future Extensions (Intentional, Not Required)

Replace proxy SLA logic with Erlang-C / interval SL

Add FastAPI or CLI interface

Add scenario sensitivity analysis (AHT ±%, volume shocks)

Persist decisions for audit trails

Add structured logging

License / Usage

This project is intended for demonstration and portfolio use.
Secrets are never committed. External services are optional.
