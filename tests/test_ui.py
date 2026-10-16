"""Testes de integridade da camada de gráficos interativos Plotly."""

import plotly.graph_objects as go
import pytest

from src.core.schemas import (
    AcquisitionChannel,
    Category,
    SimulationScenarioInput,
)
from src.core.simulator import BusinessScenarioSimulator
from src.ui.charts import (
    plot_discount_sensitivity_curve,
    plot_waterfall_cost_breakdown,
)


@pytest.fixture
def sample_scenario() -> SimulationScenarioInput:
    return SimulationScenarioInput(
        unit_price=1000.0,
        unit_cost=500.0,
        quantity=20,
        discount_pct=0.15,
        shipping_cost=20.0,
        tax_rate=0.10,
        delivery_days=3,
        category=Category.ELECTRONICS,
        channel=AcquisitionChannel.DIRECT,
        reverse_logistics_cost=45.0,
    )


def test_plot_discount_sensitivity_curve_generation(
    sample_scenario: SimulationScenarioInput,
):
    """Gera o gráfico Plotly da curva de sensibilidade e valida sua estrutura de eixos e traces."""
    simulator = BusinessScenarioSimulator()
    result = simulator.simulate_scenario(sample_scenario)
    curve_data = simulator.calculate_discount_sensitivity_curve(sample_scenario, steps=10)

    fig = plot_discount_sensitivity_curve(
        curve_data=curve_data,
        current_discount=sample_scenario.discount_pct,
        break_even_discount=result.break_even_discount,
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 3  # Traces de margem, risco e cenário atual
    assert "Desconto" in fig.layout.xaxis.title.text
    assert "Margem" in fig.layout.yaxis.title.text


def test_plot_waterfall_cost_breakdown_generation(
    sample_scenario: SimulationScenarioInput,
):
    """Gera o gráfico Waterfall e valida valores e categorias do DRE operacional."""
    simulator = BusinessScenarioSimulator()
    result = simulator.simulate_scenario(sample_scenario)

    fig = plot_waterfall_cost_breakdown(sample_scenario, result)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    waterfall_trace = fig.data[0]
    assert waterfall_trace.type == "waterfall"
    assert len(waterfall_trace.x) == 6
    assert waterfall_trace.x[0] == "Receita Líquida"
    assert waterfall_trace.x[-1] == "Margem Líquida"
