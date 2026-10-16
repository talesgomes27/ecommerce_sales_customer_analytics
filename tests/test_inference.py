"""Testes unitários e contratuais para o motor de inferência ML e calibração de Elkan."""

import pytest
from pydantic import ValidationError

from src.core.schemas import AcquisitionChannel, Category
from src.core.simulator import BusinessScenarioSimulator
from src.features.builder import PROHIBITED_LEAKAGE_COLS
from src.models.inference import RiskModelInference
from src.models.schemas import RiskScenarioInput


@pytest.fixture
def inference_engine() -> RiskModelInference:
    """Fixture que inicializa o motor de inferência apontando para models/."""
    return RiskModelInference()


@pytest.fixture
def baseline_scenario() -> RiskScenarioInput:
    """Cenário comercial padrão validado."""
    return RiskScenarioInput(
        customer_age=35,
        quantity=2,
        gross_sales=250.0,
        tax_amount=25.0,
        shipping_cost=15.0,
        product_cost=120.0,
        orders_count_prior=3,
        spend_prior=450.0,
        days_since_last_order=25,
        gender="Female",
        customer_segment="Consumer",
        region="North",
        sales_channel="Website",
        marketing_channel="Google Ads",
        payment_method="Credit Card",
        shipping_method="Standard",
        warehouse="WH-001",
    )


def test_inference_initialization(inference_engine: RiskModelInference) -> None:
    """1. Carregamento: Garante que o pipeline treinado e metadados inicializam sem erros."""
    assert inference_engine.pipeline is not None
    assert inference_engine.metadata is not None
    assert len(inference_engine.numeric_cols) == 9
    assert len(inference_engine.categorical_cols) == 8


def test_inference_metadata_sanity(inference_engine: RiskModelInference) -> None:
    """2. Sanity check: Confirma existência e validade dos campos de governança no metadata.json."""
    assert "tau_optimal_calibrated" in inference_engine.metadata
    assert "base_rate_real" in inference_engine.metadata
    assert 0.0 < inference_engine.pi < 1.0
    assert 0.0 < inference_engine.tau_calibrated < 1.0
    assert pytest.approx(inference_engine.tau_calibrated, abs=1e-3) == 0.1549


def test_inference_predict_risk_structure(
    inference_engine: RiskModelInference, baseline_scenario: RiskScenarioInput
) -> None:
    """3. Predição básica: Garante que o retorno contém exatamente o schema acordado."""
    result = inference_engine.predict_risk(baseline_scenario)

    assert isinstance(result, dict)
    expected_keys = {
        "prob_devolucao_calibrada",
        "prob_devolucao_balanceada",
        "decisao",
        "tau_aplicado",
        "tau_balanceado",
        "modo",
    }
    assert expected_keys.issubset(result.keys())
    assert result["modo"] == "ML_LightGBM_Calibrado"
    assert result["decisao"] in {"LIBERAR", "BLOQUEAR"}


def test_inference_elkan_calibration_math(inference_engine: RiskModelInference) -> None:
    """4. Calibração Elkan: Valida matematicamente a conversão de odds balanceadas em reais."""
    # Score balanceado ótimo tau* = 0.55 deve calibrar para ~0.1549
    calibrated_tau = inference_engine._calibrate_elkan(0.55)
    assert pytest.approx(calibrated_tau, abs=1e-3) == 0.1549

    # Limites assintóticos
    assert inference_engine._calibrate_elkan(0.0) == 0.0
    assert inference_engine._calibrate_elkan(1.0) == 1.0


def test_inference_anti_leakage_and_extra_fields(baseline_scenario: RiskScenarioInput) -> None:
    """5. Anti-leakage: Pydantic deve rejeitar campos extras e colunas proibidas pós-compra."""
    data = baseline_scenario.model_dump()

    # Tentativa de injetar campo proibido do leakage list
    for forbidden_col in PROHIBITED_LEAKAGE_COLS[:3]:
        bad_data = {**data, forbidden_col: 5}
        with pytest.raises((ValidationError, ValueError)):
            RiskScenarioInput(**bad_data)

    # Tentativa de injetar campo totalmente arbitrário
    with pytest.raises(ValidationError):
        RiskScenarioInput(**{**data, "arbitrary_extra_column": 123})


def test_inference_probability_ranges(
    inference_engine: RiskModelInference, baseline_scenario: RiskScenarioInput
) -> None:
    """6. Range: As probabilidades balanceada e calibrada devem estar estritamente no intervalo [0, 1]."""
    result = inference_engine.predict_risk(baseline_scenario)
    assert 0.0 <= result["prob_devolucao_balanceada"] <= 1.0
    assert 0.0 <= result["prob_devolucao_calibrada"] <= 1.0


def test_inference_binary_decisions_extreme_scenarios(
    inference_engine: RiskModelInference,
) -> None:
    """7. Decisão binária: Cenário de alto risco deve BLOQUEAR e cenário benigno deve LIBERAR."""
    # Cenário extremo de alto risco
    high_risk_scenario = RiskScenarioInput(
        customer_age=60,
        quantity=10,
        gross_sales=2889.3,
        tax_amount=577.86,
        shipping_cost=21.77,
        product_cost=1225.17,
        orders_count_prior=6,
        spend_prior=6988.8,
        days_since_last_order=130,
        gender="Male",
        customer_segment="Premium",
        region="West",
        sales_channel="Website",
        marketing_channel="Direct",
        payment_method="Credit Card",
        shipping_method="Express",
        warehouse="WH-011",
    )
    high_result = inference_engine.predict_risk(high_risk_scenario)
    assert high_result["decisao"] == "BLOQUEAR"
    assert high_result["prob_devolucao_calibrada"] >= inference_engine.tau_calibrated

    # Cenário benigno de baixo risco
    low_risk_scenario = RiskScenarioInput(
        customer_age=69,
        quantity=11,
        gross_sales=2284.4,
        tax_amount=50.55,
        shipping_cost=38.02,
        product_cost=1067.43,
        orders_count_prior=5,
        spend_prior=1778.0,
        days_since_last_order=265,
        gender="Female",
        customer_segment="Premium",
        region="South",
        sales_channel="Mobile App",
        marketing_channel="Facebook Ads",
        payment_method="Debit Card",
        shipping_method="Economy",
        warehouse="WH-011",
    )
    low_result = inference_engine.predict_risk(low_risk_scenario)
    assert low_result["decisao"] == "LIBERAR"
    assert low_result["prob_devolucao_calibrada"] < inference_engine.tau_calibrated


def test_inference_consistency_with_heuristic(
    inference_engine: RiskModelInference,
) -> None:
    """8. Consistência com heurística: Confirma que |ML_calibrado - Heurística| < 0.10 em 3 cenários."""
    simulator = BusinessScenarioSimulator()

    scenarios = [
        (
            RiskScenarioInput(
                customer_age=35,
                quantity=2,
                gross_sales=250.0,
                tax_amount=25.0,
                shipping_cost=15.0,
                product_cost=120.0,
                orders_count_prior=3,
                spend_prior=450.0,
                days_since_last_order=25,
                gender="Female",
                customer_segment="Consumer",
                region="North",
                sales_channel="Website",
                marketing_channel="Google Ads",
                payment_method="Credit Card",
                shipping_method="Standard",
                warehouse="WH-001",
            ),
            (7, 0.20, Category.ELECTRONICS, AcquisitionChannel.PAID_SEARCH),
        ),
        (
            RiskScenarioInput(
                customer_age=45,
                quantity=1,
                gross_sales=100.0,
                tax_amount=10.0,
                shipping_cost=8.0,
                product_cost=50.0,
                orders_count_prior=5,
                spend_prior=800.0,
                days_since_last_order=15,
                gender="Male",
                customer_segment="VIP",
                region="Central",
                sales_channel="Website",
                marketing_channel="Direct",
                payment_method="Credit Card",
                shipping_method="Standard",
                warehouse="WH-002",
            ),
            (4, 0.05, Category.BOOKS_MEDIA, AcquisitionChannel.DIRECT),
        ),
        (
            RiskScenarioInput(
                customer_age=28,
                quantity=3,
                gross_sales=350.0,
                tax_amount=35.0,
                shipping_cost=20.0,
                product_cost=180.0,
                orders_count_prior=2,
                spend_prior=300.0,
                days_since_last_order=40,
                gender="Non-Binary",
                customer_segment="Consumer",
                region="East",
                sales_channel="Marketplace",
                marketing_channel="Facebook Ads",
                payment_method="Debit Card",
                shipping_method="Express",
                warehouse="WH-003",
            ),
            (6, 0.15, Category.FASHION, AcquisitionChannel.SOCIAL_MEDIA),
        ),
    ]

    for scenario_input, (days, discount, cat, channel) in scenarios:
        ml_pred = inference_engine.predict_risk(scenario_input)["prob_devolucao_calibrada"]
        p_ret, p_canc = simulator.estimate_operational_risk_rates(days, discount, cat, channel)
        heur_total = p_ret + p_canc
        assert abs(ml_pred - heur_total) < 0.10, (
            f"Divergência excessiva: ML={ml_pred}, Heur={heur_total}"
        )
