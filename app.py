import os
from typing import Optional

import streamlit as st

st.set_page_config(
    page_title="PropertyLab | AI Property Analysis Auditor",
    page_icon="🏙️",
    layout="wide",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background: #f5f7fb; }
    .block-container { padding-top: 2rem; max-width: 1180px; }
    .hero {
        padding: 1.7rem 1.8rem; border-radius: 18px;
        background: linear-gradient(120deg, #10243d, #1d4770);
        color: white; margin-bottom: 1.2rem;
    }
    .hero h1 { color: white; margin-bottom: .25rem; }
    .hero p { color: #d9e7f5; margin-bottom: 0; }
    .metric-card {
        background: white; padding: 1rem 1.15rem; border-radius: 14px;
        border: 1px solid #e4eaf2; min-height: 108px;
    }
    .metric-label { color: #62738a; font-size: .86rem; }
    .metric-value { color: #142b45; font-size: 1.65rem; font-weight: 750; }
    .small-note { color: #65758b; font-size: .82rem; }
    div[data-testid="stMetric"] {
        background: white; padding: 1rem; border-radius: 12px;
        border: 1px solid #e4eaf2;
    }
    .section-card {
        background: white; padding: 1.15rem; border-radius: 14px;
        border: 1px solid #e4eaf2; margin-bottom: .8rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def money(value: float) -> str:
    return f"RM {value:,.2f}"

def pct(value: float) -> str:
    return f"{value:.2f}%"

def generate_explanation(
    price: float,
    rent: float,
    instalment: float,
    other_expenses: float,
    vacancy_rate: float,
    stated_yield: Optional[float],
    stated_cashflow: Optional[float],
    annual_costs_included: bool,
) -> tuple[str, str]:
    """Use Gemini if a key is configured; otherwise provide a transparent rules-based explanation."""
    annual_rent = rent * 12
    effective_rent = annual_rent * (1 - vacancy_rate / 100)
    monthly_vacancy_adjusted_rent = effective_rent / 12
    monthly_cashflow = monthly_vacancy_adjusted_rent - instalment - other_expenses
    gross_yield = annual_rent / price * 100 if price else 0
    net_yield = (effective_rent - (other_expenses * 12) - (instalment * 12)) / price * 100 if price else 0

    prompt = f"""
You are a careful property-finance explainer. Explain the supplied illustrative figures in plain English.
Do not claim to predict property prices or guarantee returns. Do not give personalized financial advice.
Mention that calculations depend on the inputs and exclusions. Use concise headings: Summary, What to check, Limitations.
Do not invent missing figures.

Purchase price: RM {price:,.2f}
Monthly rent: RM {rent:,.2f}
Monthly loan instalment: RM {instalment:,.2f}
Other monthly expenses: RM {other_expenses:,.2f}
Vacancy allowance: {vacancy_rate:.2f}%
Gross rental yield (before expenses): {gross_yield:.2f}%
Estimated monthly cash flow after vacancy allowance: RM {monthly_cashflow:,.2f}
Net cash flow divided by purchase price (simple annualized indicator): {net_yield:.2f}%
Stated yield supplied by user: {stated_yield if stated_yield is not None else "not supplied"}
Stated monthly cash flow supplied by user: {stated_cashflow if stated_cashflow is not None else "not supplied"}
Annual costs included in monthly expenses: {annual_costs_included}
"""
    api_key = st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", "")).strip()
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            if response.text:
                return response.text, "AI-generated explanation (Gemini API)"
        except Exception as exc:
            fallback = rules_explanation(
                price, rent, instalment, other_expenses, vacancy_rate,
                gross_yield, monthly_cashflow, stated_yield, stated_cashflow
            )
            return fallback + f"\n\n*AI API was unavailable, so the built-in explanation was used. Technical detail: {type(exc).__name__}.*", "Built-in explanation (AI API unavailable)"
    return rules_explanation(
        price, rent, instalment, other_expenses, vacancy_rate,
        gross_yield, monthly_cashflow, stated_yield, stated_cashflow
    ), "Built-in explanation (no API key configured)"

def rules_explanation(price, rent, instalment, expenses, vacancy, gross_yield,
                      cashflow, stated_yield, stated_cashflow):
    points = []
    if cashflow < 0:
        summary = f"The estimated monthly cash flow is negative at RM {cashflow:,.2f}. Based on the inputs, rent may not cover the loan instalment and listed expenses after allowing for vacancy."
    elif cashflow == 0:
        summary = "The estimated monthly cash flow is approximately break-even. A small change in rent, vacancy, interest costs or repairs could move it into a deficit."
    else:
        summary = f"The estimated monthly cash flow is positive at RM {cashflow:,.2f}. This is a simplified estimate, not a guarantee of future performance."

    if vacancy > 0:
        points.append(f"The {vacancy:.1f}% vacancy allowance reduces the rent used in the cash-flow estimate.")
    if stated_yield is not None:
        difference = gross_yield - stated_yield
        if abs(difference) > 0.15:
            points.append(f"The stated yield ({stated_yield:.2f}%) differs from the calculated gross rental yield ({gross_yield:.2f}%) by {difference:+.2f} percentage points. Confirm whether both figures use the same rent and purchase-price assumptions.")
        else:
            points.append(f"The stated yield ({stated_yield:.2f}%) is close to the calculated gross rental yield ({gross_yield:.2f}%).")
    if stated_cashflow is not None:
        difference = cashflow - stated_cashflow
        if abs(difference) > 1:
            points.append(f"The stated monthly cash flow ({money(stated_cashflow)}) differs from this estimate ({money(cashflow)}) by {money(difference)}. Check which expenses and vacancy assumptions each figure includes.")
        else:
            points.append("The stated monthly cash flow is consistent with this simplified estimate.")
    if not points:
        points.append("Compare these figures with any advertised yield or cash-flow estimate and confirm that the same expenses and assumptions are used.")
    points.append("Check whether maintenance, assessment/quit rent, insurance, agent fees, repairs, taxes and periods without tenants are included.")
    points.append("This prototype does not model loan interest-rate changes, transaction costs, capital appreciation or tax treatment.")

    return "### Summary\n" + summary + "\n\n### What to check\n" + "\n".join(f"- {p}" for p in points) + "\n\n### Limitations\nThese are illustrative calculations based only on the inputs entered. They are not a property valuation or financial recommendation."

# ---------- Header ----------
st.markdown("""
<div class="hero">
  <h1>Property Analysis Auditor</h1>
  <p>Independent checks for property cash flow, rental yield and investment assumptions.</p>
</div>
""", unsafe_allow_html=True)

st.info(
    "Independent prototype concept — not an official PropertyLab product and not connected to PropertyLab's internal data. "
    "Use sample figures for demonstration."
)

# ---------- Sidebar inputs ----------
with st.sidebar:
    st.header("Property inputs")
    sample = st.toggle("Load demo example", value=True)
    if sample:
        default_price, default_rent, default_instalment, default_expenses = 450000.0, 2500.0, 2200.0, 700.0
        default_vacancy, default_stated_yield, default_stated_cashflow = 5.0, 6.8, -250.0
    else:
        default_price, default_rent, default_instalment, default_expenses = 450000.0, 2500.0, 2200.0, 300.0
        default_vacancy, default_stated_yield, default_stated_cashflow = 0.0, 6.67, 0.0

    price = st.number_input("Purchase price (RM)", min_value=1.0, value=default_price, step=10000.0)
    rent = st.number_input("Expected monthly rent (RM)", min_value=0.0, value=default_rent, step=100.0)
    instalment = st.number_input("Monthly loan instalment (RM)", min_value=0.0, value=default_instalment, step=100.0)
    expenses = st.number_input("Other monthly expenses (RM)", min_value=0.0, value=default_expenses, step=50.0)
    vacancy = st.slider("Vacancy allowance (%)", min_value=0.0, max_value=30.0, value=default_vacancy, step=1.0)
    st.divider()
    st.caption("Optional: compare the calculated metrics with figures shown in a listing or report.")
    compare_yield = st.checkbox("I have a stated rental yield", value=True)
    stated_yield = st.number_input("Stated gross rental yield (%)", min_value=0.0, max_value=100.0, value=default_stated_yield, step=0.1) if compare_yield else None
    compare_cashflow = st.checkbox("I have a stated monthly cash flow", value=True)
    stated_cashflow = st.number_input("Stated monthly cash flow (RM)", min_value=-100000.0, max_value=100000.0, value=default_stated_cashflow, step=50.0) if compare_cashflow else None

# ---------- Calculations ----------
annual_rent = rent * 12
effective_annual_rent = annual_rent * (1 - vacancy / 100)
effective_monthly_rent = effective_annual_rent / 12
gross_yield = annual_rent / price * 100
effective_gross_yield = effective_annual_rent / price * 100
cashflow = effective_monthly_rent - instalment - expenses
annual_cashflow = cashflow * 12
simple_cashflow_return = annual_cashflow / price * 100

st.subheader("Financial overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Gross rental yield", pct(gross_yield), help="Annual rent ÷ purchase price. Before expenses and vacancy.")
c2.metric("Yield after vacancy", pct(effective_gross_yield), help="Annual rent after vacancy allowance ÷ purchase price. Still before operating expenses.")
c3.metric("Estimated monthly cash flow", money(cashflow), delta="Deficit" if cashflow < 0 else "Surplus", delta_color="inverse" if cashflow < 0 else "normal")
c4.metric("Annualized cash flow", money(annual_cashflow), help="Monthly estimated cash flow × 12.")

left, right = st.columns([1.1, 0.9], gap="large")
with left:
    st.subheader("Cash-flow breakdown")
    breakdown = {
        "Monthly rent": rent,
        "Vacancy allowance": -(rent * vacancy / 100),
        "Loan instalment": -instalment,
        "Other expenses": -expenses,
        "Estimated net cash flow": cashflow,
    }
    st.dataframe(
        [{"Item": k, "Amount": money(v)} for k, v in breakdown.items()],
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Cash flow = rent − vacancy allowance − loan instalment − other monthly expenses.")

with right:
    st.subheader("Consistency checks")
    if stated_yield is not None:
        yield_gap = gross_yield - stated_yield
        if abs(yield_gap) > 0.15:
            st.warning(f"**Rental yield discrepancy:** stated {stated_yield:.2f}% vs calculated {gross_yield:.2f}% (difference {yield_gap:+.2f} percentage points).")
        else:
            st.success(f"Rental yield is broadly consistent (difference {yield_gap:+.2f} percentage points).")
    if stated_cashflow is not None:
        cash_gap = cashflow - stated_cashflow
        if abs(cash_gap) > 1:
            st.warning(f"**Cash-flow discrepancy:** stated {money(stated_cashflow)} vs calculated {money(cashflow)} (difference {money(cash_gap)}).")
        else:
            st.success("Stated cash flow is broadly consistent with the current inputs.")
    st.caption("A discrepancy is a prompt to check assumptions, not proof that a listing is wrong.")

st.divider()
st.subheader("AI explanation")
st.write("Generate a plain-language explanation of the calculations, discrepancies and assumptions.")
if st.button("Generate analysis", type="primary", use_container_width=False):
    with st.spinner("Preparing the explanation..."):
        explanation, mode = generate_explanation(
            price, rent, instalment, expenses, vacancy,
            stated_yield, stated_cashflow, False
        )
    st.session_state["analysis_explanation"] = explanation
    st.session_state["analysis_mode"] = mode

if "analysis_explanation" in st.session_state:
    st.caption(st.session_state.get("analysis_mode", "Explanation"))
    st.markdown(st.session_state["analysis_explanation"])
else:
    st.caption("Select **Generate analysis** to see the explanation. Without an API key, the built-in explanation works locally.")

st.divider()
st.markdown("""
**Prototype notes**
- Rental yield is calculated as annual gross rent divided by purchase price.
- Cash flow subtracts the vacancy allowance, loan instalment and entered monthly expenses from monthly rent.
- The simple cash-flow return is not the same as ROI or total return; capital gains, financing structure, taxes and purchase costs are not modelled.
- This tool is for demonstration and educational purposes only.
""")
