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
