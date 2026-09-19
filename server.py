import streamlit as st
import plotly.graph_objects as go

from model import LengnickModel


# ----------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Lengnick (2013) Baseline Macro Model",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished look
st.markdown("""
<style>
    /* Import Inter from Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Page background - light blue tint */
    [data-testid="stAppViewContainer"] {
        background: #eff5f9;
        font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main content spacing */
    .block-container { padding-top: 3rem; padding-bottom: 2rem; max-width: 1600px; }

    /* Chart card containers */
    [data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid rgba(30, 58, 95, 0.08);
        border-radius: 12px;
        padding: 8px 12px;
        box-shadow: 0 1px 3px rgba(30, 58, 95, 0.06);
        margin-bottom: 16px;
        overflow: hidden;
    }

    /* Page title */
    h1 { color: #1e3a5f; font-weight: 700; letter-spacing: -0.5px; }

    /* KPI metric cards — bigger, bolder */
    [data-testid="stMetric"] {
        background: white;
        border: 1px solid rgba(30, 58, 95, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(30, 58, 95, 0.06);
    }
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #1e3a5f !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 12px !important;
        color: #6b7a8c !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-weight: 600;
    }

/* Status badges for step/month/year — uniform card-matched look */
    .status-badge {
        display: inline-block;
        background: white;
        color: #1e3a5f;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 13px;
        font-weight: 600;
        margin: 8px 8px 16px 0;
        border: 1px solid rgba(30, 58, 95, 0.08);
        box-shadow: 0 1px 2px rgba(30, 58, 95, 0.04);
    }

    /* Light text on dark sidebar */
    [data-testid="stSidebar"] { background: #1a2332 !important; }
    [data-testid="stSidebar"] * { color: #e0e6ed !important; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #8a9cb0 !important;
    }
    [data-testid="stSidebar"] hr { border-color: #2d3b50 !important; }

    /* Sidebar button styling */
    [data-testid="stSidebar"] button {
        background: #243245 !important;
        border: 1px solid #344459 !important;
        color: #e0e6ed !important;
        transition: all 0.15s;
    }
    [data-testid="stSidebar"] button:hover {
        background: #2d3d54 !important;
        border-color: #4a5d78 !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: #1e88c7 !important;
        border-color: #1e88c7 !important;
        color: white !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: #1976a8 !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        font-size: 15px;
        padding: 8px 16px;
    }

    /* Tab descriptions */
    .tab-description {
        color: #6b7a8c;
        font-style: italic;
        font-size: 13px;
        margin: 4px 0 16px 0;
    }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
if "model" not in st.session_state:
    st.session_state.model = None
    st.session_state.steps_run = 0


def make_model(H, F, seed):
    return LengnickModel(H=H, F=F, seed=seed)


# ----------------------------------------------------------------------
# Plotly chart builders
# ----------------------------------------------------------------------
def _base_layout(title, xaxis="Step", yaxis=""):
    """Common Plotly layout — bold teal title, clean grid, transparent everywhere.
    Mimics the reference chart style: chart sits directly on page background."""
    return dict(
title=dict(
            text=f"<b>{title}</b>",
            font=dict(size=18, color="#000000", family="Inter, sans-serif"),
            x=0.02, y=0.97, xanchor="left",
        ),
        xaxis_title=dict(text=f"<b>{xaxis}</b>", font=dict(size=14, color="#000000", family="Inter, sans-serif")),
        yaxis_title=dict(text=f"<b>{yaxis}</b>", font=dict(size=14, color="#000000", family="Inter, sans-serif")),
        height=450,
        margin=dict(l=80, r=30, t=80, b=70),
        font=dict(family="Inter, sans-serif", size=12, color="#000000"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            gridcolor="rgba(30, 58, 95, 0.08)",
            zerolinecolor="rgba(30, 58, 95, 0.15)",
            linecolor="#000000",
            linewidth=1.5,
            tickfont=dict(size=12, color="#000000"),
        ),
        yaxis=dict(
            gridcolor="rgba(30, 58, 95, 0.08)",
            zerolinecolor="rgba(30, 58, 95, 0.15)",
            linecolor="#000000",
            linewidth=1.5,
            tickfont=dict(size=12, color="#000000"),
        ),
    )


def employment_figure(df):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df["Employment Rate"],
                                 mode="lines", line=dict(color="#4C78A8", width=2.5)))
    fig.update_layout(**_base_layout("Employment Rate Over Time", yaxis="Employment Rate (%)"))
    return fig


def price_wage_figure(df):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df["Mean Price"],
                                 mode="lines", line=dict(color="#54A24B", width=2.5), name="Mean Price"))
        fig.add_trace(go.Scatter(x=df.index, y=df["Mean Wage"],
                                 mode="lines", line=dict(color="#E45756", width=2.5), name="Mean Wage"))
    fig.update_layout(**_base_layout("Price & Wage Trends", yaxis="Value"))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig


def production_figure(df):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df["Total Production"],
                                 mode="lines", line=dict(color="#F58518", width=2.5)))
    fig.update_layout(**_base_layout("Total Production", yaxis="Units"))
    return fig


def liquidity_figure(df):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df["Household Liquidity"],
                                 mode="lines", line=dict(color="#72B7B2", width=2), name="Household"))
        fig.add_trace(go.Scatter(x=df.index, y=df["Firm Liquidity"],
                                 mode="lines", line=dict(color="#B279A2", width=2), name="Firm"))
    fig.update_layout(**_base_layout("Aggregate Liquidity", yaxis="Money"))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig


def wage_pressure_figure(df):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df["Mean Wage"],
                                 mode="lines", line=dict(color="#E45756", width=2.5),
                                 name="Firm wage (offered)"))
        fig.add_trace(go.Scatter(x=df.index, y=df["Mean Reservation Wage"],
                                 mode="lines", line=dict(color="#4C78A8", width=2.5),
                                 name="Reservation wage"))
    fig.update_layout(**_base_layout("Wage Pressure", yaxis="Wage"))
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig


def price_dispersion_figure(df):
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(x=df.index, y=df["Price Dispersion"],
                                 mode="lines", line=dict(color="#F58518", width=2.5)))
    fig.update_layout(**_base_layout("Price Dispersion Across Firms", yaxis="Std deviation"))
    return fig


def firm_size_figure(model):
    sizes = model._get_firm_sizes()
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=sizes, marker=dict(color="#54A24B", line=dict(color="#2A6019", width=1)),
        nbinsx=30,
    ))
    if sizes:
        mean_size = sum(sizes) / len(sizes)
        n = len(sizes)
        variance = sum((s - mean_size) ** 2 for s in sizes) / n
        std = variance ** 0.5
        skew = sum((s - mean_size) ** 3 for s in sizes) / (n * std ** 3) if std > 0 else 0.0
        subtitle = f"mean = {mean_size:.1f}, skewness = {skew:.2f}"
    else:
        subtitle = ""
    fig.update_layout(**_base_layout(
        f"Firm Size Distribution<br><sub style='color:#8a9cb0'>{subtitle}</sub>",
        xaxis="Workers per firm", yaxis="Number of firms"))
    fig.update_layout(height=450, margin=dict(t=85))
    return fig


def phillips_curve_figure(model):
    history = model.delta_p_history
    fig = go.Figure()
    if history:
        fig.add_trace(go.Scatter(
            x=[d for d, _ in history], y=[u for _, u in history],
            mode="markers", marker=dict(color="#4C78A8", size=6, opacity=0.55),
        ))
    fig.update_layout(**_base_layout("Phillips Curve",
                                     xaxis="Δ Mean Price (month-over-month)",
                                     yaxis="Unemployed Households"))
    fig.update_layout(height=450)
    return fig


def beveridge_curve_figure(model):
    history = model.beveridge_history
    fig = go.Figure()
    if history:
        fig.add_trace(go.Scatter(
            x=[v for v, _ in history], y=[u for _, u in history],
            mode="markers", marker=dict(color="#E45756", size=6, opacity=0.55),
        ))
    fig.update_layout(**_base_layout("Beveridge Curve",
                                     xaxis="Vacancies (open positions)",
                                     yaxis="Unemployed Households"))
    fig.update_layout(height=450)
    return fig


# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.title("Lengnick Model")
    st.caption("Baseline ABM (2013)")

    st.divider()
    st.subheader("Model Parameters")

    H = st.slider("Households", 100, 3000, 1000, 100)
    F = st.slider("Firms", 10, 300, 100, 10)
    seed = st.slider("Random seed", 1, 100, 1)

    if st.button("Initialise / Reset", use_container_width=True, type="primary"):
        st.session_state.model = make_model(H, F, seed)
        st.session_state.steps_run = 0
        st.rerun()

    st.divider()
    st.subheader("Simulation")

    if st.session_state.model is None:
        st.caption("Initialise a model first")
    else:
        col1, col2 = st.columns(2)
        if col1.button("Step", use_container_width=True, type="primary"):
            st.session_state.model.step()
            st.session_state.steps_run += 1
            st.rerun()
        if col2.button("Month", use_container_width=True, type="primary"):
            for _ in range(21):
                st.session_state.model.step()
            st.session_state.steps_run += 21
            st.rerun()

        if st.button("Run 12 months", use_container_width=True, type="primary"):
            for _ in range(12 * 21):
                st.session_state.model.step()
            st.session_state.steps_run += 12 * 21
            st.rerun()

        if st.button("Run 50 months", use_container_width=True, type="primary"):
            for _ in range(50 * 21):
                st.session_state.model.step()
            st.session_state.steps_run += 50 * 21
            st.rerun()


# ----------------------------------------------------------------------
# Main page
# ----------------------------------------------------------------------
title_col, about_col = st.columns([6, 1])
with title_col:
    st.title("Lengnick (2013) Baseline Macroeconomic Model")
with about_col:
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # vertical align
    with st.popover("ℹ️  About", use_container_width=True):
        st.markdown("""
        ### About this model

        A Python implementation of **Matthias Lengnick's (2013) baseline
        agent-based macroeconomic model**, published in the *Journal of
        Economic Behavior & Organization*.

        Two agent types — households and firms — are connected by a dynamic
        network of trading relationships. There is no central market-clearing
        mechanism: every transaction happens between named individuals, and
        aggregate regularities emerge from local interaction alone.

        #### Views

        - **📈 Headlines** — employment, prices, wages, production, and the
          sawtooth flow of liquidity between households and firms
          (paper Fig. 7).

        - **🎯 Stylised Facts** — the paper's main empirical claims
          (Section 3): the Phillips curve, the Beveridge curve, and the
          right-skewed firm size distribution.

        - **🔬 Diagnostics** — wage pressure (the gap between offered and
          reservation wages) and price dispersion across firms.

        #### Controls

        Set parameters in the sidebar and click **Initialise / Reset**, then
        step the model forward. Around 50 months is enough for the dynamics
        to settle; 200 shows the longer cycles.

        ---

        *This implementation departs from both the published paper and the
        original Java source in several documented ways — including the
        consumption function, the price bounds, labour productivity, and the
        speed at which firms can adjust headcount. Most correct behaviour in
        the Java that contradicts the paper's own text. See the README for
        the full list and the reasoning behind each.*
        """)

# Status badges — step, month, year
steps = st.session_state.steps_run
months = steps // 21
years = steps // 252  # 21 steps × 12 months
st.markdown(
    f'<span class="status-badge accent">Step {steps:,}</span>'
    f'<span class="status-badge">Month {months}</span>'
    f'<span class="status-badge">Approx. Year {years}</span>',
    unsafe_allow_html=True,
)

if st.session_state.model is None:
    st.info("👈 Initialise a model from the sidebar to begin.")
    st.stop()

model = st.session_state.model
df = model.datacollector.get_model_vars_dataframe()

# KPI cards
if not df.empty:
    latest = df.iloc[-1]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Employment", f"{latest['Employment Rate']:.1f}%")
    c2.metric("Mean Wage", f"{latest['Mean Wage']:.4f}")
    c3.metric("Mean Price", f"{latest['Mean Price']:.4f}")
    c4.metric("Production", f"{latest['Total Production']:.0f}")
    c5.metric("HH Liquidity", f"{latest['Household Liquidity']:.0f}")

st.divider()

# Pills navigation
view = st.pills(
    "View",
    options=["📈  Headlines", "🎯  Stylised Facts", "🔬  Diagnostics"],
    default="📈  Headlines",
    label_visibility="collapsed",
)

if view == "📈  Headlines":
    st.markdown(
        '<div class="tab-description">Core macroeconomic outcomes from the baseline simulation.</div>',
        unsafe_allow_html=True,
    )
    st.plotly_chart(employment_figure(df), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(price_wage_figure(df), use_container_width=True)
    with col2:
        st.plotly_chart(production_figure(df), use_container_width=True)
    st.plotly_chart(liquidity_figure(df), use_container_width=True)

elif view == "🎯  Stylised Facts":
    st.markdown(
        '<div class="tab-description">Reproductions of the paper\'s headline empirical claims (Section 3).</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(phillips_curve_figure(model), use_container_width=True)
    with col2:
        st.plotly_chart(beveridge_curve_figure(model), use_container_width=True)
    st.plotly_chart(firm_size_figure(model), use_container_width=True)

elif view == "🔬  Diagnostics":
    st.markdown(
        '<div class="tab-description">Internal model diagnostics for debugging and analysis.</div>',
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(wage_pressure_figure(df), use_container_width=True)
    with col2:
        st.plotly_chart(price_dispersion_figure(df), use_container_width=True)
