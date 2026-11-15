# TraceLens AI

**A lightweight LLM observability and evaluation workspace.**

TraceLens AI helps developers inspect LLM application traces, review execution quality, and compare operational signals such as latency and errors. It can load local JSON/JSONL/CSV trace exports and fetch recent traces from a Langfuse project through the Langfuse Public API.

> **Project status:** Portfolio MVP. The included evaluators are transparent heuristic checks, not a substitute for human review or model-based semantic evaluation.

## Features

- **Trace Explorer:** inspect prompts, outputs, model names, status, timestamps, and latency.
- **Evaluation Studio:** run four explainable checks: non-empty output, no reported error, latency under five seconds, and reasonable output length.
- **Workspace metrics:** view pass rate, average score, average latency, error rate, model distribution, and trace volume.
- **Data import:** upload JSON arrays, JSONL, or CSV files.
- **Langfuse integration:** fetch recent traces from a Langfuse project using its Public API and HTTP Basic Authentication.
- **Local persistence:** imported traces are stored in SQLite on the machine running the app.
- **Export:** download evaluation results as CSV.

## Quick start

Requires Python 3.10 or newer.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the app
streamlit run app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`).

## Connect Langfuse

1. Open your Langfuse project and create or copy its API keys.
2. In TraceLens AI, open **Data & Integrations**.
3. Enter the Langfuse host, public key, and secret key, then select **Fetch recent traces**.

The credentials are sent only to the configured Langfuse host for the API request; they are not written to the SQLite database. Do not commit credentials or `.env` files.

The integration currently imports trace-level fields returned by the Public API. Nested observations, token/cost breakdowns, pagination beyond the first page, and organization-wide aggregation are not currently implemented.

## Input format

A JSON trace can use the following fields:

```json
{
  "id": "trace-001",
  "name": "Support answer",
  "model": "gpt-4o-mini",
  "input": "How do I reset my password?",
  "output": "Open Settings, choose Security...",
  "latency_ms": 820,
  "status": "success",
  "created_at": "2026-11-10T09:12:00Z"
}
```

CSV and JSONL imports are also supported. Unknown fields are retained in the raw trace metadata.

## Evaluation methodology

Each trace receives up to five points, based on four binary checks scaled to a five-point score:

| Check | Pass condition |
|---|---|
| Output present | Output is not empty |
| No reported error | Status is not `error`, `failed`, or `failure` |
| Latency | Latency is at most 5,000 ms |
| Output length | Output contains 20–12,000 characters |

A trace passes the overall evaluation only when all four checks pass. These checks measure basic operational hygiene; they do **not** establish factual correctness, relevance, safety, or groundedness.

## Architecture

```text
Streamlit UI
    ├── Trace Explorer
    ├── Evaluation Studio
    └── Data & Integrations
          ├── JSON / JSONL / CSV importer
          └── Langfuse Public API client
                    |
               Trace normalizer
                    |
               SQLite storage
                    |
             Evaluation engine
```

## Repository structure

```text
tracelens-ai/
├── app.py
├── tracelens/
│   ├── evaluation.py
│   ├── langfuse_client.py
│   ├── samples.py
│   └── store.py
├── .env.example
├── .gitignore
└── requirements.txt
```

## Roadmap

- Semantic quality evaluation with configurable LLM-as-a-judge.
- Dataset-based experiment runs and model comparisons.
- Token and cost analytics when observation-level data is available.
- Evaluation history and regression alerts.
- More robust Langfuse pagination and observation ingestion.
- Automated tests and deployment.

## Attribution

TraceLens AI is an independent portfolio project. It integrates with the Langfuse Public API; it does not contain or redistribute the Langfuse application source code. Langfuse is an independent open-source project: https://github.com/langfuse/langfuse.

## License

This project is released under the MIT License. The Langfuse name and trademarks belong to their respective owners.
