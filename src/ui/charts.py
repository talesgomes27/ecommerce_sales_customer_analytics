"""Gráficos interativos em Plotly para visualização de rentabilidade, risco e sensibilidade."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.core.schemas import SimulationResultOutput, SimulationScenarioInput


def plot_discount_sensitivity_curve(
    curve_data: list[dict[str, float | str | bool]],
    current_discount: float,
    break_even_discount: float,
) -> go.Figure:
    """Plota a curva de sensibilidade da margem de contribuição e taxa de devolução por desconto."""
    df = pd.DataFrame(curve_data)
    df["discount_pct_100"] = df["discount_pct"] * 100.0
    df["return_rate_100"] = df["estimated_return_rate"] * 100.0

    be_pct = break_even_discount * 100.0
    curr_pct = current_discount * 100.0

    # Cria subplots com dois eixos Y
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
    )

    # 1. Zona de destruição de margem (vermelho translúcido)
    max_d = df["discount_pct_100"].max()
    if be_pct < max_d:
        fig.add_vrect(
            x0=be_pct,
            x1=max_d,
            fillcolor="rgba(231, 76, 60, 0.12)",
            layer="below",
            line_width=0,
            annotation_text="Zona de Destruição de Margem",
            annotation_position="top right",
            annotation_font={"color": "#c0392b", "size": 11, "family": "sans-serif"},
        )

    # 2. Linha de Margem de Contribuição Líquida (USD)
    fig.add_trace(
        go.Scatter(
            x=df["discount_pct_100"],
            y=df["contribution_margin_value"],
            mode="lines+markers",
            name="Margem de Contribuição ($)",
            line={"color": "#1b4f72", "width": 3},
            marker={"size": 6, "color": "#1b4f72"},
            hovertemplate="Desconto: %{x:.1f}%<br>Margem Líquida: $%{y:,.2f}<extra></extra>",
        ),
        secondary_y=False,
    )

    # 3. Linha de Taxa de Devolução Projetada (%)
    fig.add_trace(
        go.Scatter(
            x=df["discount_pct_100"],
            y=df["return_rate_100"],
            mode="lines",
            name="Risco de Devolução (%)",
            line={"color": "#e67e22", "width": 2, "dash": "dot"},
            hovertemplate="Desconto: %{x:.1f}%<br>Taxa de Devolução: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    # 4. Linha de Breakeven horizontal ($0)
    fig.add_hline(
        y=0,
        line={"color": "#7f8c8d", "width": 1.5, "dash": "dash"},
        secondary_y=False,
    )

    # 5. Marcador vertical de Break-even
    fig.add_vline(
        x=be_pct,
        line={"color": "#c0392b", "width": 2, "dash": "dash"},
        annotation_text=f"Break-even ({be_pct:.1f}%)",
        annotation_position="bottom right",
        annotation_font={"color": "#c0392b", "size": 11, "weight": "bold"},
    )

    # 6. Ponto do Cenário Atual selecionado
    curr_point = df.iloc[(df["discount_pct_100"] - curr_pct).abs().argsort()[:1]]
    if not curr_point.empty:
        fig.add_trace(
            go.Scatter(
                x=[curr_pct],
                y=curr_point["contribution_margin_value"].values,
                mode="markers",
                name="Cenário Atual",
                marker={
                    "color": "#27ae60" if curr_pct <= be_pct else "#e74c3c",
                    "size": 13,
                    "symbol": "diamond",
                    "line": {"color": "#ffffff", "width": 2},
                },
                hovertemplate="<b>Cenário Selecionado</b><br>Desconto: %{x:.1f}%<br>Margem: $%{y:,.2f}<extra></extra>",
            ),
            secondary_y=False,
        )

    # Layout corporativo e responsivo
    fig.update_layout(
        title={
            "text": "<b>Curva de Sensibilidade: Margem Líquida vs. Desconto Comercial</b>",
            "font": {"size": 16, "color": "#2c3e50"},
            "x": 0.0,
        },
        xaxis={
            "title": "<b>Desconto Concedido (%)</b>",
            "ticksuffix": "%",
            "gridcolor": "#f1f2f6",
            "showline": True,
            "linecolor": "#bdc3c7",
        },
        yaxis={
            "title": "<b>Margem de Contribuição (USD)</b>",
            "tickprefix": "$",
            "gridcolor": "#f1f2f6",
            "zeroline": False,
            "showline": True,
            "linecolor": "#bdc3c7",
        },
        yaxis2={
            "title": "<b>Taxa de Devolução Estimada (%)</b>",
            "ticksuffix": "%",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "range": [0, max(25.0, df["return_rate_100"].max() * 1.3)],
        },
        template="plotly_white",
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.03,
            "xanchor": "right",
            "x": 1.0,
            "font": {"size": 11},
        },
        margin={"l": 60, "r": 60, "t": 80, "b": 50},
        height=450,
    )

    return fig


def plot_waterfall_cost_breakdown(
    scenario: SimulationScenarioInput,
    result: SimulationResultOutput,
) -> go.Figure:
    """Gera gráfico Waterfall decompondo a transição da Receita Líquida até a Margem de Contribuição."""
    q = scenario.quantity
    p_net = scenario.unit_price * (1.0 - scenario.discount_pct)
    net_revenue = q * p_net

    cogs_total = q * scenario.unit_cost
    shipping_total = q * scenario.shipping_cost
    tax_total = net_revenue * scenario.tax_rate
    risk_total = result.total_cost - (cogs_total + shipping_total + tax_total)
    margin = result.contribution_margin_value

    measures = ["relative", "relative", "relative", "relative", "relative", "total"]
    x_labels = [
        "Receita Líquida",
        "CMV (Custo Produto)",
        "Frete Envio",
        "Impostos Fiscais",
        "Provisão de Risco",
        "Margem Líquida",
    ]
    y_values = [
        round(net_revenue, 2),
        -round(cogs_total, 2),
        -round(shipping_total, 2),
        -round(tax_total, 2),
        -round(risk_total, 2),
        round(margin, 2),
    ]

    fig = go.Figure(
        go.Waterfall(
            name="Decomposição",
            orientation="v",
            measure=measures,
            x=x_labels,
            textposition="outside",
            text=[f"${abs(v):,.0f}" for v in y_values],
            y=y_values,
            connector={"line": {"color": "#7f8c8d", "width": 1, "dash": "dot"}},
            increasing={"marker": {"color": "#27ae60"}},
            decreasing={"marker": {"color": "#e74c3c"}},
            totals={
                "marker": {"color": "#1b4f72" if margin >= 0 else "#c0392b"},
            },
        )
    )

    fig.update_layout(
        title={
            "text": "<b>DRE Gerencial da Operação: Decomposição de Custos e Risco</b>",
            "font": {"size": 14, "color": "#2c3e50"},
            "x": 0.0,
        },
        xaxis={"tickangle": -15},
        yaxis={
            "title": "Valor Consolidado (USD)",
            "tickprefix": "$",
            "gridcolor": "#f1f2f6",
        },
        template="plotly_white",
        margin={"l": 50, "r": 40, "t": 60, "b": 60},
        height=360,
    )

    return fig
