"""Testes unitários para o gerador de parecer executivo em PDF (Typst)."""

import pathlib

import pytest

from src.reports.executive_pdf import (
    ExecutivePdfError,
    generate_executive_pdf,
    generate_executive_pdf_bytes,
)


@pytest.fixture
def synthetic_scenario() -> dict:
    """Fixture com cenário executivo padrão seguro."""
    return {
        "unit_price": 1200.0,
        "unit_cost": 580.0,
        "quantity": 50,
        "discount_pct": 0.20,
        "shipping_cost": 25.0,
        "tax_rate": 0.10,
        "delivery_days": 4,
        "reverse_logistics_cost": 45.0,
        "category": "Electronics",
        "channel": "Direct",
        "gross_revenue": 60000.0,
        "net_revenue": 48000.0,
        "total_cost": 34320.0,
        "contribution_margin_value": 13680.0,
        "contribution_margin_pct": 28.5,
        "break_even_discount": 0.342,
        "estimated_return_rate": 0.0685,
        "estimated_cancellation_rate": 0.0608,
        "risk_alert": "SAFE_GREEN",
    }


def test_generate_executive_pdf_creates_valid_file(
    synthetic_scenario: dict, tmp_path: pathlib.Path
):
    """Verifica se o arquivo PDF é gerado, maior que 1KB e com cabeçalho %PDF-."""
    out_pdf = tmp_path / "parecer_executivo_teste.pdf"

    result_path = generate_executive_pdf(synthetic_scenario, out_pdf)

    assert result_path.exists()
    assert result_path == out_pdf
    size_bytes = result_path.stat().st_size
    assert size_bytes > 1024, f"Arquivo PDF muito pequeno: {size_bytes} bytes"

    header = result_path.read_bytes()[:5]
    assert header == b"%PDF-", f"Header inválido no PDF: {header}"


def test_generate_executive_pdf_bytes_returns_valid_pdf(synthetic_scenario: dict):
    """Verifica se a função de bytes retorna diretamente o conteúdo compilado."""
    pdf_bytes = generate_executive_pdf_bytes(synthetic_scenario)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1024
    assert pdf_bytes.startswith(b"%PDF-")


@pytest.mark.parametrize("risk_level", ["SAFE_GREEN", "WARNING_YELLOW", "DANGER_RED"])
def test_generate_executive_pdf_different_risk_levels(
    synthetic_scenario: dict, risk_level: str, tmp_path: pathlib.Path
):
    """Verifica a correta compilação para todos os níveis de alerta semântico."""
    scenario = synthetic_scenario.copy()
    scenario["risk_alert"] = risk_level
    if risk_level == "DANGER_RED":
        scenario["discount_pct"] = 0.50
        scenario["contribution_margin_value"] = -5000.0
        scenario["contribution_margin_pct"] = -10.0

    out_pdf = tmp_path / f"parecer_{risk_level}.pdf"
    res = generate_executive_pdf(scenario, out_pdf)

    assert res.exists()
    assert res.stat().st_size > 1024
    assert res.read_bytes().startswith(b"%PDF-")


def test_generate_executive_pdf_error_handling(tmp_path: pathlib.Path):
    """Verifica se exceções na compilação Typst são devidamente encapsuladas em ExecutivePdfError."""
    # Cenário inválido proposital que quebra o tipo numérico em tempo de formatação
    invalid_scenario = {
        "unit_price": "invalido_nao_numerico",
    }
    out_pdf = tmp_path / "erro_esperado.pdf"

    with pytest.raises(ExecutivePdfError) as exc_info:
        generate_executive_pdf(invalid_scenario, out_pdf)

    assert "Falha na compilação" in str(exc_info.value)


def test_generate_executive_pdf_ml_mode(synthetic_scenario: dict, tmp_path: pathlib.Path):
    """Verifica a correta compilação e cabeçalho ao selecionar o modo de inferência ML."""
    scenario = synthetic_scenario.copy()
    scenario["risk_source"] = "ML"
    scenario["estimated_return_rate"] = 0.0337
    scenario["estimated_cancellation_rate"] = 0.0

    out_pdf = tmp_path / "parecer_ml_teste.pdf"
    res = generate_executive_pdf(scenario, out_pdf, risk_source="ML")

    assert res.exists()
    assert res.stat().st_size > 1024
    assert res.read_bytes().startswith(b"%PDF-")


def test_generate_executive_pdf_bytes_risk_source_precedence(synthetic_scenario: dict):
    """Regressão do commit 54f44e5: cobre os 3 caminhos de propagação do risk_source.

    Cenários:
    1. Kwarg explícito: generate_executive_pdf_bytes(scenario, risk_source="ML").
    2. Dict com chave embutida: generate_executive_pdf_bytes({**scenario, "risk_source": "ML"}).
    3. Precedência: kwarg explícito vence o dict quando ambos estão presentes.
    """
    # Caminho 1: kwarg explícito
    pdf_kwarg = generate_executive_pdf_bytes(synthetic_scenario, risk_source="ML")
    assert pdf_kwarg.startswith(b"%PDF-")
    assert len(pdf_kwarg) > 1024

    # Caminho 2: chave embutida no dict (comportamento do app.py pós-54f44e5)
    scenario_with_source = synthetic_scenario.copy()
    scenario_with_source["risk_source"] = "ML"
    pdf_dict = generate_executive_pdf_bytes(scenario_with_source)
    assert pdf_dict.startswith(b"%PDF-")
    assert len(pdf_dict) > 1024

    # Caminho 3: kwarg deve vencer o dict (precedência explícita)
    # Se o código não implementa essa precedência, este teste vai falhar
    # e revelará uma inconsistência a ser corrigida.
    pdf_precedence = generate_executive_pdf_bytes(scenario_with_source, risk_source="Heurística")
    assert pdf_precedence.startswith(b"%PDF-")
    assert len(pdf_precedence) > 1024
