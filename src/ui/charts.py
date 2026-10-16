"""Gráficos interativos em Plotly para visualização de rentabilidade, risco e sensibilidade com alto contraste visual."""

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

    # 1. Zona de destruição de margem (vermelho suave com destaque nítido)
    max_d = df["discount_pct_100"].max()
    if be_pct < max_d:
        fig.add_vrect(
            x0=be_pct,
            x1=max_d,
            fillcolor="rgba(239, 68, 68, 0.14)",
            layer="below",
            line_width=1,
            line_dash="dot",
            line_color="rgba(220, 38, 38, 0.4)",
            annotation_text="⚠️ Zona de Destruição de Margem",
            annotation_position="top right",
            annotation_font={"color": "#b91c1c", "size": 12, "weight": "bold"},
        )

    # 2. Linha de Margem de Contribuição Líquida (USD) - Azul Real vibrante de alto contraste
    fig.add_trace(
        go.Scatter(
            x=df["discount_pct_100"],
            y=df["contribution_margin_value"],
            mode="lines+markers",
            name="Margem de Contribuição ($)",
            line={"color": "#2563eb", "width": 3.5},
            marker={"size": 6, "color": "#1d4ed8"},
            hovertemplate="<b>Desconto: %{x:.1f}%</b><br>Margem Líquida: <b>$%{y:,.2f}</b><extra></extra>",
        ),
        secondary_y=False,
    )

    # 3. Linha de Taxa de Devolução Projetada (%) - Laranja Âmbar vibrante
    fig.add_trace(
        go.Scatter(
            x=df["discount_pct_100"],
            y=df["return_rate_100"],
            mode="lines+markers",
            name="Taxa de Devolução Estimada (%)",
            line={"color": "#ea580c", "width": 2.5, "dash": "dash"},
            marker={"size": 5, "color": "#c2410c", "symbol": "circle"},
            hovertemplate="<b>Desconto: %{x:.1f}%</b><br>Taxa de Devolução: <b>%{y:.2f}%</b><extra></extra>",
        ),
        secondary_y=True,
    )

    # 4. Linha de Breakeven horizontal ($0) - Cinza sólido nítido
    fig.add_hline(
        y=0,
        line={"color": "#64748b", "width": 2, "dash": "dash"},
        secondary_y=False,
    )

    # 5. Marcador vertical de Break-even
    fig.add_vline(
        x=be_pct,
        line={"color": "#dc2626", "width": 2.5, "dash": "dashdot"},
        annotation_text=f"Break-even: {be_pct:.1f}%",
        annotation_position="bottom right",
        annotation_font={"color": "#b91c1c", "size": 12, "weight": "bold"},
    )

    # 6. Ponto do Cenário Atual selecionado (Diamante grande com borda branca)
    curr_point = df.iloc[(df["discount_pct_100"] - curr_pct).abs().argsort()[:1]]
    if not curr_point.empty:
        is_safe = curr_pct <= be_pct
        fig.add_trace(
            go.Scatter(
                x=[curr_pct],
                y=curr_point["contribution_margin_value"].values,
                mode="markers",
                name="Cenário Atual Selecionado",
                marker={
                    "color": "#10b981" if is_safe else "#ef4444",
                    "size": 15,
                    "symbol": "diamond",
                    "line": {"color": "#ffffff", "width": 2.5},
                },
                hovertemplate="<b>🎯 Cenário Selecionado</b><br>Desconto: <b>%{x:.1f}%</b><br>Margem: <b>$%{y:,.2f}</b><extra></extra>",
            ),
            secondary_y=False,
        )

    # Layout corporativo de alta visibilidade e nitidez
    fig.update_layout(
        title={
            "text": "<b>Curva de Sensibilidade: Margem Líquida vs. Desconto Comercial</b>",
            "font": {"size": 17, "color": "#0f172a"},
            "x": 0.02,
            "y": 0.95,
        },
        xaxis={
            "title": "<b>Desconto Comercial Aplicado (%)</b>",
            "ticksuffix": "%",
            "gridcolor": "#e2e8f0",
            "zeroline": False,
            "showline": True,
            "linecolor": "#94a3b8",
            "tickfont": {"size": 12, "color": "#334155"},
            "title_font": {"size": 13, "color": "#0f172a"},
        },
        yaxis={
            "title": "<b>Margem de Contribuição Líquida (USD)</b>",
            "tickprefix": "$",
            "gridcolor": "#e2e8f0",
            "zeroline": False,
            "showline": True,
            "linecolor": "#94a3b8",
            "tickfont": {"size": 12, "color": "#334155"},
            "title_font": {"size": 13, "color": "#0f172a"},
        },
        yaxis2={
            "title": "<b>Taxa de Devolução Projetada (%)</b>",
            "ticksuffix": "%",
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "tickfont": {"size": 12, "color": "#ea580c"},
            "title_font": {"size": 13, "color": "#ea580c"},
            "range": [0, max(26.0, df["return_rate_100"].max() * 1.35)],
        },
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        hovermode="x unified",
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.05,
            "xanchor": "right",
            "x": 1.0,
            "font": {"size": 12, "color": "#334155"},
            "bgcolor": "rgba(255, 255, 255, 0.9)",
            "bordercolor": "#e2e8f0",
            "borderwidth": 1,
        },
        margin={"l": 65, "r": 65, "t": 90, "b": 55},
        height=480,
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
            textfont={"size": 12, "color": "#0f172a"},
            y=y_values,
            connector={"line": {"color": "#64748b", "width": 1.5, "dash": "dot"}},
            increasing={"marker": {"color": "#10b981"}},
            decreasing={"marker": {"color": "#ef4444"}},
            totals={
                "marker": {"color": "#1e3a8a" if margin >= 0 else "#dc2626"},
            },
        )
    )

    fig.update_layout(
        title={
            "text": "<b>DRE Gerencial da Operação: Decomposição de Custos e Risco</b>",
            "font": {"size": 16, "color": "#0f172a"},
            "x": 0.02,
        },
        xaxis={
            "tickangle": -15,
            "tickfont": {"size": 12, "color": "#334155"},
            "showline": True,
            "linecolor": "#94a3b8",
        },
        yaxis={
            "title": "<b>Valor Consolidado (USD)</b>",
            "tickprefix": "$",
            "gridcolor": "#e2e8f0",
            "tickfont": {"size": 12, "color": "#334155"},
            "title_font": {"size": 13, "color": "#0f172a"},
        },
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        margin={"l": 60, "r": 50, "t": 70, "b": 65},
        height=390,
    )

    return fig
