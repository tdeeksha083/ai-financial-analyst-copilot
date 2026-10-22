import os
from io import StringIO

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="AI Financial Analyst Copilot", page_icon="📊", layout="wide")

REQUIRED_COLUMNS = ["month", "revenue", "cogs", "operating_expenses", "budget_revenue", "budget_expenses"]
NUMERIC_COLUMNS = ["revenue", "cogs", "operating_expenses", "budget_revenue", "budget_expenses"]

st.title("📊 AI Financial Analyst Copilot")
st.caption("Upload monthly financial data, review deterministic KPIs, and ask evidence-grounded questions.")
st.warning("Privacy: do not upload confidential, personal, customer-identifiable, or otherwise restricted data unless your organisation has approved this use. If you use the LLM feature, selected financial summaries and relevant rows are sent to the configured API provider. Review that provider's terms and your company policy first.")

with st.expander("Expected CSV format"):
    st.write("Required columns: " + ", ".join(REQUIRED_COLUMNS))
    st.write("Use one row per month. `month` should be parseable as a date or month label. Monetary values should be numeric and use a consistent currency/unit.")
    st.code("month,revenue,cogs,operating_expenses,budget_revenue,budget_expenses\n2025-01,1000000,420000,350000,950000,800000\n2025-02,1100000,450000,370000,1050000,820000", language="csv")

@st.cache_data
def load_sample():
    return pd.read_csv("sample_financials.csv")

uploaded = st.file_uploader("Upload monthly financial statements (CSV)", type=["csv"])
use_sample = st.checkbox("Use included synthetic sample data", value=uploaded is None)

if uploaded is not None:
    try:
        raw = pd.read_csv(uploaded)
    except Exception as exc:
        st.error(f"Could not read this CSV: {exc}")
        st.stop()
elif use_sample:
    try:
        raw = load_sample()
    except Exception:
        st.error("Sample file not found. Run the app from the project directory or upload a CSV.")
        st.stop()
else:
    st.info("Upload a CSV or select the synthetic sample data to begin.")
    st.stop()

raw.columns = [str(c).strip().lower() for c in raw.columns]
missing = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
if missing:
    st.error("Missing required column(s): " + ", ".join(missing) + ". Required columns are: " + ", ".join(REQUIRED_COLUMNS))
    st.stop()
if raw.empty:
    st.error("The CSV has headers but no data rows.")
    st.stop()

# Validate and normalize dates.
raw["month"] = pd.to_datetime(raw["month"], errors="coerce")
if raw["month"].isna().any():
    bad_rows = (raw.index[raw["month"].isna()] + 2).tolist()
    st.error(f"Invalid or missing month/date value in CSV row(s): {bad_rows}. Use values such as 2025-01 or 2025-01-31.")
    st.stop()
for col in NUMERIC_COLUMNS:
    raw[col] = pd.to_numeric(raw[col].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.strip(), errors="coerce")
    if raw[col].isna().any():
        bad_rows = (raw.index[raw[col].isna()] + 2).tolist()
        st.error(f"Column `{col}` has missing or non-numeric values in CSV row(s): {bad_rows}.")
        st.stop()
    if (raw[col] < 0).any():
        bad_rows = (raw.index[raw[col] < 0] + 2).tolist()
        st.error(f"Column `{col}` has negative values in CSV row(s): {bad_rows}. Check whether the file uses a different sign convention.")
        st.stop()
if raw["month"].duplicated().any():
    dupes = raw.loc[raw["month"].duplicated(keep=False), "month"].dt.strftime("%Y-%m").tolist()
    st.error("Duplicate month(s) found: " + ", ".join(dupes) + ". Provide one row per month or aggregate the source data first.")
    st.stop()

raw = raw.sort_values("month").reset_index(drop=True)
df = raw.copy()
df["gross_profit"] = df["revenue"] - df["cogs"]
df["gross_margin_pct"] = (df["gross_profit"] / df["revenue"].replace(0, pd.NA)) * 100
df["ebitda"] = df["gross_profit"] - df["operating_expenses"]
df["revenue_growth_pct"] = df["revenue"].pct_change() * 100
df["expense_growth_pct"] = df["operating_expenses"].pct_change() * 100
df["revenue_budget_variance"] = df["revenue"] - df["budget_revenue"]
df["revenue_budget_variance_pct"] = df["revenue_budget_variance"] / df["budget_revenue"].replace(0, pd.NA) * 100
df["expense_budget_variance"] = df["operating_expenses"] - df["budget_expenses"]
df["expense_budget_variance_pct"] = df["expense_budget_variance"] / df["budget_expenses"].replace(0, pd.NA) * 100
df["month_label"] = df["month"].dt.strftime("%b %Y")

st.subheader("Financial overview")
latest = df.iloc[-1]
previous = df.iloc[-2] if len(df) > 1 else None
fmt = lambda x: "N/A" if pd.isna(x) else f"{x:,.0f}"
fmt_pct = lambda x: "N/A" if pd.isna(x) else f"{x:,.1f}%"
cols = st.columns(4)
cols[0].metric("Latest revenue", fmt(latest["revenue"]), None if previous is None else fmt(latest["revenue"] - previous["revenue"]))
cols[1].metric("Gross margin", fmt_pct(latest["gross_margin_pct"]))
cols[2].metric("EBITDA", fmt(latest["ebitda"]))
cols[3].metric("Revenue vs budget", fmt(latest["revenue_budget_variance"]), fmt_pct(latest["revenue_budget_variance_pct"]))

with st.expander("Calculation definitions"):
    st.markdown("- **Revenue growth %** = current month revenue / prior month revenue − 1. First month is unavailable.\n- **Gross margin %** = (revenue − COGS) / revenue.\n- **EBITDA (proxy)** = revenue − COGS − operating expenses. This is only as complete as the uploaded expense definitions.\n- **Expense growth %** = current month operating expenses / prior month operating expenses − 1.\n- **Budget variances** = actual less budget. Positive expense variance means overspend; positive revenue variance means above budget.")

chart1, chart2 = st.columns(2)
with chart1:
    st.plotly_chart(px.line(df, x="month", y=["revenue", "budget_revenue"], markers=True, title="Revenue vs budget"), use_container_width=True)
with chart2:
    st.plotly_chart(px.bar(df, x="month_label", y="ebitda", title="Monthly EBITDA (proxy)"), use_container_width=True)
chart3, chart4 = st.columns(2)
with chart3:
    st.plotly_chart(px.line(df, x="month", y="gross_margin_pct", markers=True, title="Gross margin trend (%)"), use_container_width=True)
with chart4:
    st.plotly_chart(px.bar(df, x="month_label", y="expense_budget_variance", title="Operating expense budget variance (actual − budget)"), use_container_width=True)

st.subheader("Monthly results")
display_cols = ["month_label", "revenue", "revenue_growth_pct", "gross_profit", "gross_margin_pct", "operating_expenses", "expense_growth_pct", "ebitda", "revenue_budget_variance", "revenue_budget_variance_pct", "expense_budget_variance", "expense_budget_variance_pct"]
st.dataframe(df[display_cols].rename(columns={"month_label":"Month", "revenue":"Revenue", "revenue_growth_pct":"Revenue growth %", "gross_profit":"Gross profit", "gross_margin_pct":"Gross margin %", "operating_expenses":"Operating expenses", "expense_growth_pct":"Expense growth %", "ebitda":"EBITDA (proxy)", "revenue_budget_variance":"Revenue variance", "revenue_budget_variance_pct":"Revenue variance %", "expense_budget_variance":"Expense variance", "expense_budget_variance_pct":"Expense variance %"}), use_container_width=True, hide_index=True)

st.download_button("Download calculated results (CSV)", data=df.drop(columns=["month_label"]).to_csv(index=False).encode("utf-8"), file_name="financial_analysis_results.csv", mime="text/csv")

st.subheader("Ask the AI Financial Analyst")
st.caption("The LLM interprets the supplied evidence; all arithmetic and KPIs above are calculated in Python. The model may still make mistakes, so verify important conclusions against the table and source data.")
question = st.text_area("Ask a question about this dataset", placeholder="Example: Which month had the largest operating expense overspend, and what were the figures?")

if st.button("Ask question", type="primary", disabled=not question.strip()):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if not api_key:
        st.error("OPENAI_API_KEY is not set. Add it to your environment or .env file, then restart Streamlit. The dashboard works without an API key.")
    else:
        try:
            from openai import OpenAI
            # Include computed metrics and the original numeric rows. Keep the evidence bounded.
            evidence_cols = ["month_label", "revenue", "cogs", "operating_expenses", "budget_revenue", "budget_expenses", "gross_profit", "gross_margin_pct", "ebitda", "revenue_growth_pct", "expense_growth_pct", "revenue_budget_variance", "revenue_budget_variance_pct", "expense_budget_variance", "expense_budget_variance_pct"]
            evidence = df[evidence_cols].tail(36).round(3).where(pd.notna(df[evidence_cols].tail(36)), None).to_dict(orient="records")
            system_prompt = """You are an AI financial analyst. Answer only from the EVIDENCE provided by the application. The evidence consists of deterministic Python-calculated monthly metrics and uploaded source-row fields. Do not calculate new financial figures mentally; use supplied computed fields. For every material claim, name the relevant month/period and quote the supporting metric(s). If evidence is missing, a denominator is zero, the period is outside the supplied rows, or the question asks for a cause not present in the data, explicitly say the data is insufficient and explain what is missing. Distinguish facts from interpretation. Do not claim fraud from duplicate-looking or unusual values. Do not invent company context, currency, causes, or forecasts. Mention that EBITDA is a proxy based on revenue minus COGS minus operating expenses."""
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                temperature=0.1,
                messages=[
                    {"role":"system", "content":system_prompt},
                    {"role":"user", "content":f"QUESTION:\n{question}\n\nEVIDENCE (up to the latest 36 monthly rows; values are from the uploaded file and Python calculations):\n{evidence}\n\nIf the question cannot be answered from this evidence, say so plainly."}
                ],
            )
            st.markdown(response.choices[0].message.content or "The model returned an empty response.")
            st.caption(f"Model: {model}. Check the evidence table before relying on conclusions.")
        except ImportError:
            st.error("The OpenAI package is missing. Install dependencies with `pip install -r requirements.txt`.")
        except Exception as exc:
            st.error(f"The LLM request failed: {exc}. Check your API key, model name, network access, and provider account limits.")

with st.expander("Limitations and responsible use"):
    st.markdown("- The app assumes one row per month and consistent monetary units.\n- EBITDA is a proxy, not a substitute for a reconciled accounting EBITDA definition.\n- Budget variance is actual minus budget; expense overspend is positive.\n- Growth rates are undefined for the first month and may be undefined when the prior period is zero.\n- The LLM can make mistakes despite evidence constraints. Independently verify material decisions.\n- No uploaded data is intentionally written to a database by this app; Streamlit hosting, logs, browser caches, and the LLM provider may have separate data-handling behavior. Review deployment and provider policies before using sensitive data.")
