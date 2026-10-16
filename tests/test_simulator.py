"""Testes unitários rigorosos para o motor de simulação de negócios e cenários."""

import pytest
from pydantic import ValidationError

from src.core.schemas import (
    AcquisitionChannel,
    Category,
    RiskAlertLevel,
    SimulationScenarioInput,
)
from src.core.simulator import BusinessScenarioSimulator


@pytest.fixture
def simulator() -> BusinessScenarioSimulator:
    return BusinessScenarioSimulator()


@pytest.fixture
def baseline_scenario() -> SimulationScenarioInput:
    return SimulationScenarioInput(
        unit_price=1200.0,
        unit_cost=600.0,
        quantity=10,
        discount_pct=0.0,
        shipping_cost=25.0,
        tax_rate=0.10,
        delivery_days=3,
        category=Category.ELECTRONICS,
        channel=AcquisitionChannel.DIRECT,
        reverse_logistics_cost=45.0,
    )


def test_baseline_scenario_no_discount(
    simulator: BusinessScenarioSimulator,
    baseline_scenario: SimulationScenarioInput,
):
    """Cenário baseline sem desconto deve manter receita íntegra e margem saudável."""
    result = simulator.simulate_scenario(baseline_scenario)

    assert result.gross_revenue == 12000.0
    assert result.net_revenue == 12000.0
    assert result.net_revenue == result.gross_revenue
    assert result.contribution_margin_value > 0
    assert result.contribution_margin_pct >= 25.0
    assert result.risk_alert == RiskAlertLevel.SAFE_GREEN.value
    assert 0.05 <= result.estimated_return_rate <= 0.12
    assert 0.03 <= result.estimated_cancellation_rate <= 0.10


def test_margin_destruction_extreme_discount(
    simulator: BusinessScenarioSimulator,
    baseline_scenario: SimulationScenarioInput,
):
    """Desconto agressivo (70%) deve destruir margem e acionar alerta DANGER_RED."""
    aggressive_scenario = baseline_scenario.model_copy(update={"discount_pct": 0.70})
    result = simulator.simulate_scenario(aggressive_scenario)

    assert result.gross_revenue == 12000.0
    assert result.net_revenue == 3600.0
    assert result.contribution_margin_value < 0.0
    assert result.contribution_margin_pct < 0.0
    assert result.risk_alert == RiskAlertLevel.DANGER_RED.value
    # Descontos profundos elevam risco operacional
    assert result.estimated_return_rate > baseline_scenario.discount_pct


def test_break_even_discount_calculation(
    simulator: BusinessScenarioSimulator,
    baseline_scenario: SimulationScenarioInput,
):
    """O ponto de equilíbrio (break-even) deve delimitar exatamente a fronteira de rentabilidade."""
    be_discount = simulator.find_break_even_discount(baseline_scenario)

    assert 0.10 < be_discount < 0.60

    # Margem ligeiramente abaixo do break-even deve ser positiva
    safe_scenario = baseline_scenario.model_copy(update={"discount_pct": be_discount - 0.02})
    safe_res = simulator.simulate_scenario(safe_scenario)
    assert safe_res.contribution_margin_value > 0

    # Margem ligeiramente acima do break-even deve ser negativa
    deficit_scenario = baseline_scenario.model_copy(update={"discount_pct": be_discount + 0.02})
    deficit_res = simulator.simulate_scenario(deficit_scenario)
    assert deficit_res.contribution_margin_value < 0


def test_pydantic_schema_validation_errors():
    """Valida que o schema Pydantic bloqueia inputs que violam limites físicos ou regras."""
    # Preço base negativo
    with pytest.raises(ValidationError):
        SimulationScenarioInput(
            unit_price=-100.0,
            unit_cost=50.0,
            quantity=5,
            discount_pct=0.10,
        )

    # CMV negativo
    with pytest.raises(ValidationError):
        SimulationScenarioInput(
            unit_price=100.0,
            unit_cost=-50.0,
            quantity=5,
            discount_pct=0.10,
        )

    # Desconto acima de 90%
    with pytest.raises(ValidationError):
        SimulationScenarioInput(
            unit_price=100.0,
            unit_cost=50.0,
            quantity=5,
            discount_pct=1.20,
        )

    # Desconto negativo
    with pytest.raises(ValidationError):
        SimulationScenarioInput(
            unit_price=100.0,
            unit_cost=50.0,
            quantity=5,
            discount_pct=-0.15,
        )

    # Quantidade zero ou negativa
    with pytest.raises(ValidationError):
        SimulationScenarioInput(
            unit_price=100.0,
            unit_cost=50.0,
            quantity=0,
            discount_pct=0.10,
        )


def test_discount_sensitivity_curve_structure(
    simulator: BusinessScenarioSimulator,
    baseline_scenario: SimulationScenarioInput,
):
    """A curva de sensibilidade deve conter N passos com monotonocidade de receita líquida decrescente."""
    steps = 15
    curve = simulator.calculate_discount_sensitivity_curve(baseline_scenario, steps=steps)

    assert len(curve) == steps
    assert curve[0]["discount_pct"] == 0.0
    assert curve[-1]["discount_pct"] == 0.90

    # À medida que o desconto sobe, o preço líquido unitário deve decrescer monotonamente
    net_prices = [p["unit_net_price"] for p in curve]
    assert all(x >= y for x, y in zip(net_prices, net_prices[1:], strict=False))

    # A curva deve conter transição de lucratividade
    profitable_flags = [p["is_profitable"] for p in curve]
    assert True in profitable_flags
    assert False in profitable_flags


def test_delivery_delay_risk_escalation(
    simulator: BusinessScenarioSimulator,
    baseline_scenario: SimulationScenarioInput,
):
    """Prazos longos de entrega (>5 dias) devem elevar probabilidade de devolução (H5)."""
    fast_delivery = baseline_scenario.model_copy(update={"delivery_days": 2})
    slow_delivery = baseline_scenario.model_copy(update={"delivery_days": 14})

    fast_res = simulator.simulate_scenario(fast_delivery)
    slow_res = simulator.simulate_scenario(slow_delivery)

    assert slow_res.estimated_return_rate > fast_res.estimated_return_rate
    assert slow_res.estimated_cancellation_rate > fast_res.estimated_cancellation_rate
    assert slow_res.contribution_margin_value < fast_res.contribution_margin_value
