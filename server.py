import solara
import plotly.graph_objects as go

from model import LengnickModel


# ----------------------------------------------------------------------
# Reactive parameters (Solara state) - these drive the sliders in the UI
# ----------------------------------------------------------------------
households = solara.reactive(1000)
firms = solara.reactive(100)
seed = solara.reactive(1)


def make_model():
    return LengnickModel(H=households.value, F=firms.value, seed=seed.value)


# ----------------------------------------------------------------------
# Plotly chart components
# ----------------------------------------------------------------------
def employment_figure(model):
    df = model.datacollector.get_model_vars_dataframe()

    fig = go.Figure()
    if not df.empty:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Employment Rate"],
                mode="lines",
                line=dict(color="#4C78A8", width=2),
                name="Employment Rate",
            )
        )
    fig.update_layout(
        title="Employment Rate Over Time",
        xaxis_title="Step",
        yaxis_title="Employment Rate (%)",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def price_wage_figure(model):
    df = model.datacollector.get_model_vars_dataframe()

    fig = go.Figure()
    if not df.empty:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Mean Price"],
                mode="lines",
                line=dict(color="#54A24B", width=2),
                name="Mean Price",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Mean Wage"],
                mode="lines",
                line=dict(color="#E45756", width=2),
                name="Mean Wage",
            )
        )
    fig.update_layout(
        title="Price & Wage Trends",
        xaxis_title="Step",
        yaxis_title="Value",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def production_figure(model):
    df = model.datacollector.get_model_vars_dataframe()

    fig = go.Figure()
    if not df.empty:
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["Total Production"],
                mode="lines",
                line=dict(color="#F58518", width=2),
                name="Total Production",
            )
        )
    fig.update_layout(
        title="Total Production",
        xaxis_title="Step",
        yaxis_title="Units",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def reservation_wage_figure(model):
    df = model.datacollector.get_model_vars_dataframe()

    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Mean Wage"],
            mode="lines", line=dict(color="#E45756", width=2),
            name="Mean Firm Wage (offered)",
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Mean Reservation Wage"],
            mode="lines", line=dict(color="#4C78A8", width=2),
            name="Mean Reservation Wage (households)",
        ))
    fig.update_layout(
        title="Wage Pressure",
        xaxis_title="Step",
        yaxis_title="Wage",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def liquidity_figure(model):
    df = model.datacollector.get_model_vars_dataframe()

    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Household Liquidity"],
            mode="lines", line=dict(color="#72B7B2", width=2),
            name="Household Liquidity",
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Firm Liquidity"],
            mode="lines", line=dict(color="#B279A2", width=2),
            name="Firm Liquidity",
        ))
    fig.update_layout(
        title="Aggregate Liquidity",
        xaxis_title="Step",
        yaxis_title="Money",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def price_dispersion_figure(model):
    df = model.datacollector.get_model_vars_dataframe()

    fig = go.Figure()
    if not df.empty:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Price Dispersion"],
            mode="lines", line=dict(color="#F58518", width=2),
            name="Price Dispersion (std dev across firms)",
        ))
    fig.update_layout(
        title="Price Dispersion Across Firms",
        xaxis_title="Step",
        yaxis_title="Standard Deviation",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig


def firm_size_figure(model):
    sizes = model._get_firm_sizes()

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=sizes,
        marker=dict(color="#54A24B", line=dict(color="#2A6019", width=1)),
        nbinsx=30,
        name="Firms",
    ))

    if sizes:
        mean_size = sum(sizes) / len(sizes)
        # sample skewness
        n = len(sizes)
        variance = sum((s - mean_size) ** 2 for s in sizes) / n
        std = variance ** 0.5
        if std > 0:
            skew = sum((s - mean_size) ** 3 for s in sizes) / (n * std ** 3)
        else:
            skew = 0.0
        subtitle = f"mean = {mean_size:.1f}, skewness = {skew:.2f}"
    else:
        subtitle = ""

    fig.update_layout(
        title=f"Firm Size Distribution<br><sub>{subtitle}</sub>",
        xaxis_title="Workers per firm",
        yaxis_title="Number of firms",
        template="plotly_white",
        height=350,
        margin=dict(l=50, r=20, t=70, b=40),
    )
    return fig


def phillips_curve_figure(model):
    history = model.delta_p_history

    fig = go.Figure()
    if history:
        delta_ps = [d for d, _ in history]
        unemploys = [u for _, u in history]
        fig.add_trace(go.Scatter(
            x=delta_ps, y=unemploys,
            mode="markers",
            marker=dict(color="#4C78A8", size=5, opacity=0.6),
            name="Monthly observation",
        ))
    fig.update_layout(
        title="Phillips Curve (Unemployment vs ΔPrice)",
        xaxis_title="Δ Mean Price (month-over-month)",
        yaxis_title="Unemployed Households",
        template="plotly_white",
        height=400,
        margin=dict(l=50, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig


def beveridge_curve_figure(model):
    history = model.beveridge_history

    fig = go.Figure()
    if history:
        vacancies = [v for v, _ in history]
        unemploys = [u for _, u in history]
        fig.add_trace(go.Scatter(
            x=vacancies, y=unemploys,
            mode="markers",
            marker=dict(color="#E45756", size=5, opacity=0.6),
            name="Monthly observation",
        ))
    fig.update_layout(
        title="Beveridge Curve (Unemployment vs Vacancies)",
        xaxis_title="Vacancies (open positions)",
        yaxis_title="Unemployed Households",
        template="plotly_white",
        height=400,
        margin=dict(l=50, r=20, t=50, b=40),
        showlegend=False,
    )
    return fig


# ----------------------------------------------------------------------
# Page layout
# ----------------------------------------------------------------------
@solara.component
def Page():
    model = solara.use_memo(
        make_model, dependencies=[households.value, firms.value, seed.value]
    )
    step_count = solara.use_reactive(0)

    def do_step():
        model.step()
        step_count.value += 1

    def do_month():
        for _ in range(21):
            model.step()
        step_count.value += 21

    def do_reset():
        model.reset()  # placeholder, see note below
        step_count.value = 0

    with solara.AppBar():
        solara.AppBarTitle("Lengnick (2013) Baseline Macro Model")

    with solara.Sidebar():
        solara.Markdown("## Model Parameters")
        solara.SliderInt("Households", value=households, min=100, max=3000, step=100)
        solara.SliderInt("Firms", value=firms, min=10, max=300, step=10)
        solara.SliderInt("Random seed", value=seed, min=1, max=100, step=1)
        solara.Markdown("_Changing a parameter rebuilds the model from scratch._")

    with solara.Column(style={"padding": "20px"}):
        with solara.Row(style={"gap": "10px", "margin-bottom": "10px"}):
            solara.Button("Step", on_click=do_step, color="primary")
            solara.Button("Run 21 steps (1 month)", on_click=do_month, color="primary")
            solara.Info(f"Current step: {step_count.value}")

        solara.FigurePlotly(employment_figure(model))
        solara.FigurePlotly(price_wage_figure(model))
        solara.FigurePlotly(production_figure(model))
        solara.FigurePlotly(liquidity_figure(model))
        solara.FigurePlotly(reservation_wage_figure(model))
        solara.FigurePlotly(price_dispersion_figure(model))
        solara.FigurePlotly(firm_size_figure(model))
        solara.FigurePlotly(phillips_curve_figure(model))
        solara.FigurePlotly(beveridge_curve_figure(model))
