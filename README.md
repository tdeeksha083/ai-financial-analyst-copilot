# AI Financial Analyst Copilot

A small portfolio project built with Python, Streamlit, pandas, Plotly, and an optional OpenAI-compatible LLM API. It combines deterministic financial calculations with an evidence-grounded natural-language Q&A interface.

## Features

- Upload monthly financial statements as CSV, with validation and row-specific error messages.
- Included synthetic monthly dataset for a demo without real company data.
- Python-calculated revenue growth, gross profit, gross margin, EBITDA proxy, operating-expense growth, and revenue/expense budget variances.
- KPI cards, trend charts, monthly results table, and downloadable calculated results.
- Optional LLM Q&A grounded in calculated metrics and up to 36 recent source rows.
- API keys read from environment variables; no secrets are included in source code.
- Privacy warning and limitations guidance.

## Requirements

- Python 3.10 or newer
- An API key for the optional LLM feature. The dashboard and calculations work without one.

## Run locally

```bash
# 1. Open this project directory
cd ai_financial_analyst_copilot

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 3. Install packages
python -m pip install -r requirements.txt

# 4. Start the dashboard
streamlit run app.py
```

The app opens in your browser and defaults to the included synthetic sample data. Upload your own CSV to replace it.

## Configure the LLM

Set `OPENAI_API_KEY` in your shell environment. Optionally set `OPENAI_MODEL` (defaults to `gpt-4.1-mini`).

Windows PowerShell for the current terminal session:

```powershell
$env:OPENAI_API_KEY="your-real-key"
$env:OPENAI_MODEL="gpt-4.1-mini"
streamlit run app.py
```

macOS/Linux for the current terminal session:

```bash
export OPENAI_API_KEY="your-real-key"
export OPENAI_MODEL="gpt-4.1-mini"
streamlit run app.py
```

You may copy `.env.example` to `.env` for your own local workflow, but this app intentionally does not automatically load `.env`; export variables in your shell or use a trusted secret manager. Do not commit `.env`, paste keys into source code, or share keys in screenshots. If using Streamlit Community Cloud, configure secrets in the app's deployment settings and adjust the code to read from `st.secrets` only if you intentionally choose that deployment pattern.

## CSV schema

Required columns (case-insensitive; surrounding spaces are trimmed):

| Column | Meaning |
|---|---|
| `month` | A parseable month/date, e.g. `2025-01` |
| `revenue` | Actual revenue |
| `cogs` | Cost of goods/services sold |
| `operating_expenses` | Operating expenses excluding COGS |
| `budget_revenue` | Revenue budget |
| `budget_expenses` | Operating-expense budget |

Use one row per month, numeric non-negative values, and consistent currency/units. The app rejects duplicate months, missing columns, invalid dates, and missing/non-numeric/negative financial values. If your source uses negative expenses or a different accounting convention, normalize it deliberately before upload.

## Calculation definitions

- Gross profit = revenue − COGS
- Gross margin % = gross profit ÷ revenue × 100
- EBITDA proxy = revenue − COGS − operating expenses
- Revenue growth % = (current revenue ÷ previous revenue − 1) × 100
- Expense growth % = (current operating expenses ÷ previous operating expenses − 1) × 100
- Revenue budget variance = actual revenue − budget revenue
- Expense budget variance = actual operating expenses − budget expenses
- Variance % = variance ÷ corresponding budget × 100

A positive revenue variance means revenue is above budget. A positive expense variance means overspend. Growth and margin percentages can be undefined if the denominator is zero; the first month's growth is unavailable.

## Grounding and limitations

The LLM receives a bounded evidence package containing computed metrics and uploaded source values. Its instructions require it to name periods, cite metrics, distinguish interpretation from fact, and admit when evidence is insufficient. This is a prompt-based safeguard, not a formal guarantee: models can still produce incorrect statements. Verify important conclusions against the displayed table and original source data. The app does not use the LLM for arithmetic.

EBITDA is labeled a **proxy** because the input schema may not capture every adjustment required by your accounting policy. This is a portfolio demo, not audited financial reporting or investment advice.

## Privacy and deployment

Do not upload confidential or personally identifiable data without approval. When you ask an AI question, the selected financial evidence and your question are sent to the configured API provider. Review provider retention and data-use terms, your organisation's policies, and the hosting environment's logging/caching behavior. The app itself does not intentionally persist uploaded data to a database.

## Verification status

This README describes the intended setup. Do not describe the project as fully tested unless you have run it in your own environment and verified the dashboard and LLM flow with valid and invalid files.
