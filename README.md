# AI Planning & Workforce Decision Engine

A **decision-support system** that combines deterministic scenario modeling with **LLM-based reasoning** to recommend, compare, and explain workforce planning options under real-world constraints.

This project demonstrates how structured business inputs and quantitative outputs can be paired with AI reasoning to produce **auditable, executive-ready decisions**.

---

## What This Project Does

1. **Consumes authoritative scenario metrics** (e.g., FTE, cost, SLA, risk)
2. **Applies business constraints** (SLA targets, budget caps, risk limits)
3. **Runs AI reasoning** over the scenario set
4. **Produces structured recommendations** with explanations, tradeoffs, and citations
5. **Presents results in an interactive Streamlit UI**

The AI does **not invent numbers** — it reasons only over deterministic engine outputs.

---

## Key Features

- Deterministic-first design (AI never replaces math)
- Strongly typed schemas with validation (Pydantic)
- Multiple decision modes:
  - `recommend` – select the best scenario
  - `compare` – analyze tradeoffs between scenarios
  - `qa` – answer questions about the scenario set
- Audience-aware explanations (exec, ops manager, analyst)
- Constraint-aware feasibility checks
- Audit-friendly structured outputs
- Streamlit UI for interactive exploration

---

---

## Key Features

- Deterministic-first design (AI never replaces math)
- Strongly typed schemas with validation (Pydantic)
- Multiple decision modes:
  - `recommend` – select the best scenario
  - `compare` – analyze tradeoffs between scenarios
  - `qa` – answer questions about the scenario set
- Audience-aware explanations (exec, ops manager, analyst)
- Constraint-aware feasibility checks
- Audit-friendly structured outputs
- Streamlit UI for interactive exploration

---
re Data Models
DecisionContext

Defines how the AI should reason.

objective: balanced | min_cost | max_sla | risk_averse
decision_mode: recommend | compare | qa
audience: exec | ops_manager | analyst

min_sla_target: Optional[float]
max_budget_annual: Optional[float]
max_breach_risk: Optional[float]
notes: Optional[str]

scenario_id: str
name: str
fte_required: float
cost_annual: float
expected_sla: float
breach_risk: float
occupancy_peak: Optional[float]
scenario_id: str
name: str
fte_required: float
cost_annual: float
expected_sla: float
breach_risk: float
occupancy_peak: Optional[float]

Scenario

Authoritative outputs from the deterministic engine.


## Repository Structure ##

```text

├── ai/                     # AI reasoning, schemas, prompts
│   ├── schema.py           # Pydantic models (DecisionContext, Scenario, AIResponse)
│   ├── reasoning.py        # Orchestrates LLM reasoning
│   └── providers/          # LLM clients (e.g., OpenAI)
│
├── engine/                 # (Planned) deterministic scenario generation
│
├── ui/
│   ├── app.py              # Streamlit application
│   └── components/         # Reusable UI panels
│
├── config/                 # Settings and environment configuration
├── docs/                   # Architecture notes and diagrams
├── tests/                  # Unit and validation tests
├── run_decision_engine.py  # Headless (non-UI) entry point
└── requirements.txt

Core Data Models
DecisionContext

Defines how the AI should reason.
objective: balanced | min_cost | max_sla | risk_averse
decision_mode: recommend | compare | qa
audience: exec | ops_manager | analyst

min_sla_target: Optional[float]
max_budget_annual: Optional[float]
max_breach_risk: Optional[float]
notes: Optional[str]

Scenario

Authoritative outputs from the deterministic engine.
scenario_id: str
name: str
fte_required: float
cost_annual: float
expected_sla: float
breach_risk: float
occupancy_peak: Optional[float]

AIResponse

    Structured, auditable AI output.

    Recommendation (with confidence)

    Tradeoffs and comparisons

Executive summary

    Citations (which scenario metrics were used)

    Optional Q&A responses

Streamlit UI

    The Streamlit app provides:

        Sidebar controls for:

            Objective

            Decision mode

            Audience

            Constraints (SLA, budget, risk)

        Scenario table with feasibility filtering

        Baseline (manual) scenario selection

        AI-generated recommendation panel

        Side-by-side comparison (baseline vs AI pick)

        CSV and JSON export for audit or reporting

Running the App Locally
1. Install dependencies
pip install -r requirements.txt

2. Set environment variables
export OPENAI_API_KEY=your_key_here
export PYTHONPATH=$(pwd)

3. Run Streamlit
streamlit run ui/app.py

Headless Execution (No UI)

You can run the decision engine programmatically:
python run_decision_engine.py

This is useful for:

    Batch runs

    CI pipelines

    API integration

    Scheduled evaluations

Design Principles

    Math first, AI second
    The AI never fabricates metrics.
    
    Typed contracts everywhere
    All inputs and outputs are validated.
    
    Explainability over opacity
    Every recommendation includes rationale, risks, and assumptions.
    
    Enterprise realism
    Constraints, budgets, and tradeoffs are first-class concepts.

Intended Use Cases

    Workforce planning & staffing optimization
    
    Capacity planning under SLA constraints
    
    Executive decision support
    
    Scenario comparison and tradeoff analysis
    
    AI governance / explainability demos

Roadmap

    Deterministic scenario generator in engine/
    
    Multi-skill / multi-queue modeling
    
    Sensitivity analysis and rerun suggestions
    
    Scenario versioning and audit logs
    
    API service wrapper

Disclaimer

This project is for demonstration and portfolio purposes.
It does not make autonomous decisions and should not be used as-is for production staffing without domain validation.

Author

Built by a workforce analytics practitioner exploring how AI can enhance — not replace — quantitative decision-making.
